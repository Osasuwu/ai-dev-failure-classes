"""Link check — an optional PR check (#264, ADR-0004 decision 19).

Takes the files a PR changed, keeps the markdown files under the shared path definition
(``.github/hold-paths.json``, ADR-0004 decision 4), and reports every link in them with one state:

- ``alive`` — a web link answered with a 2xx status, or a relative link names a file or directory
  that exists.
- ``dead`` — a web link answered 404 or 410, or its host name does not exist; or a relative link
  names a file that does not exist. A private repository, or any page that answers 404 to a
  reader without access, is dead too: a reader of this public repo cannot open it either.
- ``not verified`` — anything else: 401 or 403 (a login, a bot check), 429 (a rate limit), 5xx,
  any other status, a redirect that ends on a sign-in page, a temporary name-lookup failure, a
  timeout or connection error, a scheme other than http(s). The link may be fine; the check
  could not tell. Open it by hand.

    python scripts/check_links.py [changed files ...]

Run from the repository root. Exits 1 if any link is ``dead``, and only then; exits 2 if the path
definition cannot be read. ``alive`` means the address resolves, nothing more: the check never
reads what a page says, so it never reports that a claim behind a link is correct. That stays
the reviewer's job. In GitHub Actions the report is also added to the job summary
(``$GITHUB_STEP_SUMMARY``).

The links are inline markdown link targets (``[text](target)`` or ``[text](<target>)``, with an
optional double-quoted title) and bare http(s) URLs, in the paragraphs ``check_quotes.py``
reads: outside code fences and HTML comments. In-page ``#anchor`` links, empty targets and
anything inside inline code are left out. An angle-bracket target may hold spaces; a web one is
fetched with each space as ``%20``. A bare URL stops at a ``|`` and before the first ``)`` it did
not open, and loses the punctuation and markup after it (``**``, ``'``, ``.``). Not parsed as
links: reference-style definitions
(``[id]: target``) and single-quoted titles (``[text](target 'title')``). A web URL in one of
those is still found as a bare URL; a relative target in one is not checked.
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
_CODE_SPAN_RE = re.compile(r"(`+).+?\1", re.S)
# [text](<target>), which may hold spaces, or [text](target): check_quotes' _LINK_RE.
_TARGET_RE = re.compile(
    r"\[[^\]]*\]\((?:<([^<>\n]*)>|((?:[^()\s]|\([^()\s]*\))+))(?:\s+\"[^\"]*\")?\)"
)
# Parentheses are allowed so a Wikipedia title survives; _trim cuts at an unbalanced one.
_BARE_URL_RE = re.compile(r"https?://[^\s<>\[\]`\"|]+")
# A sign-in page, read off the URL a redirect ended on: a host named login./signin./sso./auth.,
# or a path segment such as /login, /sign_in, /signin.aspx, /ServiceLogin, /oauth2/authorize,
# /wp-login.php, /logon, /authwall, /openid-connect/auth.
_SIGN_IN_RE = re.compile(
    r"^https?://(?:(?:login|signin|sso|auth)\.|[^/?#]+(?:/[^?#]*)?/"
    r"(?:(?:wp-)?log[-_]?(?:in|on)|_?sign[-_]?(?:in|on)|servicelogin|sso|oauth2?|authorize"
    r"|authwall|openid-connect/auth)(?:[./?#]|$))",
    re.I,
)
# Lookup errors that mean the name does not exist; any other one (EAI_AGAIN, ...) may pass.
# EAI_NODATA is missing on some platforms.
_NO_SUCH_NAME = {socket.EAI_NONAME, getattr(socket, "EAI_NODATA", socket.EAI_NONAME)}


class HostNotFound(Exception):
    """The link's host name does not resolve."""


class SignInRedirect(Exception):
    """The link redirected to a sign-in page: what is behind it was not seen."""


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
    """The final HTTP status of a GET, after redirects. A failed name lookup is tried twice, in
    case the runner's DNS blinked; if the second one says the name does not exist, raises
    HostNotFound. Raises SignInRedirect when the redirects end on a sign-in page, whatever it
    answered. Other failures propagate, a temporary lookup failure among them."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ai-dev-failure-classes check_links", "Accept": "*/*"},
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                _raise_on_sign_in(url, response.url)
                return response.status
        except urllib.error.HTTPError as err:
            # urllib raises the error with the URL the redirects ended on.
            _raise_on_sign_in(url, err.filename)
            return err.code
        except urllib.error.URLError as err:
            if not isinstance(err.reason, socket.gaierror):
                raise
            if attempt == 1:
                if err.reason.errno in _NO_SUCH_NAME:
                    raise HostNotFound(url) from err
                raise
            time.sleep(3)
    raise AssertionError("unreachable")


def _raise_on_sign_in(url: str, final: str | None) -> None:
    """Raise SignInRedirect if a request for ``url`` was redirected to a sign-in page. A link to
    a sign-in page itself is not a redirect."""
    if final and final != url and _SIGN_IN_RE.search(final):
        raise SignInRedirect(final)


def judge(url: str, doc: Path, fetch=fetch_status) -> tuple[str, str]:
    """The state of one link in ``doc``, with the reason."""
    if url.startswith(("http://", "https://")):
        try:
            status = fetch(url.split("#", 1)[0].replace(" ", "%20"))
        except HostNotFound:
            return DEAD, "host does not resolve"
        except SignInRedirect:
            return NOT_VERIFIED, "redirected to a sign-in page"
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
    # A leading "/" is the repository root, as GitHub renders it. ".." is resolved on the text,
    # as GitHub does, so "a/../b.md" finds b.md on Linux too when a/ does not exist.
    path = (
        Path.cwd() / target.lstrip("/")
        if target.startswith("/")
        else doc.parent / target
    )
    path = Path(os.path.normpath(path))
    return (ALIVE, "file exists") if path.exists() else (DEAD, "no such file")


def _links(paragraph: str) -> list[str]:
    """Markdown link targets, then bare URLs, in order, with inline code left out."""
    # A space, not nothing: the text either side of a code span must not join into one URL.
    prose = _CODE_SPAN_RE.sub(" ", paragraph)
    # findall gives (angle, plain); an empty angle target leaves both empty.
    targets = (angle or plain for angle, plain in _TARGET_RE.findall(prose))
    links = [url for url in targets if url and not url.startswith("#")]
    return links + [
        _trim(url) for url in _BARE_URL_RE.findall(_TARGET_RE.sub("", prose))
    ]


def _trim(url: str) -> str:
    """A bare URL without the markup or punctuation after it. It ends before the first ``)``
    that closes nothing opened in the URL, so a Wikipedia title keeps its parentheses."""
    depth = 0
    for index, char in enumerate(url):
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                url = url[:index]
                break
            depth -= 1
    return url.rstrip(".,;:!?*_~'")


def doc_links(text: str) -> list[tuple[int, str]]:
    """(line, url) for each link in the doc body, at its first appearance."""
    seen: dict[str, int] = {}
    for line, para, _ in paragraphs(text):
        for url in _links(para):
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

    cache: dict[
        str, tuple[str, str]
    ] = {}  # web links only; a relative link depends on its doc
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
