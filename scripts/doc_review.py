"""Advisory doc reviewer: every decision `.github/workflows/doc-review.yml` acts on (#244).

ADR-0004 decision 5: the reviewer runs once by itself on a PR that changes a document, once more
on request when the reviewed text changed since, and never a third time. Its findings never fail
a check; the `doc-review` commit status on the reviewed head SHA fails only when the run itself
failed. Which files are documents is `.github/hold-paths.json`, the one definition the hold and
the structure gate also read.

The workflow calls four subcommands, in order:

  classify  reads the PR, its files and its comments; decides review / skip / refuse / fork;
            writes the plan, the model's task and a copy of this script and the skill to
            $RUNNER_TEMP before the model runs. Read-only on GitHub.
  start     acts on a non-review plan (a refusal comment, a fork's failed status) or sets the
            pending status for a review.
  post      posts the model's report as a collapsed comment, then the success status. A missing
            or empty report exits 1 and posts nothing.
  errored   after a failed or cancelled review: an error comment and the failure status.

The budget is read from a trailing `<!-- doc-review-run: {...} -->` block in comments by
github-actions[bot]. A report spends a run; an error does not, but it stops the automatic
trigger from firing again on later pushes.
"""

import hashlib
import json
import os
import re
import shutil
import sys
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

BOT_LOGIN = "github-actions[bot]"
STATUS_CONTEXT = "doc-review"
MARKER = "doc-review-run"
BUDGET = 2
DEFINITION_FILE = ".github/hold-paths.json"
SKILL_FILE = ".agents/skills/review-doc/SKILL.md"

NO_DOC = "no document this reviewer reads changed"
FORK = "not reviewed: fork PR, no secret"
DRAFT = "draft; the automatic run waits for ready for review"
NOT_OPEN = "the PR is not open"
REFUSE_BUDGET = (
    "one automatic and one requested review already ran on this PR (ADR-0004 decision 5)"
)
NOT_PROSE = "not prose; the structure gate checks it"
NO_ROWS = "no added or changed rows"

_BLOCK = re.compile(r"<!-- " + MARKER + r": (\{.*?\}) -->\s*\Z", re.S)
_ROW_ID = re.compile(r"^\+(INC-\d+),")


class ReportError(Exception):
    """The model left no usable report."""


@dataclass(frozen=True)
class Plan:
    action: str  # review | skip | refuse | fork
    message: str
    run: int
    head_sha: str
    digest: str
    reviewed: tuple  # ((path, blob sha), ...), sorted by path
    skipped: tuple  # ((path, reason), ...), sorted by path
    rows: tuple = ()  # ((dataset path, (row id, ...)), ...); no entry means every row


# --- paths --------------------------------------------------------------------------------


def load_definition(root):
    return json.loads((Path(root) / DEFINITION_FILE).read_text(encoding="utf-8"))


def is_review_path(path, definition):
    """True if `path` is a document under `definition`.

    A listed file is in; otherwise an excluded prefix wins over a held prefix. The same rule as
    `tests/structure_gate.py::is_hold_path`, written again on purpose so the agreement test
    compares two implementations rather than one with itself.
    """
    if path in definition.get("files", []):
        return True
    if any(path.startswith(p) for p in definition.get("excluded_prefixes", [])):
        return False
    return any(path.startswith(p) for p in definition.get("prefixes", []))


def review_kind(path):
    if path == "README.md":
        return "readme"
    if path.endswith(".csv"):
        return "dataset"
    if path.endswith(".md"):
        return "doc"
    return None


def changed_rows(patch):
    """Row ids on the added side of a dataset patch, sorted."""
    ids = set()
    for line in patch.splitlines():
        match = _ROW_ID.match(line)
        if match:
            ids.add(match.group(1))
    return tuple(sorted(ids))


def select(files, definition):
    """Split the PR's documents into (reviewed, skipped).

    reviewed: sorted (path, blob sha at head) for documents that exist at head and are prose.
    skipped: sorted (path, reason) for the other documents. Files outside the definition are in
    neither.
    """
    reviewed, skipped = [], []
    for entry in files:
        path = entry["filename"]
        if not is_review_path(path, definition):
            continue
        if entry.get("status") == "removed":
            skipped.append((path, "deleted"))
        elif review_kind(path) is None:
            skipped.append((path, NOT_PROSE))
        elif (
            review_kind(path) == "dataset"
            and entry.get("patch") is not None
            and not changed_rows(entry["patch"])
        ):
            skipped.append((path, NO_ROWS))
        else:
            reviewed.append((path, entry["sha"]))
    return sorted(reviewed), sorted(skipped)


def digest(reviewed):
    """sha256 over the sorted (path, blob sha) pairs: changes exactly when the reviewed text does."""
    text = "".join(f"{path}\0{sha}\n" for path, sha in sorted(reviewed))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- the budget ---------------------------------------------------------------------------


def parse_records(comments):
    """The run records: a trailing block in a comment by the workflow's bot, nothing else."""
    records = []
    for comment in comments:
        if (comment.get("user") or {}).get("login") != BOT_LOGIN:
            continue
        match = _BLOCK.search(comment.get("body") or "")
        if not match:
            continue
        try:
            record = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if (
            isinstance(record, dict)
            and record.get("kind") in ("report", "error")
            and isinstance(record.get("run"), int)
            and isinstance(record.get("sha"), str)
        ):
            records.append(record)
    return records


def _is_fork(pr):
    head_repo = (pr.get("head") or {}).get("repo") or {}
    base_repo = (pr.get("base") or {}).get("repo") or {}
    return head_repo.get("full_name") != base_repo.get("full_name")


def plan_run(event, pr, files, comments, definition):
    head = pr["head"]["sha"]
    reviewed, skipped = select(files, definition)
    rows = tuple(
        (entry["filename"], changed_rows(entry["patch"]))
        for entry in files
        if entry.get("patch") is not None
        and (entry["filename"], entry["sha"]) in reviewed
        and review_kind(entry["filename"]) == "dataset"
    )
    d = digest(reviewed)

    def make(action, message, run=0):
        return Plan(action, message, run, head, d, tuple(reviewed), tuple(skipped), rows)

    if _is_fork(pr):
        return make("fork", FORK)
    records = parse_records(comments)
    reports = [r for r in records if r["kind"] == "report"]

    if event == "pull_request":
        if pr.get("draft"):
            return make("skip", DRAFT)
        if records:
            return make(
                "skip",
                f"an automatic review already ran on this PR (on `{records[0]['sha'][:7]}`); "
                "request a second one with Run workflow on the Doc review workflow",
            )
        if not reviewed:
            return make("skip", NO_DOC)
        return make("review", "", 1)

    if pr.get("state") != "open":
        return make("refuse", NOT_OPEN)
    if not reviewed:
        return make("refuse", NO_DOC)
    if len(reports) >= BUDGET:
        return make("refuse", REFUSE_BUDGET)
    if reports and reports[-1].get("digest") == d:
        return make(
            "refuse",
            f"the reviewed text is unchanged since the review of `{reports[-1]['sha'][:7]}`",
        )
    return make("review", "", len(reports) + 1)


# --- what the job writes ------------------------------------------------------------------


def render_block(plan, kind):
    record = {"digest": plan.digest, "kind": kind, "run": plan.run, "sha": plan.head_sha}
    return f"<!-- {MARKER}: {json.dumps(record, sort_keys=True)} -->"


def _inert(text):
    """Model text as it goes into a comment: it cannot open a block or close the collapse."""
    return text.replace("<!--", "&lt;!--").replace("</details", "&lt;/details")


def render_report_comment(plan, report, run_url):
    lines = [
        f"**Doc review**, advisory: findings never fail a check. Run {plan.run} of {BUDGET} on "
        f"`{plan.head_sha[:7]}`. Read the doc first; the report is collapsed so it does not "
        "frame the read.",
        "",
        "<details>",
        f"<summary>Report on {len(plan.reviewed)} file(s)</summary>",
        "",
        _inert(report.strip()),
        "",
    ]
    if plan.skipped:
        lines.append("Not reviewed:")
        lines += [f"- `{path}`: {reason}" for path, reason in plan.skipped]
        lines.append("")
    lines += ["</details>", "", f"[Run log]({run_url})", "", render_block(plan, "report")]
    return "\n".join(lines)


def render_error_comment(plan, run_url):
    return "\n".join(
        [
            f"**Doc review** errored on `{plan.head_sha[:7]}`: no report was posted, and the "
            "`doc-review` status is failed. This run does not count toward the two reviews; "
            "request one with Run workflow on the Doc review workflow.",
            "",
            f"[Run log]({run_url})",
            "",
            render_block(plan, "error"),
        ]
    )


def render_refusal(plan):
    return f"**Doc review** not run: {plan.message}."


def status_request(repo, plan, state, target_url):
    if plan.action == "fork":
        description = FORK
    elif state == "pending":
        description = f"review running, run {plan.run} of {BUDGET}"
    elif state == "success":
        description = f"report posted, run {plan.run} of {BUDGET}; advisory, findings never fail this"
    else:
        description = "the review run errored; no report was posted"
    body = {
        "state": state,
        "context": STATUS_CONTEXT,
        "description": description,
        "target_url": target_url,
    }
    return f"/repos/{repo}/statuses/{plan.head_sha}", body


def read_report(path):
    path = Path(path)
    if not path.is_file():
        raise ReportError(f"no report at {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ReportError("the report is empty")
    return text


def render_task(plan, skill_path, report_path):
    rows = dict(plan.rows)
    lines = [
        "# Doc review task",
        "",
        f"Follow the skill at `{Path(skill_path).as_posix()}`. Review each file below, at the PR's head, with the "
        "pass it names, and nothing else.",
        "",
    ]
    for path, _sha in plan.reviewed:
        kind = review_kind(path)
        if kind == "readme":
            what = (
                "newcomer pass only, on the hand-written text; skip the generated class map "
                "between `<!-- class-map:start -->` and `<!-- class-map:end -->`"
            )
        elif kind == "dataset":
            ids = rows.get(path)
            what = (
                f"claim-evidence pass only, on rows {', '.join(ids)}"
                if ids
                else "claim-evidence pass only, on every row"
            )
        else:
            what = "both passes, the whole file"
        lines.append(f"- `{path}`: {what}")
    lines += [
        "",
        "Vocabulary: `docs/vocabularies.json`. The approval rule: "
        "`docs/classes/irreversible-effects.md`.",
        "",
        f"Write the report to `{Path(report_path).as_posix()}`. Post nothing.",
        "",
    ]
    return "\n".join(lines)


# --- GitHub and the CLI -------------------------------------------------------------------


def _api(method, path, body=None):
    request = urllib.request.Request(
        "https://api.github.com" + path,
        method=method,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
    return json.loads(raw) if raw else {}


def _pages(path):
    items, page = [], 1
    while True:
        batch = _api("GET", f"{path}?per_page=100&page={page}")
        items += batch
        if len(batch) < 100:
            return items
        page += 1


def _dirs():
    temp = Path(os.environ["RUNNER_TEMP"])
    return temp / "doc-review-state", temp / "doc-review"


def _load_plan():
    state, _ = _dirs()
    data = json.loads((state / "plan.json").read_text(encoding="utf-8"))
    data["reviewed"] = tuple(tuple(x) for x in data["reviewed"])
    data["skipped"] = tuple(tuple(x) for x in data["skipped"])
    data["rows"] = tuple((p, tuple(ids)) for p, ids in data["rows"])
    return Plan(**data)


def _summary(text):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
        f.write(text + "\n")


def _comment(repo, number, body):
    _api("POST", f"/repos/{repo}/issues/{number}/comments", {"body": body})


def _status(repo, plan, state, url):
    path, body = status_request(repo, plan, state, url)
    _api("POST", path, body)


def main(argv):
    command = argv[0]
    repo, number, url = os.environ["REPO"], os.environ["PR_NUMBER"], os.environ["RUN_URL"]

    if command == "classify":
        pr = _api("GET", f"/repos/{repo}/pulls/{number}")
        files = _pages(f"/repos/{repo}/pulls/{number}/files")
        comments = _pages(f"/repos/{repo}/issues/{number}/comments")
        plan = plan_run(os.environ["EVENT_NAME"], pr, files, comments, load_definition(Path.cwd()))
        state, work = _dirs()
        state.mkdir(parents=True, exist_ok=True)
        work.mkdir(parents=True, exist_ok=True)
        (state / "plan.json").write_text(json.dumps(asdict(plan)), encoding="utf-8")
        shutil.copy(__file__, state / "doc_review.py")
        if plan.action == "review":
            shutil.copy(Path.cwd() / SKILL_FILE, work / "review-doc.md")
            task = render_task(plan, work / "review-doc.md", work / "report.md")
            (work / "task.md").write_text(task, encoding="utf-8")
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"action={plan.action}\nmessage={plan.message}\n")
            f.write(f"head_sha={plan.head_sha}\nrun={plan.run}\n")
        print(f"doc-review: {plan.action} {plan.message}".rstrip())
        return 0

    plan = _load_plan()
    if command == "start":
        if plan.action == "review":
            _status(repo, plan, "pending", url)
        elif plan.action == "fork":
            _status(repo, plan, "failure", url)
            _summary(f"**Doc review:** {plan.message}")
        else:
            if plan.action == "refuse":
                _comment(repo, number, render_refusal(plan))
            _summary(f"**Doc review:** {plan.message}")
        return 0

    if command == "post":
        try:
            report = read_report(_dirs()[1] / "report.md")
        except ReportError as e:
            print(f"::error::{e}")
            return 1
        _comment(repo, number, render_report_comment(plan, report, url))
        _status(repo, plan, "success", url)
        return 0

    if command == "errored":
        _comment(repo, number, render_error_comment(plan, url))
        _status(repo, plan, "failure", url)
        return 0

    print(f"unknown command {command!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
