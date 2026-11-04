"""The changed-file list in the link-check and quote-check workflow steps (#293).

Both steps list the markdown files a PR changed with `git diff` and pass them to a script. Each
`run:` block is executed under bash with a stand-in `python`, as in test_check_links.py: a list
that cannot be read must fail the step, never pass it with no files checked, and a path with
non-ASCII characters must reach the script as it is, not in git's quoted form.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).parent.parent / ".github" / "workflows"
STEPS = [
    ("link-check.yml", "Check links in changed docs", "scripts/check_links.py"),
    ("quote-check.yml", "Check quotes in changed docs", "scripts/check_quotes.py"),
]


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


def _run_block(workflow: str, step: str) -> str:
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    match = re.search(
        rf"- name: {re.escape(step)}\n(?: {{8}}.*\n)*? {{8}}run: \|\n((?:(?: {{10}}.*)?\n)+)",
        text,
    )
    assert match, f"{step} missing from {workflow}"
    return textwrap.dedent(match.group(1))


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repo: Path, files: list[str]) -> str:
    for rel in files:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "c")
    return _git(repo, "rev-parse", "HEAD")


def _run_step(tmp_path: Path, workflow: str, step: str, base: str, repo: Path):
    """Run the step against `repo`; returns the process and the stand-in's arguments, or None
    when the stand-in was never called."""
    args_file = tmp_path / "args.txt"
    stub = f'python() {{ printf "%s\\n" "$@" > "{args_file.as_posix()}"; return 0; }}\n'
    script = tmp_path / "step.sh"
    # GitHub runs a `run:` block as `bash -e {0}`.
    script.write_text(
        "set -e\n" + stub + _run_block(workflow, step), encoding="utf-8", newline="\n"
    )
    env = dict(
        os.environ, BASE_SHA=base, GITHUB_STEP_SUMMARY=str(tmp_path / "summary.md")
    )
    proc = subprocess.run(
        [BASH, script.as_posix()], cwd=repo, env=env, capture_output=True, text=True
    )
    args = (
        args_file.read_text(encoding="utf-8").splitlines()
        if args_file.exists()
        else None
    )
    return proc, args


@pytest.fixture
def repo(tmp_path):
    if BASH is None:
        if os.environ.get("CI"):
            pytest.fail("bash is required in CI to test the workflow steps")
        pytest.skip("bash not installed")
    path = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


@pytest.mark.parametrize("workflow,step,script", STEPS)
def test_the_step_fails_when_the_changed_file_list_cannot_be_read(
    tmp_path, repo, workflow, step, script
):
    _commit(repo, ["docs/a.md"])
    # A base the clone lacks: git diff fails.
    proc, args = _run_step(tmp_path, workflow, step, "0" * 40, repo)
    assert proc.returncode != 0
    assert args is None


@pytest.mark.parametrize("workflow,step,script", STEPS)
def test_the_step_passes_a_non_ascii_path_as_it_is(
    tmp_path, repo, workflow, step, script
):
    base = _commit(repo, ["docs/a.md"])
    _commit(repo, ["docs/naïve café.md"])
    proc, args = _run_step(tmp_path, workflow, step, base, repo)
    assert proc.returncode == 0, proc.stderr
    assert args == [script, "docs/naïve café.md"]
