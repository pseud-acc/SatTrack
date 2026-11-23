"""CelesTrak HTTP client shared by every CelesTrak download (D-008, CelesTrak usage policy updated 2026-11-16).

Used by the pipeline's constellation groups (celestrak_groups.py, D-026), the on-demand analysis fetch
(scripts/celestrak_fetch.py) and, later, SupGP (plan 4.2). Standard library only, so the analysis script runs on a
bare Python and the tests run without network packages.

Rules from the usage policy, enforced here for every caller:
  * request compressed data (gzip) and CSV;
  * any non-200 response stops the caller: redirects (301) are never followed, 403/404/429/5xx are never retried
    (Refused carries the status; a 5xx means "stop everything for at least 15 minutes");
  * a 200 whose body is not CSV (CelesTrak answers "GP data has not updated since your last download" in plain
    text when data is fetched twice per update) is a refusal too.
Never run from a machine whose IP CelesTrak has blocked: the pipeline and the fetch workflow run on GitHub's runners.
"""
from __future__ import annotations

import gzip
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

SITE = "https://celestrak.org/"
INDEX_URL = "https://celestrak.org/NORAD/elements/"
GROUP_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=csv"
CSV_HEADER = "OBJECT_NAME,"
SERVER_ERROR_PAUSE_S = 15 * 60   # usage policy: after a 500/503 all requests stop for at least 15 minutes


class Refused(Exception):
    """CelesTrak refused or returned something unexpected: stop all requests (D-008). `status` is the HTTP status,
    or None for a 200 with an unexpected body."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status

    @property
    def server_error(self) -> bool:
        return self.status is not None and self.status >= 500


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """CelesTrak's usage policy: stop on any non-200 response, redirects (301) included; never follow them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _open(request, timeout):
    return _OPENER.open(request, timeout=timeout)


def get(url: str, opener=_open, user_agent: str = "SatTrack/1.0 (+https://github.com/pseud-acc/SatTrack)") -> str:
    """One GET, gzip requested. Returns the decoded body of a 200; raises Refused on anything else."""
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip"})
    try:
        with opener(request, timeout=60) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise Refused(f"HTTP {status} for {url}", status)
            body = response.read()
            headers = getattr(response, "headers", None)
            if headers is not None and headers.get("Content-Encoding", "").lower() == "gzip":
                body = gzip.decompress(body)
            return body.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise Refused(f"HTTP {e.code} for {url}", e.code) from None


def groups_on_index(html: str) -> list[str]:
    """Group names linked from the GP index page, in page order, without duplicates."""
    return list(dict.fromkeys(re.findall(r"gp\.php\?GROUP=([A-Za-z0-9_-]+)", html)))


def check_csv(body: str, url: str, required: tuple[str, ...] = ()) -> int:
    """Number of data rows; raise Refused if the body isn't GP CSV or lacks a required column."""
    if not body.startswith(CSV_HEADER):
        raise Refused(f"not CSV from {url}: {body[:80]!r}")
    header = body.split("\n", 1)[0].strip().split(",")
    missing = [c for c in required if c not in header]
    if missing:
        raise Refused(f"CSV from {url} lacks {missing}")
    return max(0, len(body.strip().splitlines()) - 1)


# Link texts on the index page that name a format or a view, not a group (never a group's title).
_FORMAT_WORDS = {"tle", "2le", "3le", "omm", "xml", "kvn", "json", "json-pp", "csv", "table", "html", "txt",
                 "supgp", "sup-gp", "data", "format", "formats"}
_GROUP_IN_HREF = re.compile(r"GROUP=([A-Za-z0-9_-]+)")


class _IndexParser(HTMLParser):
    """Collects, per innermost table cell (or per link outside any cell), the groups its links name and its texts.

    On CelesTrak's GP index page (archived 2026-11-23, fetch run 45099334610) each group is one <td>: its title as
    plain text, then icon-only links to gp.php?GROUP=<group>&FORMAT=csv and table.php?GROUP=<group>. A row can hold
    two groups (e.g. Starlink and OneWeb), and the group tables sit inside an outer layout table, so cells nest."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells: list[dict] = []
        self._open: list[dict] = []           # open <td>/<th> cells, innermost last
        self._link: dict | None = None        # a group link outside any cell

    def handle_starttag(self, tag, attrs):
        if tag in ("td", "th"):
            cell = {"groups": [], "texts": []}
            self.cells.append(cell)
            self._open.append(cell)
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            m = _GROUP_IN_HREF.search(href) if ("gp.php" in href or "table.php" in href) else None
            if not m:
                return
            if self._open:
                self._open[-1]["groups"].append(m.group(1))
            else:                              # a group link outside any table: its own text is the title
                self._link = {"groups": [m.group(1)], "texts": []}
                self.cells.append(self._link)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._open:
            self._open.pop()
        elif tag == "a":
            self._link = None

    def handle_data(self, data):
        text = " ".join(data.split())
        if not text:
            return
        if self._open:
            self._open[-1]["texts"].append(text)
        elif self._link is not None:
            self._link["texts"].append(text)


def group_titles(html: str) -> dict[str, str]:
    """{group: title} from the GP index page, e.g. {"gps-ops": "GPS Operational", "iridium-NEXT": "Iridium NEXT"}.

    A group's title is the first text of its table cell (or of its own link, outside a table) that isn't a format or
    view label (TLE, JSON, CSV, Table, ...). Cells naming more than one group are skipped. A group without a title is
    left out, so the caller can tell the page changed layout. Checked against the live page archived on 2026-11-23
    (fetch run 45099334610; trimmed copy in ingestion/tests/fixtures/celestrak/).
    """
    parser = _IndexParser()
    parser.feed(html)
    titles: dict[str, str] = {}
    for cell in parser.cells:
        groups = list(dict.fromkeys(cell["groups"]))
        if len(groups) != 1 or groups[0] in titles:
            continue
        for text in cell["texts"]:
            text = text.strip(" :|-")
            if text and text.lower() not in _FORMAT_WORDS:
                titles[groups[0]] = text
                break
    return titles
