"""Behaviour checks for scripts/doc_review.py and .github/workflows/doc-review.yml (#244).

The doc reviewer is advisory (ADR-0004 decision 5): one automatic run per PR that changes a
document, one more on request when the reviewed text changed, a status on the head SHA that
fails only when the run itself failed. Every decision is a function in scripts/doc_review.py;
the workflow calls it. The CLI checks run `main` against a fake GitHub API, so they exercise the
code the workflow runs, not a re-creation of it.
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import doc_review  # noqa: E402
from structure_gate import check_tree, is_hold_path  # noqa: E402
from test_waiting_human_review import CHANGED_DEFINITION, CORPUS  # noqa: E402

ROOT = Path(__file__).parent.parent
WORKFLOW = (ROOT / ".github" / "workflows" / "doc-review.yml").read_text(encoding="utf-8")
SHIPPED = doc_review.load_definition(ROOT)

HEAD = "1111111" + "a" * 33
OLD = "2222222" + "b" * 33
RUN_URL = "https://example.invalid/runs/1"
BOT = "github-actions[bot]"


def _pr(head=HEAD, fork=False, draft=False, state="open"):
    return {
        "number": 7,
        "head": {"sha": head, "repo": {"full_name": "someone/fork" if fork else "o/r"}},
        "base": {"repo": {"full_name": "o/r"}},
        "draft": draft,
        "state": state,
    }


def _file(path, sha="e" * 40, status="modified", patch=None):
    entry = {"filename": path, "sha": sha, "status": status}
    if patch is not None:
        entry["patch"] = patch
    return entry


def _comment(body, login=BOT):
    return {"user": {"login": login}, "body": body}


DOC_FILES = [_file("docs/classes/a.md", "a" * 40), _file("scripts/x.py")]
CHANGED_DOC_FILES = [_file("docs/classes/a.md", "c" * 40), _file("scripts/x.py")]


def _report_on(files, sha=OLD, run=1):
    """The comment the post step writes for a report on `files` at `sha`."""
    plan = doc_review.plan_run("pull_request", _pr(head=sha), files, [], SHIPPED)
    plan = doc_review.Plan(**{**plan.__dict__, "run": run})
    return _comment(doc_review.render_report_comment(plan, "report text", RUN_URL))


def _error_on(files, sha=OLD):
    plan = doc_review.plan_run("pull_request", _pr(head=sha), files, [], SHIPPED)
    return _comment(doc_review.render_error_comment(plan, RUN_URL))


# --- one path definition, read by the reviewer, the hold and the structure gate --------------


def test_the_reviewer_and_the_gate_select_the_same_paths_under_the_shipped_definition():
    selected = {p for p in CORPUS if doc_review.is_review_path(p, SHIPPED)}
    assert selected == {p for p in CORPUS if is_hold_path(p, SHIPPED)}
    assert {"README.md", "docs/guide.md", "incidents/incidents.csv"} <= selected
    assert not selected & {"docs/adr/0004-x.md", "scripts/README.md", "scripts/s.py"}


def test_the_reviewer_and_the_gate_follow_a_changed_definition_together(tmp_path):
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "hold-paths.json").write_text(
        json.dumps(CHANGED_DEFINITION), encoding="utf-8"
    )
    definition = doc_review.load_definition(tmp_path)
    selected = {p for p in CORPUS if doc_review.is_review_path(p, definition)}
    assert selected == {p for p in CORPUS if is_hold_path(p, CHANGED_DEFINITION)}
    assert selected == {"notes/a.md", "private/keep.md", "Makefile", "docs/adr/0004-x.md"}


# --- what is reviewed, and the digest of it -------------------------------------------------


def test_the_reviewed_set_is_the_changed_documents_that_still_exist_at_head():
    files = [
        _file("docs/classes/b.md", "b" * 40),
        _file("docs/classes/a.md", "a" * 40),
        _file("docs/classes/gone.md", "0" * 40, status="removed"),
        _file("docs/vocabularies.json", "c" * 40),
        _file("docs/adr/0004-x.md"),
        _file("scripts/s.py"),
        _file("README.md", "d" * 40, status="renamed"),
    ]
    reviewed, skipped = doc_review.select(files, SHIPPED)
    assert reviewed == [
        ("README.md", "d" * 40),
        ("docs/classes/a.md", "a" * 40),
        ("docs/classes/b.md", "b" * 40),
    ]
    assert skipped == [
        ("docs/classes/gone.md", "deleted"),
        ("docs/vocabularies.json", "not prose; the structure gate checks it"),
    ]


def test_the_digest_follows_the_reviewed_text_not_the_order_it_is_listed_in():
    one = doc_review.digest([("a.md", "1" * 40), ("b.md", "2" * 40)])
    assert re.fullmatch(r"[0-9a-f]{64}", one)
    assert one == doc_review.digest([("b.md", "2" * 40), ("a.md", "1" * 40)])
    assert one != doc_review.digest([("a.md", "1" * 40), ("b.md", "3" * 40)])
    assert one != doc_review.digest([("a.md", "1" * 40), ("c.md", "2" * 40)])


# --- the run budget: one automatic run, one request, never a third --------------------------


def test_the_automatic_run_reviews_a_pr_that_changes_a_document_once():
    first = doc_review.plan_run("pull_request", _pr(), DOC_FILES, [], SHIPPED)
    assert (first.action, first.run, first.head_sha) == ("review", 1, HEAD)
    assert first.reviewed == (("docs/classes/a.md", "a" * 40),)

    later = doc_review.plan_run("pull_request", _pr(), CHANGED_DOC_FILES, [_report_on(DOC_FILES)], SHIPPED)
    assert later.action == "skip"
    assert later.message == (
        "an automatic review already ran on this PR (on `2222222`); request a second one "
        "with Run workflow on the Doc review workflow"
    )


def test_an_errored_run_stops_the_automatic_trigger_but_does_not_spend_the_budget():
    comments = [_error_on(DOC_FILES)]
    auto = doc_review.plan_run("pull_request", _pr(), DOC_FILES, comments, SHIPPED)
    assert auto.action == "skip"
    request = doc_review.plan_run("workflow_dispatch", _pr(), DOC_FILES, comments, SHIPPED)
    assert (request.action, request.run) == ("review", 1)


def test_a_request_after_one_report_runs_only_if_the_reviewed_text_changed():
    comments = [_report_on(DOC_FILES)]
    changed = doc_review.plan_run("workflow_dispatch", _pr(), CHANGED_DOC_FILES, comments, SHIPPED)
    assert (changed.action, changed.run) == ("review", 2)

    same = doc_review.plan_run("workflow_dispatch", _pr(), DOC_FILES, comments, SHIPPED)
    assert same.action == "refuse"
    assert same.message == "the reviewed text is unchanged since the review of `2222222`"


def test_a_third_run_is_refused_with_the_reason_even_on_changed_text():
    comments = [_report_on(DOC_FILES), _report_on(CHANGED_DOC_FILES, run=2)]
    third = doc_review.plan_run(
        "workflow_dispatch", _pr(), [_file("docs/classes/a.md", "9" * 40)], comments, SHIPPED
    )
    assert third.action == "refuse"
    assert third.message == (
        "one automatic and one requested review already ran on this PR (ADR-0004 decision 5)"
    )


@pytest.mark.parametrize(
    "event, pr, files, action, message",
    [
        ("pull_request", _pr(), [_file("scripts/x.py")], "skip",
         "no document this reviewer reads changed"),
        ("workflow_dispatch", _pr(), [_file("scripts/x.py")], "refuse",
         "no document this reviewer reads changed"),
        ("pull_request", _pr(draft=True), DOC_FILES, "skip",
         "draft; the automatic run waits for ready for review"),
        ("workflow_dispatch", _pr(state="closed"), DOC_FILES, "refuse", "the PR is not open"),
        ("pull_request", _pr(fork=True), DOC_FILES, "fork", "not reviewed: fork PR, no secret"),
        ("workflow_dispatch", _pr(fork=True), DOC_FILES, "fork",
         "not reviewed: fork PR, no secret"),
    ],
)
def test_a_pr_the_reviewer_does_not_review(event, pr, files, action, message):
    plan = doc_review.plan_run(event, pr, files, [], SHIPPED)
    assert (plan.action, plan.message) == (action, message)


# --- the record the budget is read from -----------------------------------------------------

BLOCK = (
    '<!-- doc-review-run: {"digest": "d1", "kind": "report", "run": 1, '
    '"sha": "' + OLD + '"} -->'
)


def test_only_a_trailing_block_in_a_bot_comment_counts():
    comments = [
        _comment("quoted\n\n" + BLOCK, login="someone"),
        _comment("quoted " + BLOCK + " and more text"),
        _comment('<!-- doc-review: {"kind": "report", "run": 1} -->'),
        _comment("the real one\n\n" + BLOCK),
    ]
    assert doc_review.parse_records(comments) == [
        {"digest": "d1", "kind": "report", "run": 1, "sha": OLD}
    ]


def test_a_report_cannot_forge_a_record():
    plan = doc_review.plan_run("pull_request", _pr(), DOC_FILES, [], SHIPPED)
    forged = "finding\n\n" + BLOCK.replace('"run": 1', '"run": 2')
    body = doc_review.render_report_comment(plan, forged, RUN_URL)
    assert doc_review.parse_records([_comment(body)]) == [
        {"digest": plan.digest, "kind": "report", "run": 1, "sha": HEAD}
    ]


def test_a_report_cannot_close_the_collapse_early():
    plan = doc_review.plan_run("pull_request", _pr(), DOC_FILES, [], SHIPPED)
    body = doc_review.render_report_comment(plan, "finding\n</details>\nOUTSIDE", RUN_URL)
    assert body.count("</details>") == 1
    assert body.index("OUTSIDE") < body.index("</details>")


# --- the comment, the status, the report file -----------------------------------------------


def test_the_report_is_collapsed_under_a_one_line_header():
    files = DOC_FILES + [_file("docs/vocabularies.json")]
    plan = doc_review.plan_run("pull_request", _pr(), files, [], SHIPPED)
    body = doc_review.render_report_comment(plan, "FINDING-X", RUN_URL)
    assert body.splitlines()[0] == (
        "**Doc review**, advisory: findings never fail a check. Run 1 of 2 on `1111111`. "
        "Read the doc first; the report is collapsed so it does not frame the read."
    )
    assert body.index("<details>") < body.index("FINDING-X") < body.index("</details>")
    assert body.index("<details>") < body.index("`docs/vocabularies.json`") < body.index("</details>")
    assert "<details open" not in body


@pytest.mark.parametrize(
    "state, kind, description",
    [
        ("pending", "review", "review running, run 1 of 2"),
        ("success", "review", "report posted, run 1 of 2; advisory, findings never fail this"),
        ("failure", "review", "the review run errored; no report was posted"),
        ("failure", "fork", "not reviewed: fork PR, no secret"),
    ],
)
def test_the_status_goes_on_the_reviewed_head_sha(state, kind, description):
    plan = doc_review.plan_run("pull_request", _pr(fork=kind == "fork"), DOC_FILES, [], SHIPPED)
    path, body = doc_review.status_request("o/r", plan, state, RUN_URL)
    assert path == f"/repos/o/r/statuses/{HEAD}"
    assert body == {
        "state": state,
        "context": "doc-review",
        "description": description,
        "target_url": RUN_URL,
    }


def test_a_missing_or_blank_report_is_an_error(tmp_path):
    with pytest.raises(doc_review.ReportError, match="no report"):
        doc_review.read_report(tmp_path / "report.md")
    (tmp_path / "report.md").write_text("  \n", encoding="utf-8")
    with pytest.raises(doc_review.ReportError, match="empty"):
        doc_review.read_report(tmp_path / "report.md")


def test_the_task_gives_each_file_its_pass():
    files = [
        _file("README.md", "d" * 40),
        _file("docs/classes/a.md", "a" * 40),
        _file(
            "incidents/incidents.csv",
            "f" * 40,
            patch="@@ -3,2 +3,3 @@\n INC-002,x,code,issue,primary,https://e.invalid/2\n"
            "-INC-003,x,code,issue,primary,https://e.invalid/3\n"
            "+INC-003,y,code,issue,secondary,https://e.invalid/3\n"
            "+INC-009,z,review,issue,primary,https://e.invalid/9",
        ),
    ]
    plan = doc_review.plan_run("pull_request", _pr(), files, [], SHIPPED)
    task = doc_review.render_task(plan, Path("/skill.md"), Path("/out/report.md"))
    lines = {line.split("`")[1]: line for line in task.splitlines() if line.startswith("- `")}
    assert set(lines) == {"README.md", "docs/classes/a.md", "incidents/incidents.csv"}
    assert "newcomer pass only" in lines["README.md"]
    assert "<!-- class-map:start -->" in lines["README.md"]
    assert "both passes" in lines["docs/classes/a.md"]
    assert "claim-evidence pass only, on rows INC-003, INC-009" in lines["incidents/incidents.csv"]
    assert "/out/report.md" in task


# --- the steps the workflow runs ------------------------------------------------------------


class FakeGitHub:
    """Answers the calls doc_review makes; records every write."""

    def __init__(self, pr, files, comments):
        self.pr, self.files, self.comments = pr, files, comments
        self.writes = []

    def __call__(self, method, path, body=None):
        if method == "GET":
            if re.fullmatch(r"/repos/o/r/pulls/7", path):
                return self.pr
            if path.startswith("/repos/o/r/pulls/7/files"):
                return self.files if "page=1" in path else []
            if path.startswith("/repos/o/r/issues/7/comments"):
                return self.comments if "page=1" in path else []
            raise AssertionError(f"unexpected GET {path}")
        self.writes.append((method, path, body))
        return {}


def _env(monkeypatch, tmp_path, event):
    out = tmp_path / "output"
    monkeypatch.setenv("EVENT_NAME", event)
    monkeypatch.setenv("REPO", "o/r")
    monkeypatch.setenv("PR_NUMBER", "7")
    monkeypatch.setenv("RUN_URL", RUN_URL)
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    monkeypatch.chdir(ROOT)
    return out


def _outputs(path):
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines())


def test_a_review_run_sets_pending_then_posts_the_report_and_success(monkeypatch, tmp_path):
    out = _env(monkeypatch, tmp_path, "pull_request")
    gh = FakeGitHub(_pr(), DOC_FILES, [])
    monkeypatch.setattr(doc_review, "_api", gh)
    assert doc_review.main(["classify"]) == 0
    assert _outputs(out)["action"] == "review"
    assert doc_review.main(["start"]) == 0
    assert gh.writes == [
        ("POST", f"/repos/o/r/statuses/{HEAD}",
         {"state": "pending", "context": "doc-review",
          "description": "review running, run 1 of 2", "target_url": RUN_URL}),
    ]
    (tmp_path / "doc-review" / "report.md").write_text("FINDING-Y\n", encoding="utf-8")
    assert doc_review.main(["post"]) == 0
    (_, comment_path, comment), (_, status_path, status) = gh.writes[1:]
    assert comment_path == "/repos/o/r/issues/7/comments"
    assert "FINDING-Y" in comment["body"]
    assert doc_review.parse_records([_comment(comment["body"])])[0]["kind"] == "report"
    assert (status_path, status["state"]) == (f"/repos/o/r/statuses/{HEAD}", "success")


def test_a_run_without_a_report_posts_no_report_and_the_errored_step_marks_failure(
    monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path, "pull_request")
    gh = FakeGitHub(_pr(), DOC_FILES, [])
    monkeypatch.setattr(doc_review, "_api", gh)
    doc_review.main(["classify"])
    doc_review.main(["start"])
    assert doc_review.main(["post"]) == 1
    assert len(gh.writes) == 1
    assert doc_review.main(["errored"]) == 0
    (_, comment_path, comment), (_, status_path, status) = gh.writes[1:]
    assert comment_path == "/repos/o/r/issues/7/comments"
    assert doc_review.parse_records([_comment(comment["body"])])[0]["kind"] == "error"
    assert (status_path, status["state"]) == (f"/repos/o/r/statuses/{HEAD}", "failure")


def test_a_refused_request_comments_the_reason_and_sets_no_status(monkeypatch, tmp_path):
    out = _env(monkeypatch, tmp_path, "workflow_dispatch")
    gh = FakeGitHub(_pr(), DOC_FILES, [_report_on(DOC_FILES)])
    monkeypatch.setattr(doc_review, "_api", gh)
    assert doc_review.main(["classify"]) == 0
    assert _outputs(out)["action"] == "refuse"
    assert doc_review.main(["start"]) == 0
    assert [(m, p) for m, p, _ in gh.writes] == [("POST", "/repos/o/r/issues/7/comments")]
    assert "the reviewed text is unchanged since the review of `2222222`" in gh.writes[0][2]["body"]


def test_the_workflow_triggers_on_the_pr_events_and_a_request_only():
    head = WORKFLOW.split("\njobs:")[0]
    assert "    types: [opened, reopened, ready_for_review, synchronize]\n" in head
    assert re.search(r"  workflow_dispatch:\n    inputs:\n      pr:\n", head)
    assert re.findall(r"^  (\w+):$", head.split("\non:\n")[1].split("\n\n")[0], re.M) == [
        "pull_request",
        "workflow_dispatch",
    ]


def test_the_model_gets_no_shell_and_no_web():
    allowed = re.search(r'--allowedTools "([^"]+)"', WORKFLOW)
    assert allowed and allowed.group(1) == "Read,Glob,Grep,Write"
    denied = re.search(r'--disallowedTools "([^"]+)"', WORKFLOW)
    assert denied
    assert {"Bash", "WebFetch", "WebSearch"} <= set(denied.group(1).split(","))


def test_an_errored_or_cancelled_run_marks_the_status_failed():
    step = re.search(r"- name: Mark an errored run\n((?:        .*\n)+)", WORKFLOW)
    assert step, "errored step missing"
    assert "if: ${{ (failure() || cancelled()) && steps.classify.outputs.action == 'review' }}" in step.group(1)
    assert 'python "$RUNNER_TEMP/doc-review-state/doc_review.py" errored' in step.group(1)


def test_the_steps_after_the_head_checkout_run_the_script_classify_saved(monkeypatch, tmp_path):
    # The head checkout replaces scripts/ with the PR's copy; on a request, that is not the
    # script that classified the run.
    before, after = WORKFLOW.split("- name: Check out the reviewed head\n")
    assert "run: python scripts/doc_review.py classify\n" in before
    runs = re.findall(r"run: (.*doc_review\.py.*)", after)
    assert runs == [
        'python "$RUNNER_TEMP/doc-review-state/doc_review.py" post',
        'python "$RUNNER_TEMP/doc-review-state/doc_review.py" errored',
    ]
    _env(monkeypatch, tmp_path, "pull_request")
    monkeypatch.setattr(doc_review, "_api", FakeGitHub(_pr(), DOC_FILES, []))
    doc_review.main(["classify"])
    saved = tmp_path / "doc-review-state" / "doc_review.py"
    assert saved.read_bytes() == (ROOT / "scripts" / "doc_review.py").read_bytes()


def test_the_measurement_fixture_passes_the_structure_gate(tmp_path):
    # Its six defects are the reviewer's to find (seeded-defects.md); none may be a gate failure.
    for rel in (".github/hold-paths.json", "docs/vocabularies.json", "incidents/incidents.csv"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    (tmp_path / "docs" / "classes").mkdir()
    fixture = ROOT / "tests" / "fixtures" / "doc_review" / "seeded-class-doc.md"
    shutil.copy(fixture, tmp_path / "docs" / "classes" / "seeded-class-doc.md")
    assert check_tree(tmp_path) == []
