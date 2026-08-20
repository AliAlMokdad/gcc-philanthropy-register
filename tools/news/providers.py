# Provider adapters. Each one fetches, validates the response shape, and returns
# provider-independent candidate dicts plus a status record. Nothing downstream of here
# knows which provider a record came from, except through the `discovered_via` field.
#
# Every adapter obeys the same contract:
#   fetch(source, budget) -> (candidates, status)
#   candidates: list of dicts with at least title, url, published_raw, publisher_hint
#   status: {"source_id","ok","http","records","error","quota_note"}
#
# and the same resilience rules: connect and read timeouts, limited retries, exponential
# backoff, 429 handled as backoff rather than failure, 4xx never retried, and one
# provider's failure never aborts the run.

import email.utils, html, json, os, re, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

UA = ("gccphilanthropy-monitor/0.1 (+https://gccphilanthropy.org; "
      "philanthropy sector monitoring; contact via the site)")

CONNECT_TIMEOUT = 20
READ_TIMEOUT = 45
MAX_TRIES = 4
BACKOFF = 8          # seconds, doubled per retry. A bot-mitigation
                     # challenge wants real patience, not a fast retry.
SPACING = 1.2        # minimum gap between requests to the same host


_last_hit = {}


def _space(host):
    """One request per host per SPACING seconds. GDELT asks for five and gets it via the
    per-source spacing in its own adapter; this is the floor for everyone else."""
    now = time.time()
    prev = _last_hit.get(host, 0)
    wait = SPACING - (now - prev)
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.time()


def http_get(url, accept="*/*", tries=MAX_TRIES, spacing=None):
    """Returns (http_code, bytes, error_string). Never raises."""
    host = urllib.parse.urlparse(url).netloc
    backoff = BACKOFF
    last = (None, b"", "no attempt made")
    for attempt in range(tries):
        if spacing:
            prev = _last_hit.get(host, 0)
            gap = spacing - (time.time() - prev)
            if gap > 0:
                time.sleep(gap)
            _last_hit[host] = time.time()
        else:
            _space(host)
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": accept,
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept-Encoding": "identity",
            })
            with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as f:
                code, body = f.getcode(), f.read()
                # A 202 WITH NOTHING IN IT IS A CHALLENGE, NOT AN ANSWER. Observed on a GitHub
                # runner: ReliefWeb returned 202 and an empty body for every query while the
                # same requests from a residential address returned 200 and twenty items. Treat
                # it as "come back in a moment" and say what the far end sent, so this is
                # diagnosable from a log rather than from guesswork.
                if code != 200 or not body.strip():
                    note = "HTTP %s, %d bytes, ct=%r server=%r cf=%r" % (
                        code, len(body), f.headers.get("Content-Type"),
                        f.headers.get("Server"), f.headers.get("CF-Mitigated")
                        or f.headers.get("cf-ray") or "")
                    if attempt < tries - 1:
                        time.sleep(backoff)
                        backoff *= 2
                        last = (code, body, note + " (retrying)")
                        continue
                    return code, body, note
                return code, body, None
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()[:300]
            except Exception:
                pass
            last = (e.code, body, "HTTP %s" % e.code)
            # 429 and 5xx are worth another try. Everything else in 4xx is our fault and
            # retrying it just burns the provider's patience.
            if e.code != 429 and e.code < 500:
                return last
            if attempt < tries - 1:
                time.sleep(backoff)
                backoff *= 2
        except Exception as e:
            last = (None, b"", "%s: %s" % (type(e).__name__, e))
            if attempt < tries - 1:
                time.sleep(backoff)
                backoff *= 2
    return last


# --------------------------------------------------------------------------- helpers
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


# ReliefWeb prefixes every description with its own tag block, so the first forty to
# ninety characters of every humanitarian item were "Country: Sudan Source: Qatar Charity
# Please refer to the attached file." That is metadata sitting in the two lines a reader
# gets. Removed here, at the adapter, because it is that provider's shape and no other's.
RW_BOILER = re.compile(
    r"^(?:\s*(?:Countr(?:y|ies)|Source[s]?|Theme[s]?|Format|Disaster[s]?)\s*:\s*[^:]{0,180}?"
    r"(?=(?:Countr(?:y|ies)|Source[s]?|Theme[s]?|Format|Disaster[s]?)\s*:|$))+", re.I)
RW_ATTACHED = re.compile(
    r"\b(?:Please (?:refer to|see|find) the attached[A-Za-z ]{0,24}\.?|"
    r"Download (?:the )?(?:full )?(?:report|document|file|infographic)\.?)", re.I)


def strip_reliefweb_boiler(s, known=None):
    """Strips "Country: X Source: Y Theme: Z" from the head of a description.

    THE FIRST VERSION ONLY HALF WORKED, leaving "Source: Qatar Charity" on 48 of 50 items,
    because its repetition needed another label or the end of the string to follow and prose
    followed instead. Guessing where a proper-noun run stops is fragile: in "Source: Qatar
    Charity More than three years into" nothing distinguishes "More" from a third word of
    the organisation's name.

    So it no longer guesses. The feed states the author and the categories separately, so the
    exact values are known and are removed by identity. `known` is that list."""
    if not s:
        return s
    labels = ("Countries", "Country", "Sources", "Source", "Themes", "Theme",
              "Formats", "Format", "Disasters", "Disaster")
    vals = sorted({v.strip() for v in (known or []) if v and len(v.strip()) > 1},
                  key=len, reverse=True)
    changed = True
    guard = 0
    while changed and guard < 12:
        changed = False
        guard += 1
        t = s.lstrip(" :,;-")
        for lab in labels:
            if not t.lower().startswith(lab.lower() + ":"):
                continue
            rest = t[len(lab) + 1:].lstrip()
            # consume every known value, and the separators between them, that sits at the
            # head of the remainder
            progressed = True
            while progressed:
                progressed = False
                rest = rest.lstrip(" ,;/&")
                for v in vals:
                    if rest.lower().startswith(v.lower()):
                        rest = rest[len(v):]
                        progressed = True
                        break
            s = rest
            changed = True
            break
    s = RW_ATTACHED.sub(" ", s)
    return _WS.sub(" ", s).strip(" -\u2013\u2014:.,")


def strip_html(s):
    """Provider descriptions arrive as HTML. This is the only place markup is handled, and
    it DELETES rather than renders: the page never receives a tag, and it never uses
    innerHTML, so there are two independent barriers."""
    if not s:
        return ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>", " ", s)
    s = _TAG.sub(" ", s)
    s = html.unescape(s)
    # markdown emphasis, which some providers emit in a field documented as plain text. One
    # real item carried "Qatar Charity**.**" through to the page.
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<![A-Za-z0-9])__(.+?)__(?![A-Za-z0-9])", r"\1", s)
    s = re.sub(r"\*\*|__(?![A-Za-z0-9])", "", s)
    # a markdown link becomes its label: the URL belongs in original_url, not in prose
    s = re.sub(r"\[([^\]]{1,120})\]\((?:https?://|/)[^)\s]{1,300}\)", r"\1", s)
    return _WS.sub(" ", s).strip()


def rfc822(s):
    """RFC 822/1123 dates, as RSS uses. Returns (iso_utc, precision) or (None, None)."""
    if not s:
        return None, None
    try:
        dt = email.utils.parsedate_to_datetime(s.strip())
    except Exception:
        return None, None
    if dt is None:
        return None, None
    try:
        import datetime as _d
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_d.timezone.utc)
        dt = dt.astimezone(_d.timezone.utc)
    except Exception:
        return None, None
    # Midnight usually means the feed published only a date, but ONLY when the original
    # string carried no clock at all. Testing the CONVERTED time labelled
    # "Wed, 20 Aug 2026 04:00:00 +0400" as date-only, throwing away a time the source gave.
    has_clock = bool(re.search(r"\d{1,2}:\d{2}", s))
    precision = "datetime" if has_clock else "date"
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), precision


def iso8601(s):
    """ISO dates as the JSON providers use, CONVERTED to UTC.

    The first version matched only the leading date and time and appended "Z", so
    "2026-08-20T12:00:00+04:00" became "12:00:00Z", four hours wrong, and every offset in a
    provider feed was silently discarded."""
    if not s:
        return None, None
    import datetime as _d
    t = s.strip()
    if " " in t[:11]:
        t = t.replace(" ", "T", 1)
    date_only = not re.search(r"[T ]\d{1,2}:\d{2}", t)
    try:
        dt2 = _d.datetime.fromisoformat(t.replace("Z", "+00:00"))
    except Exception:
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", t)
        if m:
            return "%s-%s-%sT00:00:00Z" % m.groups(), "date"
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?", t)
        if not m:
            return None, None
        return ("%s-%s-%sT%s:%s:%sZ" % (m.group(1), m.group(2), m.group(3),
                                        m.group(4), m.group(5), m.group(6) or "00"),
                "datetime")
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=_d.timezone.utc)
    dt2 = dt2.astimezone(_d.timezone.utc)
    return dt2.strftime("%Y-%m-%dT%H:%M:%SZ"), ("date" if date_only else "datetime")


def gdelt_stamp(s):
    """GDELT returns 20260820T104500Z."""
    m = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z?$", (s or "").strip())
    if not m:
        return None, None
    return ("%s-%s-%sT%s:%s:%sZ" % m.groups(), "datetime")


# Some feeds use a namespace prefix they never declare, which a conforming parser must reject.
# Inspected on a real feed: it declares atom, content, dc, slash, sy and wfw, then uses `media:`
# without declaring it, and the whole 12 KB document is otherwise fine.
#
# The repair ADDS the missing declarations rather than stripping prefixes. An earlier version
# stripped every prefix, including the declared ones, which invalidated the root element. This
# leaves every element name and every value exactly as the publisher sent them.
USED_PREFIX = re.compile(rb"<([A-Za-z_][\w.-]*):")
DECL_PREFIX = re.compile(rb"xmlns:([A-Za-z_][\w.-]*)\s*=")
ROOT_OPEN = re.compile(rb"<([A-Za-z_][\w.-]*)((?:\s[^>]*)?)>")


def declare_missing_prefixes(body):
    used = set(USED_PREFIX.findall(body))
    declared = set(DECL_PREFIX.findall(body))
    missing = sorted(used - declared)
    if not missing:
        return body, []
    # the root element is the first tag that is not a declaration or a processing instruction
    m = None
    for mm in ROOT_OPEN.finditer(body):
        if not mm.group(1).startswith(b"?") and not mm.group(1).startswith(b"!"):
            m = mm
            break
    if not m:
        return body, []
    add = b"".join(b' xmlns:%s="urn:x-undeclared:%s"' % (p, p) for p in missing)
    insert_at = m.end() - 1
    return body[:insert_at] + add + body[insert_at:], [p.decode("ascii", "replace")
                                                       for p in missing]


def _tag(e):
    return re.sub(r"\{.*\}", "", e.tag)


# --------------------------------------------------------------------------- RSS / Atom
def fetch_rss(source, budget=None):
    """One adapter for every RSS and Atom feed, including ReliefWeb's.

    THE RELIEFWEB SUBTLETY, measured rather than assumed: its <source> element says
    "ReliefWeb - Updates" while <author> carries the organisation that actually wrote the
    report ("World Food Programme"). Presenting ReliefWeb as the publisher would be exactly
    the error section 17 forbids, so <author> becomes the publisher and ReliefWeb becomes
    discovered_via."""
    out, statuses = [], []
    urls = []
    if source.get("queries"):
        for q in source["queries"]:
            sep = "&" if "?" in source["url"] else "?"
            urls.append((q, source["url"] + sep + "search=" + urllib.parse.quote(q)))
    else:
        urls.append((None, source["url"]))

    for query, url in urls:
        code, body, err = http_get(url, accept="application/rss+xml,application/xml,text/xml,*/*")
        st = {"source_id": source["id"], "query": query, "ok": False,
              "http": code, "records": 0, "error": err, "quota_note": None}
        if code != 200 or not body or not body.strip():
            statuses.append(st)
            continue
        try:
            root = ET.fromstring(body)
        except Exception as e:
            # a repaired parse, for the ordinary case of a feed that uses a namespace prefix it
            # never declared. Prefixes are stripped and the same elements read under plain
            # names; nothing is added and nothing is guessed.
            root = None
            repaired, added = declare_missing_prefixes(body)
            try:
                root = ET.fromstring(repaired)
            except Exception as e2:
                st["error"] = "unparseable XML: %s (repair also failed: %s)" % (e, e2)
                statuses.append(st)
                continue
            st["quota_note"] = "parsed after declaring the prefixes this feed uses without "                               "declaring: " + ", ".join(added)

        items = root.findall(".//item") or root.findall(
            ".//{http://www.w3.org/2005/Atom}entry")
        n = 0
        for it in items:
            rec = {"title": None, "url": None, "description": None,
                   "published_raw": None, "publisher_hint": source["name"],
                   "categories": [], "guid": None, "author": None,
                   "source_declared": None, "language": source.get("lang", "en"),
                   "query_id": query or source["id"]}
            for c in it:
                t = _tag(c)
                v = (c.text or "").strip()
                if t == "title":
                    rec["title"] = html.unescape(_WS.sub(" ", v))
                elif t == "link":
                    rec["url"] = v or c.attrib.get("href")
                elif t in ("description", "summary", "content"):
                    if not rec["description"]:
                        rec["description"] = strip_html(v)
                elif t in ("pubDate", "published", "updated"):
                    if not rec["published_raw"]:
                        rec["published_raw"] = v
                elif t == "category":
                    if v:
                        rec["categories"].append(v)
                    elif c.attrib.get("term"):
                        rec["categories"].append(c.attrib["term"])
                elif t == "guid" or t == "id":
                    rec["guid"] = v
                elif t == "author" or t == "creator":
                    rec["author"] = _WS.sub(" ", v) or None
                elif t == "source":
                    rec["source_declared"] = v or None
            if not rec["title"] or not rec["url"]:
                continue
            # now that author and categories are read, the boilerplate values are known
            if source.get("publisher_from_author") and rec["description"]:
                rec["description"] = strip_reliefweb_boiler(
                    rec["description"],
                    (rec["categories"] or []) + [rec["author"] or ""])
            # Only an aggregator's <author> is a publisher. See publisher_from_author in
            # the source registry, and the byline defect it was added to fix.
            if (source.get("publisher_from_author") and rec["author"]
                    and rec["author"].lower() != source["name"].lower()):
                rec["publisher_hint"] = rec["author"]
            elif rec["author"]:
                rec["byline"] = rec["author"]      # kept, not displayed as the publisher
            rec["discovered_via"] = source["id"]
            rec["source_type_hint"] = source["type"]
            rec["official_hint"] = source.get("official", False)
            rec["feed_country"] = source.get("country")
            out.append(rec)
            n += 1
        st["ok"] = True
        st["records"] = n
        statuses.append(st)
    return out, statuses


# --------------------------------------------------------------------------- GDELT DOC
def fetch_gdelt_doc(source, budget=None):
    """GDELT DOC 2.0. Article-list mode, JSON, date-descending.

    NOT ENABLED. Measured 2026-08-20 from this machine: HTTP 429 on four of four attempts
    seven seconds apart, with a body asking for one request every five seconds. The adapter
    is complete and its normaliser is unit-tested against a recorded payload, but nothing
    about a live 200 is claimed. Spacing is set to 6s, above the stated 5, and MAXRECORDS to
    250, the documented ceiling."""
    queries = source.get("queries") or []
    out, statuses = [], []
    for q in queries:
        url = (source["url"] + "?query=" + urllib.parse.quote(q)
               + "&mode=artlist&format=json&maxrecords=250&timespan=24h&sort=datedesc")
        code, body, err = http_get(url, accept="application/json", spacing=6.0)
        st = {"source_id": source["id"], "query": q, "ok": False, "http": code,
              "records": 0, "error": err,
              "quota_note": "429 means back off, not fail" if code == 429 else None}
        if code != 200 or not body:
            statuses.append(st)
            continue
        try:
            d = json.loads(body)
        except Exception as e:
            st["error"] = "not JSON (GDELT returns a plain-text throttle notice): %s" % e
            statuses.append(st)
            continue
        arts = d.get("articles")
        if not isinstance(arts, list):
            st["error"] = "no articles array"
            statuses.append(st)
            continue
        for a in arts:
            if not isinstance(a, dict):
                continue
            u, t = a.get("url"), a.get("title")
            if not u or not t:
                continue
            out.append({
                "title": _WS.sub(" ", html.unescape(t)),
                "url": u,
                "description": None,            # DOC 2.0 artlist carries no summary
                "published_raw": a.get("seendate"),
                "publisher_hint": a.get("domain") or "",
                "categories": [], "guid": None, "author": None,
                "source_declared": a.get("domain"),
                "language": (a.get("language") or "en")[:2].lower(),
                "query_id": q,
                "discovered_via": "gdelt_doc",
                "source_type_hint": "other",     # resolved later from the domain registry
                "official_hint": False,
                "feed_country": None,
                "_stamp": "gdelt",
            })
            st["records"] += 1
        st["ok"] = True
        statuses.append(st)
    return out, statuses


# --------------------------------------------------------------------------- ReliefWeb API
def fetch_reliefweb_api(source, budget=None):
    """ReliefWeb v2 JSON.

    NOT ENABLED. Measured 2026-08-20: without appname, HTTP 400 "Missing appname parameter";
    with an arbitrary appname, HTTP 403 "You are not using an approved appname." An approved
    appname must be requested. `source.name` is the credited organisation and becomes the
    publisher; ReliefWeb is discovered_via."""
    appname = os.environ.get("RELIEFWEB_APPNAME", "")
    if not appname:
        return [], [{"source_id": source["id"], "query": None, "ok": False, "http": None,
                     "records": 0, "error": "RELIEFWEB_APPNAME not set", "quota_note": None}]
    out, statuses = [], []
    for q in (source.get("queries") or ["philanthropy"]):
        params = {
            "appname": appname, "limit": "50", "profile": "list",
            "query[value]": q, "sort[]": "date.original:desc",
        }
        fields = ["title", "url", "source.name", "source.shortname", "date.original",
                  "theme.name", "country.name", "format.name", "body"]
        url = source["url"] + "?" + urllib.parse.urlencode(params) + "".join(
            "&fields[include][]=" + urllib.parse.quote(f) for f in fields)
        code, body, err = http_get(url, accept="application/json")
        st = {"source_id": source["id"], "query": q, "ok": False, "http": code,
              "records": 0, "error": err, "quota_note": None}
        if code != 200 or not body:
            statuses.append(st)
            continue
        try:
            d = json.loads(body)
        except Exception as e:
            st["error"] = "not JSON: %s" % e
            statuses.append(st)
            continue
        for row in (d.get("data") or []):
            f = row.get("fields") or {}
            if not f.get("title") or not f.get("url"):
                continue
            src = (f.get("source") or [{}])
            pub = (src[0].get("name") if isinstance(src, list) and src else None) or "ReliefWeb"
            cats = ([t.get("name") for t in (f.get("theme") or []) if t.get("name")]
                    + [c.get("name") for c in (f.get("country") or []) if c.get("name")]
                    + [x.get("name") for x in (f.get("format") or []) if x.get("name")])
            out.append({
                "title": _WS.sub(" ", f["title"]),
                "url": f["url"],
                "description": strip_html(f.get("body") or "")[:600] or None,
                "published_raw": ((f.get("date") or {}).get("original")),
                "publisher_hint": pub,
                "categories": cats, "guid": str(row.get("id") or ""), "author": pub,
                "source_declared": "ReliefWeb", "language": "en", "query_id": q,
                "discovered_via": "reliefweb_api", "source_type_hint": "un_multilateral",
                "official_hint": True, "feed_country": None, "_stamp": "iso",
            })
            st["records"] += 1
        st["ok"] = True
        statuses.append(st)
    return out, statuses


# --------------------------------------------------------------------------- NewsData
def fetch_newsdata(source, budget=None):
    """NewsData. NOT ENABLED, no key on this machine, so nothing about its live behaviour
    is claimed here. Its free feed is delayed, which is why the page must never say LIVE."""
    key = os.environ.get("NEWSDATA_KEY", "")
    if not key:
        return [], [{"source_id": source["id"], "query": None, "ok": False, "http": None,
                     "records": 0, "error": "NEWSDATA_KEY not set", "quota_note": None}]
    out, statuses = [], []
    for q in (source.get("queries") or []):
        url = source["url"] + "?" + urllib.parse.urlencode(
            {"apikey": key, "q": q, "language": "en,ar", "size": "10"})
        code, body, err = http_get(url, accept="application/json")
        # the key is in the query string, so it must never reach a log
        safe = url.replace(key, "REDACTED")
        st = {"source_id": source["id"], "query": q, "ok": False, "http": code,
              "records": 0, "error": err, "quota_note": "1 credit per request", "url": safe}
        if code != 200 or not body:
            statuses.append(st)
            continue
        try:
            d = json.loads(body)
        except Exception as e:
            st["error"] = "not JSON: %s" % e
            statuses.append(st)
            continue
        for a in (d.get("results") or []):
            if not a.get("title") or not a.get("link"):
                continue
            out.append({
                "title": _WS.sub(" ", a["title"]), "url": a["link"],
                "description": strip_html(a.get("description") or "") or None,
                "published_raw": a.get("pubDate"),
                "publisher_hint": a.get("source_name") or a.get("source_id") or "",
                "categories": a.get("category") or [], "guid": a.get("article_id"),
                "author": None, "source_declared": a.get("source_name"),
                "language": (a.get("language") or "en")[:2],
                "query_id": q, "discovered_via": "newsdata",
                "source_type_hint": "other", "official_hint": False,
                "feed_country": None, "_stamp": "iso",
            })
            st["records"] += 1
        st["ok"] = True
        statuses.append(st)
    return out, statuses


# --------------------------------------------------------------------------- Currents
def fetch_currents(source, budget=None):
    """Currents. NOT ENABLED, no key on this machine. Its self-service terms cover API
    processing, previews, attribution and publisher links; wider redistribution needs
    separate terms, so it stays a prototype lane until that is reviewed."""
    key = os.environ.get("CURRENTS_KEY", "")
    if not key:
        return [], [{"source_id": source["id"], "query": None, "ok": False, "http": None,
                     "records": 0, "error": "CURRENTS_KEY not set", "quota_note": None}]
    out, statuses = [], []
    for q in (source.get("queries") or []):
        url = source["url"] + "?" + urllib.parse.urlencode(
            {"keywords": q, "language": "en", "page_size": "20"})
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Authorization": "Bearer " + key})
        st = {"source_id": source["id"], "query": q, "ok": False, "http": None,
              "records": 0, "error": None, "quota_note": "1 request of 1,000 per day"}
        try:
            _space(urllib.parse.urlparse(url).netloc)
            with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as f:
                st["http"] = f.getcode()
                d = json.loads(f.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            st["http"] = e.code
            st["error"] = "HTTP %s" % e.code
            statuses.append(st)
            continue
        except Exception as e:
            st["error"] = "%s: %s" % (type(e).__name__, e)
            statuses.append(st)
            continue
        for a in (d.get("news") or []):
            if not a.get("title") or not a.get("url"):
                continue
            out.append({
                "title": _WS.sub(" ", a["title"]), "url": a["url"],
                "description": strip_html(a.get("description") or "") or None,
                "published_raw": a.get("published"),
                "publisher_hint": urllib.parse.urlparse(a["url"]).netloc,
                "categories": a.get("category") or [], "guid": a.get("id"),
                "author": (a.get("author") or None), "source_declared": None,
                "language": (a.get("language") or "en")[:2],
                "query_id": q, "discovered_via": "currents",
                "source_type_hint": "other", "official_hint": False,
                "feed_country": None, "_stamp": "iso",
            })
            st["records"] += 1
        st["ok"] = True
        statuses.append(st)
    return out, statuses


ADAPTERS = {
    "rss": fetch_rss,
    "gdelt_doc": fetch_gdelt_doc,
    "reliefweb_api": fetch_reliefweb_api,
    "newsdata": fetch_newsdata,
    "currents": fetch_currents,
}


def fetch_source(source):
    fn = ADAPTERS.get(source.get("provider"))
    if not fn:
        return [], [{"source_id": source["id"], "query": None, "ok": False, "http": None,
                     "records": 0, "error": "no adapter for provider %r" % source.get("provider"),
                     "quota_note": None}]
    try:
        return fn(source)
    except Exception as e:
        # one provider blowing up must never end the run
        return [], [{"source_id": source["id"], "query": None, "ok": False, "http": None,
                     "records": 0, "error": "adapter raised %s: %s" % (type(e).__name__, e),
                     "quota_note": None}]
