# Refuses to let a rebuilt oecd.json be published unless it still makes sense.
#
#   python tools/build-oecd/check_oecd.py [previous_oecd.json]
#
# The monthly job runs with nobody watching, so this is the only thing standing between a bad
# API response and a public page. An earlier version of this file was adversarially tested by
# feeding it deliberately corrupted builds, and it PASSED eight of them: doubled headline
# figures, a missing latest year of channel data, channel parts halved, a negative NGO share,
# missing totals, altered measure metadata, and NaN, which is not even valid JSON. Every check
# below exists because one of those got through.
#
# Exits non-zero and says why, which stops the workflow before anything is committed.
import io, json, math, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "oecd.json")
PREV = sys.argv[1] if len(sys.argv) > 1 else None
fail = []
warn = []


def bad(m): fail.append(m)
def note(m): warn.append(m)


# ---------------------------------------------------------------- it must be valid JSON
if not os.path.exists(PATH):
    sys.exit("oecd.json is missing")
raw = io.open(PATH, encoding="utf-8").read()
size = len(raw.encode("utf-8"))
if size < 4000 or size > 400000:
    bad("file is %d bytes, outside anything this file has ever been" % size)
# NaN and Infinity are accepted by python and REJECTED by every browser, so a build that
# produced them would fail silently in the reader's browser and nowhere else
try:
    d = json.loads(raw, parse_constant=lambda c: (_ for _ in ()).throw(
        ValueError("the file contains " + c + ", which no browser will parse")))
except ValueError as e:
    sys.exit("oecd.json is not valid JSON for a browser: %s" % e)

REQUIRED = ("meta", "names", "oda", "oda_net", "sectors", "channels", "recipients",
            "crs_total", "sector_names", "channel_names", "recipient_names")
for k in REQUIRED:
    if k not in d:
        sys.exit("oecd.json has no %s, the shape changed" % k)

meta = d["meta"]
rep = meta.get("reporting", [])
if not rep:
    sys.exit("no reporting states at all")
if sorted(rep) != ["ARE", "KWT", "QAT", "SAU"]:
    bad("the set of reporting states changed to %s, which a person should see first" % rep)

# ---------------------------------------------------------------- the metadata must be true
q = meta.get("queries", {})
if q.get("headline", {}).get("measure") != "11010" or q.get("headline", {}).get("flow") != "1160":
    bad("the headline is no longer the grant equivalent measure 11010 flow 1160, which is the "
        "one the page says it is showing")
if q.get("composition", {}).get("measure") != "100" or q.get("composition", {}).get("flow") != "D":
    bad("the composition is no longer gross disbursements, measure 100 flow D")
for k in ("headline", "composition"):
    if q.get(k, {}).get("unit") != "USD":
        bad("%s is not in USD any more" % k)
if not str(meta.get("built", "")).startswith("20"):
    bad("the built timestamp is missing or malformed")

# ---------------------------------------------------------------- every number is a number
now = time.gmtime().tm_year


def numbers(obj, path):
    if isinstance(obj, dict):
        for k, v in obj.items():
            numbers(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            numbers(v, path + "[%d]" % i)
    elif isinstance(obj, bool):
        bad("%s is a boolean where a number belongs" % path)
    elif isinstance(obj, (int, float)):
        if math.isnan(obj) or math.isinf(obj):
            bad("%s is not a finite number" % path)
        elif obj < 0:
            # aid figures are never negative in these series, and a negative share is
            # meaningless. A sign flip would otherwise draw a bar backwards.
            bad("%s is negative, %s" % (path, obj))


for k in ("oda", "oda_net", "sectors", "channels", "recipients", "crs_total"):
    numbers(d[k], k)

# ---------------------------------------------------------------- the headline series
for c in rep:
    ys = [int(y) for y in d["oda"].get(c, {})]
    if not ys:
        bad("%s has no headline series" % c); continue
    if max(ys) > now:
        bad("%s reports %d, which is in the future" % (c, max(ys)))
    if max(ys) < now - 3:
        bad("%s stops at %d, too stale to publish unseen" % (c, max(ys)))
    for y, v in d["oda"][c].items():
        if v > 60000:
            # in USD millions. A units change to thousands or units shows up here first.
            bad("%s %s is %s, outside any plausible range in USD millions" % (c, y, v))

# ---------------------------------------------------------------- the composition
for c in rep:
    ch, ct = d["channels"].get(c, {}), d["crs_total"].get(c, {})
    if not ch or not ct:
        bad("%s has no composition data at all" % c); continue
    latest = max(int(y) for y in ct)
    if str(latest) not in ch:
        # the cards read the latest channel year; if it is missing the page silently drops
        # the one number this panel exists to show
        bad("%s has no channel data for its latest composition year %d" % (c, latest))
    for y, split in ch.items():
        t = split.get("_T")
        if not t:
            bad("%s %s channel split has no total" % (c, y)); continue
        parts = sum(v for k, v in split.items() if k != "_T")
        r = parts / t
        # BOTH directions. The earlier version only caught over-counting, so a split that had
        # lost half its rows passed as though the money had simply gone somewhere unnamed.
        if r > 1.02:
            bad("%s %s channel parts are %.0f%% of the total" % (c, y, r * 100))
        if r < 0.9:
            bad("%s %s channel parts are only %.0f%% of the total, rows are missing"
                % (c, y, r * 100))

for c in d["sectors"]:
    for y, groups in d["sectors"][c].items():
        whole = d["crs_total"].get(c, {}).get(y)
        if whole is None:
            bad("%s %s has sector groups but no total to check them against" % (c, y)); continue
        if not whole:
            continue
        parts = sum(groups.values())
        if abs(parts - whole) / whole > 0.02:
            # this is the check that catches a dimension that stopped being pinned, which
            # multiplies every figure and looks entirely plausible on the page
            bad("%s %s sector parts %.1f do not sum to the total %.1f" % (c, y, parts, whole))

for c in d["recipients"]:
    for y, r in d["recipients"][c].items():
        t = d["crs_total"].get(c, {}).get(y)
        if t is None:
            bad("%s %s has recipients but no total, so every share would be wrong" % (c, y))
        elif t and r and max(r.values()) > t * 1.02:
            bad("%s %s has a recipient larger than that year's total" % (c, y))

# ---------------------------------------------------------------- names, or the page prints codes
if not d["channel_names"].get("20000"):
    bad("the channel names did not load, so the page would print bare codes")
if not d["sector_names"].get("700"):
    bad("the sector names did not load")
missing = [c for cc in d["recipients"].values() for yy in cc.values() for c in yy
           if c not in d["recipient_names"]]
if missing:
    bad("%d recipient codes have no name" % len(set(missing)))

# ---------------------------------------------------------------- against the previous file
# THE ONLY THING THAT CATCHES A UNIFORM SHIFT. Every figure doubled is individually plausible:
# it stays inside the range, the parts still sum, the shares are unchanged. Nothing inside a
# single file contradicts it. Against last month's file it is obvious, and a whole series
# moving at once is the signature of a changed measure or unit rather than of news.
if PREV and os.path.exists(PREV):
    try:
        p = json.load(io.open(PREV, encoding="utf-8"))
        moved, compared, worst = 0, 0, ""
        for c in rep:
            for y, v in d["oda"].get(c, {}).items():
                o = p.get("oda", {}).get(c, {}).get(y)
                if not o or not v:
                    continue
                compared += 1
                ch = abs(v - o) / o
                if ch > 0.5:
                    moved += 1
                    if not worst:
                        worst = "%s %s went from %s to %s" % (c, y, o, v)
        if compared and moved:
            share = moved / compared
            # a genuine revision touches a year or two. Half the series moving is a defect.
            if share >= 0.35:
                bad("%d of %d headline figures already published moved by more than half, "
                    "for example %s. A whole series moving at once is a changed measure or "
                    "unit, not news." % (moved, compared, worst))
            else:
                note("%d of %d headline figures moved by more than half, for example %s"
                     % (moved, compared, worst))
    except Exception as e:
        note("could not compare with the previous file: %s" % e)
elif PREV:
    note("no previous file at %s to compare against" % PREV)

for w in warn:
    print("   note: " + w)
if fail:
    print("REFUSING the rebuilt oecd.json:")
    for f in fail:
        print("   " + f)
    sys.exit(1)
print("oecd.json passes: %d states, headline to %s, %d bytes"
      % (len(rep), max(max(int(y) for y in d["oda"][c]) for c in rep), size))
