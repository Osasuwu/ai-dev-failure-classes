"""Link check — an optional PR check (#264, ADR-0004 decision 19).

Takes the files a PR changed, keeps the markdown files under the shared path definition
(``.github/hold-paths.json``, ADR-0004 decision 4), and reports every link in them with one state:

- ``alive`` — a web link answered with a 2xx status, or a relative link names a file or directory
  that exists.
- ``dead`` — a web link answered 404 or 410, or its host does not resolve; or a relative link
  names a file that does not exist.
- ``not verified`` — anything else: 401 or 403 (a login, a bot check), 429 (a rate limit), 5xx,
  any other status, a timeout or connection error, a scheme other than http(s). The link may be
  fine; the check could not tell. Open it by hand.

    python scripts/check_links.py [changed files ...]

Run from the repository root. Exits 1 if any link is ``dead``, and only then; exits 2 if the path
definition cannot be read. ``alive`` means the address resolves, nothing more: the check never
reads what a page says, so it never reports that a claim behind a link is correct. That stays
the reviewer's job. In GitHub Actions the report is also added to the job summary
(``$GITHUB_STEP_SUMMARY``).

The links are the ones ``check_quotes.py`` sees: markdown link targets and bare URLs, outside
code fences and HTML comments, without in-page ``#anchor`` links.
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote

from check_quotes import paragraphs

ALIVE, DEAD, NOT_VERIFIED = "alive", "dead", "not verified"
DEAD_STATUSES = (404, 410)
DEFINITION_FILE = ".github/hold-paths.json"
HEADER = "whether each link in the changed docs resolves. It does not check what a page says."

_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class HostNotFound(Exception):
    """The link's host name does not resolve."""


def is_checked(path: str, definition: dict) -> bool:
    """A markdown file the path definition selects. The definition's order is the one
    ``tests/structure_gate.py:is_hold_path`` uses: a listed file, else not under an excluded
    prefix, else under a listed prefix."""
    if not path.endswith(".md"):
        return False
    if path in definition["files"]:
        return True
    if path.startswith(tuple(definition["excluded_prefixes"])):
        return False
    return path.startswith(tuple(definition["prefixes"]))


def fetch_status(url: str) -> int:
    """The final HTTP status of a GET, after redirects. Raises HostNotFound when the host does
    not resolve (tried twice, in case the runner's DNS blinked); other failures propagate."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "jarvis-oss check_links", "Accept": "*/*"}
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.status
        except urllib.error.HTTPError as err:
            return err.code
        except urllib.error.URLError as err:
            if not isinstance(err.reason, socket.gaierror):
                raise
            if attempt == 1:
                raise HostNotFound(url) from err
            time.sleep(3)
    raise AssertionError("unreachable")


def judge(url: str, doc: Path, fetch=fetch_status) -> tuple[str, str]:
    """The state of one link in ``doc``, with the reason."""
    if url.startswith(("http://", "https://")):
        try:
            status = fetch(url.split("#", 1)[0])
        except HostNotFound:
            return DEAD, "host does not resolve"
        except Exception as err:  # a timeout, a reset, a TLS error: nothing was judged
            return NOT_VERIFIED, type(err).__name__
        if 200 <= status < 300:
            return ALIVE, f"HTTP {status}"
        if status in DEAD_STATUSES:
            return DEAD, f"HTTP {status}"
        return NOT_VERIFIED, f"HTTP {status}"
    if _SCHEME_RE.match(url):
        return NOT_VERIFIED, "not an http(s) or file link"
    target = unquote(url.split("#", 1)[0].split("?", 1)[0])
    # A leading "/" is the repository root, as GitHub renders it.
    path = Path.cwd() / target.lstrip("/") if target.startswith("/") else doc.parent / target
    return (ALIVE, "file exists") if path.exists() else (DEAD, "no such file")


def doc_links(text: str) -> list[tuple[int, str]]:
    """(line, url) for each link in the doc body, at its first appearance."""
    seen: dict[str, int] = {}
    for line, _, urls in paragraphs(text):
        for url in urls:
            seen.setdefault(url, line)
    return [(line, url) for url, line in seen.items()]


def main(argv: list[str], fetch=fetch_status) -> int:
    try:
        definition = json.loads(Path(DEFINITION_FILE).read_text(encoding="utf-8"))
        docs = [p for p in argv if is_checked(p.replace("\\", "/"), definition)]
    except (OSError, ValueError, KeyError, TypeError) as err:
        print(f"Cannot read the path definition {DEFINITION_FILE}: {err}")
        return 2
    if not docs:
        line = "No changed markdown file under the shared path definition; nothing to check."
        print(line)
        _write_step_summary([f"**Link check:** {line}"])
        return 0

    cache: dict[str, tuple[str, str]] = {}  # web links only; a relative link depends on its doc
    counts = {ALIVE: 0, DEAD: 0, NOT_VERIFIED: 0}
    report: list[str] = []
    print(f"Link check: {HEADER}")
    for name in docs:
        doc = Path(name)
        for line, url in doc_links(doc.read_text(encoding="utf-8")):
            web = url.startswith(("http://", "https://"))
            if web and url.split("#", 1)[0] in cache:
                state, reason = cache[url.split("#", 1)[0]]
            else:
                state, reason = judge(url, doc, fetch=fetch)
                if web:
                    cache[url.split("#", 1)[0]] = (state, reason)
            counts[state] += 1
            print(f"{name}:{line}: {state}: {url} ({reason})")
            report.append(f"- `{name}:{line}` {state}: {url} ({reason})")
    summary = (
        f"{len(docs)} file(s), {sum(counts.values())} link(s): {counts[ALIVE]} alive, "
        f"{counts[DEAD]} dead, {counts[NOT_VERIFIED]} not verified "
        "(not verified is not a failure; open those by hand)"
    )
    print(summary)
    _write_step_summary([f"**Link check:** {HEADER}", "", *report, "", summary])
    return 1 if counts[DEAD] else 0


def _write_step_summary(lines: list[str]) -> None:
    """In GitHub Actions, also add the report to the job summary page."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
