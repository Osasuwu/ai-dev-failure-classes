"""Tests for the link check (#264, ADR-0004 decision 19). No network: every test passes its own fetch.

The script's state rules, its file selection against the shared path definition, and the
workflow that runs it: the trigger, the name, and the run block, executed under bash with a
stand-in `python` as in test_quote_cron.py.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from check_links import (  # noqa: E402
    ALIVE,
    DEAD,
    NOT_VERIFIED,
    HostNotFound,
    is_checked,
    judge,
    main,
)
from structure_gate import is_hold_path  # noqa: E402

ROOT = Path(__file__).parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
WORKFLOW = (WORKFLOWS / "link-check.yml").read_text(encoding="utf-8")
SHIPPED = json.loads((ROOT / ".github" / "hold-paths.json").read_text(encoding="utf-8"))


def _fetcher(outcomes: dict[str, object]):
    """A fetch that returns the status given for a URL, or raises the exception given."""

    def fetch(url: str) -> int:
        outcome = outcomes[url]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    return fetch


def _repo(tmp_path: Path, definition: dict = SHIPPED) -> Path:
    (tmp_path / ".github").mkdir(parents=True)
    (tmp_path / ".github" / "hold-paths.json").write_text(
        json.dumps(definition), encoding="utf-8"
    )
    return tmp_path


def _write(root: Path, rel: str, body: str) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return rel


def _run(
    tmp_path, monkeypatch, capsys, files: dict[str, str], outcomes: dict[str, object]
):
    root = _repo(tmp_path)
    for rel, body in files.items():
        _write(root, rel, body)
    monkeypatch.chdir(root)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    code = main(list(files), fetch=_fetcher(outcomes))
    return code, capsys.readouterr().out


# --- the state of one link ---------------------------------------------------


@pytest.mark.parametrize(
    "outcome,state,reason",
    [
        (200, ALIVE, "HTTP 200"),
        (204, ALIVE, "HTTP 204"),
        (404, DEAD, "HTTP 404"),
        (410, DEAD, "HTTP 410"),
        (HostNotFound("example.invalid"), DEAD, "host does not resolve"),
        (401, NOT_VERIFIED, "HTTP 401"),
        (403, NOT_VERIFIED, "HTTP 403"),
        (429, NOT_VERIFIED, "HTTP 429"),
        (500, NOT_VERIFIED, "HTTP 500"),
        (503, NOT_VERIFIED, "HTTP 503"),
        (400, NOT_VERIFIED, "HTTP 400"),
        (301, NOT_VERIFIED, "HTTP 301"),
        (TimeoutError("timed out"), NOT_VERIFIED, "TimeoutError"),
        (OSError("connection reset"), NOT_VERIFIED, "OSError"),
    ],
)
def test_a_web_link_gets_its_state_from_the_response(tmp_path, outcome, state, reason):
    url = "https://example.org/page"
    assert judge(url, tmp_path / "doc.md", fetch=_fetcher({url: outcome})) == (
        state,
        reason,
    )


def test_the_fragment_is_not_sent_with_the_request(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        return 200

    assert (
        judge("https://example.org/page#part", tmp_path / "doc.md", fetch=fetch)[0]
        == ALIVE
    )
    assert seen == ["https://example.org/page"]


def test_a_relative_link_to_an_existing_file_is_alive(tmp_path):
    _write(tmp_path, "docs/other.md", "x")
    _write(tmp_path, "docs/sub/dir/keep.txt", "x")
    doc = tmp_path / "docs" / "classes" / "a.md"
    assert judge("../other.md#section", doc, fetch=None) == (ALIVE, "file exists")
    assert judge("../sub/dir", doc, fetch=None) == (ALIVE, "file exists")
    # ".." is resolved on the text, as GitHub does: the missing directory before it does not matter.
    assert judge("../nowhere/../other.md", doc, fetch=None) == (ALIVE, "file exists")


def test_a_relative_link_to_a_missing_file_is_dead(tmp_path):
    doc = tmp_path / "docs" / "a.md"
    assert judge("missing.md", doc, fetch=None) == (DEAD, "no such file")


def test_a_link_starting_with_a_slash_is_relative_to_the_repository_root(
    tmp_path, monkeypatch
):
    _write(tmp_path, "AGENTS.md", "x")
    monkeypatch.chdir(tmp_path)
    doc = tmp_path / "docs" / "classes" / "a.md"
    assert judge("/AGENTS.md", doc, fetch=None) == (ALIVE, "file exists")
    assert judge("/docs/AGENTS.md", doc, fetch=None) == (DEAD, "no such file")


def test_a_percent_encoded_relative_link_is_decoded(tmp_path):
    _write(tmp_path, "docs/with space.md", "x")
    assert judge("with%20space.md", tmp_path / "docs" / "a.md", fetch=None)[0] == ALIVE


@pytest.mark.parametrize("url", ["mailto:someone@example.org", "ftp://example.org/x"])
def test_a_link_of_another_scheme_is_not_verified(tmp_path, url):
    assert judge(url, tmp_path / "doc.md", fetch=None) == (
        NOT_VERIFIED,
        "not an http(s) or file link",
    )


# --- the run -----------------------------------------------------------------


def test_a_dead_link_fails_the_run_and_every_link_is_reported(
    tmp_path, monkeypatch, capsys
):
    body = (
        "One [alive](https://a.example/x) and one [dead](https://d.example/x).\n\n"
        "Then [blocked](https://b.example/x) and [local](missing.md).\n"
    )
    outcomes = {
        "https://a.example/x": 200,
        "https://d.example/x": 404,
        "https://b.example/x": 403,
    }
    code, out = _run(tmp_path, monkeypatch, capsys, {"docs/a.md": body}, outcomes)
    assert code == 1
    assert "docs/a.md:1: alive: https://a.example/x (HTTP 200)" in out
    assert "docs/a.md:1: dead: https://d.example/x (HTTP 404)" in out
    assert "docs/a.md:3: not verified: https://b.example/x (HTTP 403)" in out
    assert "docs/a.md:3: dead: missing.md (no such file)" in out
    assert out.splitlines()[-1] == (
        "1 file(s), 4 link(s): 1 alive, 2 dead, 1 not verified "
        "(not verified is not a failure; open those by hand)"
    )


def test_a_link_that_is_only_not_verified_does_not_fail_the_run(
    tmp_path, monkeypatch, capsys
):
    body = "See [a](https://a.example/x), [b](https://b.example/x) and [c](https://c.example/x).\n"
    outcomes = {
        "https://a.example/x": 200,
        "https://b.example/x": 429,
        "https://c.example/x": TimeoutError("timed out"),
    }
    code, out = _run(tmp_path, monkeypatch, capsys, {"docs/a.md": body}, outcomes)
    assert code == 0
    assert out.splitlines()[-1].startswith(
        "1 file(s), 3 link(s): 1 alive, 0 dead, 2 not verified"
    )


def test_a_link_repeated_in_a_doc_is_fetched_and_reported_once(
    tmp_path, monkeypatch, capsys
):
    calls = []

    def fetch(url):
        calls.append(url)
        return 200

    root = _repo(tmp_path)
    _write(
        root, "docs/a.md", "[x](https://a.example/x)\n\n[again](https://a.example/x)\n"
    )
    _write(root, "docs/b.md", "[x](https://a.example/x)\n")
    monkeypatch.chdir(root)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert main(["docs/a.md", "docs/b.md"], fetch=fetch) == 0
    out = capsys.readouterr().out
    assert calls == ["https://a.example/x"]
    assert out.count("alive: https://a.example/x") == 2  # once per doc that has it
    assert "docs/a.md:1: alive: https://a.example/x" in out  # at its first appearance
    assert "docs/b.md:1: alive: https://a.example/x" in out


def test_links_in_code_and_anchors_are_not_links(tmp_path, monkeypatch, capsys):
    body = "```\n[x](https://code.example/x)\n```\n\nSee [below](#below).\n"
    code, out = _run(tmp_path, monkeypatch, capsys, {"docs/a.md": body}, {})
    assert code == 0
    assert out.splitlines()[-1].startswith("1 file(s), 0 link(s)")


def test_files_outside_the_path_definition_are_not_checked(
    tmp_path, monkeypatch, capsys
):
    files = {
        "docs/adr/0004-x.md": "[x](https://adr.example/x)\n",
        "scripts/README.md": "[x](https://scripts.example/x)\n",
        "docs/a.md": "[x](https://a.example/x)\n",
    }
    code, out = _run(tmp_path, monkeypatch, capsys, files, {"https://a.example/x": 200})
    assert code == 0
    assert "adr.example" not in out and "scripts.example" not in out
    assert out.splitlines()[-1].startswith("1 file(s), 1 link(s)")


def test_no_changed_doc_reports_nothing_and_passes(tmp_path, monkeypatch, capsys):
    code, out = _run(
        tmp_path,
        monkeypatch,
        capsys,
        {"scripts/README.md": "[x](https://s.example/x)\n"},
        {},
    )
    assert code == 0
    assert (
        out.strip()
        == "No changed markdown file under the shared path definition; nothing to check."
    )


def test_a_missing_path_definition_fails_the_run(tmp_path, monkeypatch, capsys):
    _write(tmp_path, "docs/a.md", "[x](https://a.example/x)\n")
    monkeypatch.chdir(tmp_path)
    assert main(["docs/a.md"], fetch=_fetcher({"https://a.example/x": 200})) == 2
    assert ".github/hold-paths.json" in capsys.readouterr().out


def test_the_report_header_and_summary_go_to_the_job_summary(
    tmp_path, monkeypatch, capsys
):
    summary = tmp_path / "summary.md"
    root = _repo(tmp_path / "repo")
    _write(root, "docs/a.md", "[x](https://d.example/x)\n")
    monkeypatch.chdir(root)
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert main(["docs/a.md"], fetch=_fetcher({"https://d.example/x": 404})) == 1
    text = summary.read_text(encoding="utf-8")
    assert text.startswith(
        "**Link check:** whether each link in the changed docs resolves. "
        "It does not check what a page says.\n"
    )
    assert "- `docs/a.md:1` dead: https://d.example/x (HTTP 404)\n" in text
    assert "1 file(s), 1 link(s): 0 alive, 1 dead, 0 not verified" in text


# --- file selection agrees with the shared path definition --------------------

CORPUS = [
    "README.md",
    "AGENTS.md",
    "scripts/README.md",
    "docs/guide.md",
    "docs/classes/alpha.md",
    "docs/adr/0004-x.md",
    "docs/research/r.md",
    "docs/adr-notes/z.md",
    "incidents/incidents.csv",
    "incidents/sub/n.md",
    "notes/a.md",
    "private/keep.md",
    "private/open/a.md",
    "Makefile",
]
CHANGED_DEFINITION = {
    "prefixes": ["notes/", "private/"],
    "excluded_prefixes": ["private/open/"],
    "files": ["Makefile", "docs/adr/0004-x.md"],
}


def test_selection_is_the_hold_definition_narrowed_to_markdown_under_the_shipped_definition():
    checked = {p for p in CORPUS if is_checked(p, SHIPPED)}
    assert checked == {
        p for p in CORPUS if is_hold_path(p, SHIPPED) and p.endswith(".md")
    }
    assert checked == {
        "README.md",
        "docs/guide.md",
        "docs/classes/alpha.md",
        "docs/adr-notes/z.md",
        "incidents/sub/n.md",
    }


def test_selection_follows_a_changed_definition():
    checked = {p for p in CORPUS if is_checked(p, CHANGED_DEFINITION)}
    assert checked == {
        p for p in CORPUS if is_hold_path(p, CHANGED_DEFINITION) and p.endswith(".md")
    }
    assert checked == {"notes/a.md", "private/keep.md", "docs/adr/0004-x.md"}


# --- the workflow -------------------------------------------------------------


def test_the_workflow_runs_on_pull_requests_only():
    on = re.search(r"^on:\n((?:[ \t]+\S.*\n)+)", WORKFLOW, re.M)
    assert on, "on: block missing"
    assert [line.strip() for line in on.group(1).splitlines()] == ["pull_request:"]


def test_no_workflow_runs_the_link_check_on_a_schedule():
    runners = [
        p
        for p in sorted(WORKFLOWS.glob("*.y*ml"))
        if "check_links.py" in p.read_text(encoding="utf-8")
    ]
    assert [p.name for p in runners] == ["link-check.yml"]
    for path in runners:
        assert not re.search(
            r"^\s*schedule:", path.read_text(encoding="utf-8"), re.M
        ), path.name


def test_the_check_is_named_for_links_and_claims_nothing_about_content():
    assert re.search(r"^name: (.+)$", WORKFLOW, re.M).group(1) == "Link check"
    assert re.search(r"^jobs:\n  (\S+):$", WORKFLOW, re.M).group(1) == "link-check"


def _run_block() -> str:
    match = re.search(
        r"- name: Check links in changed docs\n(?: {8}.*\n)*? {8}run: \|\n((?:(?: {10}.*)?\n)+)",
        WORKFLOW,
    )
    assert match, "check step missing"
    return textwrap.dedent(match.group(1))


def _find_bash() -> str | None:
    """bash on PATH; on Windows, Git's bash (PATH often has WSL's first, which sees other paths)."""
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    if git:
        # Git for Windows puts git.exe in cmd/, bin/ or mingw64/bin/; bash.exe is in <Git>/bin/.
        here = Path(git).parent
        for candidate in (
            here.parent / "bin" / "bash.exe",
            here / "bash.exe",
            here.parent.parent / "bin" / "bash.exe",
        ):
            if candidate.exists():
                return str(candidate)
    return None


BASH = _find_bash()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.mark.parametrize("rc", [0, 1])
def test_the_step_passes_the_changed_markdown_files_and_the_scripts_exit_code(
    tmp_path, rc
):
    if BASH is None:
        if os.environ.get("CI"):
            pytest.fail("bash is required in CI to test the check step")
        pytest.skip("bash not installed")
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    for rel in ("docs/kept.md", "docs/gone.md", "docs/same.md"):
        _write(repo, rel, "x\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    for rel in ("docs/kept.md", "docs/with space.md", "scripts/x.py", "notes/n.md"):
        _write(repo, rel, "changed\n")
    (repo / "docs" / "gone.md").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")
    args_file = tmp_path / "args.txt"
    # A stand-in for the real script: record the arguments, exit with the given code.
    stub = (
        f'python() {{ printf "%s\\n" "$@" > "{args_file.as_posix()}"; return {rc}; }}\n'
    )
    step = tmp_path / "step.sh"
    # GitHub runs a `run:` block as `bash -e {0}`.
    step.write_text("set -e\n" + stub + _run_block(), encoding="utf-8", newline="\n")
    env = dict(os.environ, BASE_SHA=base)
    proc = subprocess.run(
        [BASH, step.as_posix()], cwd=repo, env=env, capture_output=True, text=True
    )
    assert proc.returncode == rc, proc.stderr
    args = args_file.read_text(encoding="utf-8").splitlines()
    # Selection by the path definition is the script's job; the step passes every changed .md
    # and leaves out deleted files.
    assert args[0] == "scripts/check_links.py"
    assert sorted(args[1:]) == ["docs/kept.md", "docs/with space.md", "notes/n.md"]
