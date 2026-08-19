# Builds oecd.json: what the Gulf states report to the OECD about the aid they give.
#
#   "C:\Users\Ali Al Mokdad\AppData\Local\Python\bin\python.exe" build_oecd.py
#
# THREE THINGS THIS SCRIPT EXISTS TO GET RIGHT, each of which was got WRONG first.
#
# 1. THE MEASURE. Since 2018 the OECD headline for official development assistance is the
#    GRANT EQUIVALENT (measure 11010, flow 1160), not net cash disbursements (1010, 1140).
#    The first version used net cash and would have published that Kuwait's aid had "all but
#    stopped", $11m in 2023. On the headline measure it was $82m that year and $218m in 2025:
#    a steep decline, not a collapse. Both series are kept here, and the page must say which
#    it is showing.
#
# 2. THE AGGREGATION. Every SDMX dimension carries its own total code, so summing rows
#    without pinning CHANNEL, MODALITY, MD_DIM, MD_ID and PRICE_BASE counts the same money
#    once per combination. Unpinned, Saudi Arabia's 2022 aid to Egypt came out at $62bn,
#    ten times the real figure, and looked entirely plausible. Every query below pins every
#    dimension it is not grouping by.
#
# 3. WHAT ANSWERS THE READER'S QUESTION. A sector code does not say whether money reaches
#    organisations: sector 500 holds budget support, food aid and commodity aid together, and
#    510 is nested INSIDE 500 rather than beside it. The CHANNEL of delivery is the field that
#    actually says who implemented the activity, so that is what this collects.
import csv, io, json, os, subprocess, sys, time

BASE = "https://sdmx.oecd.org"
DAC1 = BASE + "/public/rest/data/OECD.DCD.FSD,DSD_DAC1@DF_DAC1,"
CRS = BASE + "/dcd-public/rest/data/OECD.DCD.FSD,DSD_CRS@DF_CRS,1.6"
DSD_CRS = BASE + "/dcd-public/rest/datastructure/OECD.DCD.FSD/DSD_CRS/1.6?references=children"
STATES = ["SAU", "ARE", "QAT", "KWT", "OMN", "BHR"]
NAME = {"SAU": "Saudi Arabia", "ARE": "United Arab Emirates", "QAT": "Qatar",
        "KWT": "Kuwait", "OMN": "Oman", "BHR": "Bahrain"}
FROM = 2015
CRS_FROM = 2020                      # composition needs recent years, not the whole run
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "oecd.json")
SECTOR_GROUPS = ["100", "200", "300", "400", "500", "600", "700", "910", "930", "998"]
# the scheduled job runs on linux, where TMP is not set
TMP = os.environ.get("TMP") or os.environ.get("TMPDIR") or "/tmp"


def fetch(url, tag):
    """curl, because the OECD returns 403 to the default python user agent."""
    p = os.path.join(TMP, "oecd_%s.csv" % tag)
    for i in range(3):
        r = subprocess.run(["curl", "-s", "-m", "240", "-o", p, "-w", "%{http_code}", url],
                           capture_output=True, text=True)
        if r.stdout.strip() == "200":
            rows = list(csv.DictReader(io.open(p, encoding="utf-8", errors="replace")))
            print("   %-22s %6d rows" % (tag, len(rows)))
            return rows
        time.sleep(4 * (i + 1))
    raise SystemExit("OECD fetch failed: " + tag)


UNPARSED = []


def val(r):
    """A value that will not parse is RECORDED, not quietly turned into zero. Swallowing it
    meant a response that had gone wrong arrived as a page full of confident zeroes, which is
    indistinguishable from a state that gave nothing."""
    raw = r.get("OBS_VALUE", "")
    if raw == "" or raw is None:
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        UNPARSED.append("%s %s %r" % (r.get("DONOR"), r.get("TIME_PERIOD"), raw))
        return None
    if v != v or v in (float("inf"), float("-inf")):
        UNPARSED.append("%s %s not finite" % (r.get("DONOR"), r.get("TIME_PERIOD")))
        return None
    return round(v, 1)


def series(rows, into):
    for r in rows:
        v = val(r)
        if v is None:
            continue                      # an absent observation is absent, not zero
        into.setdefault(r["DONOR"], {})[int(r["TIME_PERIOD"])] = v


print("OECD build")
# ------------------------------------------------------------------ headline, both measures
q_ge = "/" + "+".join(STATES) + "..11010..1160.USD.V.?startPeriod=%d&format=csvfile" % FROM
q_net = "/" + "+".join(STATES) + "..1010..1140.USD.V.?startPeriod=%d&format=csvfile" % FROM
ge, net = {}, {}
series(fetch(DAC1 + q_ge, "oda grant-equiv"), ge)
series(fetch(DAC1 + q_net, "oda net cash"), net)
reporting = [c for c in STATES if ge.get(c)]
silent = [c for c in STATES if not ge.get(c)]
D = "+".join(reporting)

# ------------------------------------------------------------------ CRS composition
pin = "._T.D.V._T.0.USD."          # MODALITY, FLOW_TYPE, PRICE_BASE, MD_DIM, MD_ID, UNIT
chan = fetch(CRS + "/" + D + ".DPGC.1000.100.." + pin.lstrip(".") +
             "?startPeriod=%d&format=csvfile" % CRS_FROM, "channel of delivery")
sect = fetch(CRS + "/" + D + ".DPGC..100._T" + pin +
             "?startPeriod=%d&format=csvfile" % CRS_FROM, "sector group")
recp = fetch(CRS + "/" + D + "..1000.100._T" + pin +
             "?startPeriod=%d&format=csvfile" % CRS_FROM, "recipient")

channels, sectors, crs_total, recipients = {}, {}, {}, {}
for r in chan:
    v = val(r)
    if v is None:
        continue
    y, d = int(r["TIME_PERIOD"]), r["DONOR"]
    channels.setdefault(d, {}).setdefault(y, {})[r["CHANNEL"]] = v
for r in sect:
    v = val(r)
    if v is None:
        continue
    y, d, s = int(r["TIME_PERIOD"]), r["DONOR"], r["SECTOR"]
    if s == "1000":
        crs_total.setdefault(d, {})[y] = v
    elif s in SECTOR_GROUPS:
        sectors.setdefault(d, {}).setdefault(y, {})[s] = v
AGG = {"DPGC", "_T", "LDC", "A", "B", "C", "D", "E", "F", "G", "H"}
for r in recp:
    c = r["RECIPIENT"]
    if c in AGG or len(c) != 3 or not c.isalpha():
        continue
    v = val(r)
    if v is None:
        continue
    recipients.setdefault(r["DONOR"], {}).setdefault(int(r["TIME_PERIOD"]), {})[c] = v

# A value that would not parse is a broken response, not a small gap. Stopping here beats
# publishing a page of confident zeroes that reads exactly like a state which gave nothing.
if UNPARSED:
    raise SystemExit("%d observations would not parse, first few: %s"
                     % (len(UNPARSED), "; ".join(UNPARSED[:5])))

# what the OECD actually said about these observations, read rather than asserted
OBS_SEEN = ", ".join(sorted({r.get("OBS_STATUS", "") for r in (chan + sect + recp)
                             if r.get("OBS_STATUS", "")})) or "none given"

# the sector groups are mutually exclusive, so they must sum to the all-sectors row
bad = 0
for d in sectors:
    for y in sectors[d]:
        parts, whole = sum(sectors[d][y].values()), crs_total.get(d, {}).get(y, 0)
        if whole and abs(parts - whole) / whole > 0.02:
            print("   MISMATCH %s %d: parts %.1f vs total %.1f" % (d, y, parts, whole)); bad += 1
assert not bad, "sector groups do not sum to the total, the pinning is wrong"

# ------------------------------------------------------------------ names
subprocess.run(["curl", "-s", "-m", "180", "-o", os.path.join(TMP, "oecd_dsd.xml"), DSD_CRS],
               capture_output=True)
import re
X = io.open(os.path.join(TMP, "oecd_dsd.xml"), encoding="utf-8", errors="replace").read()


def codelist(cid):
    m = re.search(r'<structure:Codelist[^>]*\bid="%s".*?</structure:Codelist>' % cid, X, re.S)
    o = {}
    if m:
        for c in re.finditer(r'<structure:Code[^>]*\bid="([^"]+)"(.*?)</structure:Code>', m.group(0), re.S):
            n = re.search(r'<common:Name[^>]*>([^<]+)</common:Name>', c.group(2))
            if n:
                o[c.group(1)] = n.group(1).replace("&amp;", "and")
    return o


SEC, REC, CHN = codelist("CL_DAC_SECTOR"), codelist("CL_AREA_ORG"), codelist("CL_CRS_CHANNEL")
assert SEC.get("510") and CHN.get("20000"), "codelists did not load"

years = lambda m: {d: sorted(m[d]) for d in m}
doc = {
    "meta": {
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "OECD",
        "queries": {
            "headline": {"dataflow": "OECD.DCD.FSD:DSD_DAC1@DF_DAC1", "measure": "11010",
                         "flow": "1160", "unit": "USD", "price": "V",
                         "label": "official development assistance, grant equivalent, current USD million"},
            "net_cash": {"dataflow": "OECD.DCD.FSD:DSD_DAC1@DF_DAC1", "measure": "1010",
                         "flow": "1140", "unit": "USD", "price": "V",
                         "label": "official development assistance, net disbursements, current USD million"},
            "composition": {"dataflow": "OECD.DCD.FSD:DSD_CRS@DF_CRS(1.6)", "measure": "100",
                            "flow": "D", "unit": "USD", "price": "V",
                            "pinned": "MODALITY=_T, MD_DIM=_T, MD_ID=0",
                            "label": "gross bilateral ODA disbursements, current USD million"},
        },
        "obs_status": OBS_SEEN,
        "reporting": reporting,
        "not_reporting": silent,
        "headline_years": years(ge),
        "composition_years": years(crs_total),
    },
    "names": NAME,
    "oda": {d: {str(y): v for y, v in ge[d].items()} for d in ge},
    "oda_net": {d: {str(y): v for y, v in net[d].items()} for d in net},
    "channels": {d: {str(y): v for y, v in channels[d].items()} for d in channels},
    "sectors": {d: {str(y): v for y, v in sectors[d].items()} for d in sectors},
    "crs_total": {d: {str(y): v for y, v in crs_total[d].items()} for d in crs_total},
    "recipients": {d: {str(y): dict(sorted(v.items(), key=lambda kv: -kv[1])[:12])
                       for y, v in recipients[d].items()} for d in recipients},
    "sector_names": {k: SEC.get(k, k) for k in SECTOR_GROUPS},
    "channel_names": {k: CHN.get(k, k) for k in
                      sorted({c for d in channels for y in channels[d] for c in channels[d][y]})},
    "recipient_names": {c: REC.get(c, c) for d in recipients for y in recipients[d]
                        for c in recipients[d][y]},
}
# The timestamp means WHEN THESE FIGURES LAST CHANGED, not when the job last ran. A build
# stamp that moves on every run makes the file differ every month even when the OECD has
# published nothing, which would turn the scheduled job into a stream of empty commits and
# make a real change impossible to spot in the history.
if os.path.exists(OUT):
    try:
        prev = json.load(io.open(OUT, encoding="utf-8"))
        a, b = dict(prev), dict(doc)
        am, bm = dict(a.get("meta", {})), dict(b.get("meta", {}))
        am.pop("built", None); bm.pop("built", None)
        a["meta"], b["meta"] = am, bm
        if json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True):
            doc["meta"]["built"] = prev["meta"].get("built", doc["meta"]["built"])
            print("   figures unchanged since %s, keeping that date" % doc["meta"]["built"])
    except Exception:
        pass

io.open(OUT, "w", encoding="utf-8", newline="\n").write(
    # sort_keys because the equality test above sorts them. Without it, the same figures
    # returned in a different row order keep the old timestamp and STILL change the file,
    # which puts an order-only commit in the history every time the OECD shuffles a response.
    # allow_nan off because python writes NaN happily and no browser will read it back.
    json.dumps(doc, ensure_ascii=False, separators=(",", ":"),
               sort_keys=True, allow_nan=False))
print("\nwrote %s, %s bytes" % (OUT, "{:,}".format(os.path.getsize(OUT))))
print("reporting: %s" % ", ".join(reporting))
print("no observations: %s" % (", ".join(silent) or "none"))
for d in reporting:
    ly = max(ge[d]); cy = max(crs_total.get(d, {0: 0}))
    ngo = channels.get(d, {}).get(cy, {})
    tot = ngo.get("_T", 0) or 1
    print("   %-4s headline %d $%sm    %d delivered through NGOs %.1f%%"
          % (d, ly, ge[d][ly], cy, 100 * ngo.get("20000", 0) / tot))
