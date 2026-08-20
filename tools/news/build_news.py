# Builds the public news feed.
#
# THE THREE LAYERS, and why they are three rather than one. A scheduled job rebuilds its
# output from upstream every run. If the public feed IS that output, then every manual
# correction, every removed false positive, every merged duplicate and every editorial
# exclusion is silently reverted on the next run, and the monitor behaves like an
# unreviewed aggregator no matter how disciplined the page looks.
#
#     provider responses
#       -> news-candidates.json     regenerated freely, never published
#       -> news-decisions.json      persistent, hand-editable, never overwritten here
#       -> news-feed.json           what the page reads, written atomically after the guard
#
# Publication decisions live in the middle file, keyed by the stable item id, so they
# survive every rebuild.
#
# Run:  python tools/news/build_news.py            (fetch live, write candidates + feed)
#       python tools/news/build_news.py --offline  (rebuild the feed from existing candidates)
#       python tools/news/build_news.py --dry      (fetch and report, write nothing)

import hashlib, io, json, os, sys, time
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import pipeline as P                                                    # noqa: E402
from registry import enabled_sources, source_by_id, SOURCES, REGISTRY_VERSION  # noqa: E402
from providers import fetch_source                                      # noqa: E402

CANDIDATES = os.path.join(ROOT, "news-candidates.json")
DECISIONS = os.path.join(ROOT, "news-decisions.json")
FEED = os.path.join(ROOT, "news-feed.json")
REGISTER = os.path.join(ROOT, "data.json")

SCHEMA_VERSION = 1
FEED_LIMIT = 240          # what the page is served. Older items stay in candidates.
STALE_HOURS = 12          # beyond this the page says so rather than implying freshness

# THE HORIZON. ReliefWeb's ?search= returns relevance-ranked results rather than
# date-ranked ones, so a query for "waqf" happily returns a 2023 report. Measured on the
# first real run: median item age 66 days and an oldest of 1,244. A development is news, so
# anything past this horizon is dropped from the published feed. It stays in
# news-candidates.json, where it is still searchable evidence, and the number dropped is
# printed on every run so the horizon can never quietly discard everything.
HORIZON_DAYS = 180


def jload(path, default=None):
    if not os.path.exists(path):
        return default
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def jwrite_atomic(path, obj):
    """Write to a sibling temp file and replace. A reader must never see half a feed, and
    a crashed run must never leave a truncated one behind."""
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def run_id():
    return "run-" + dt.datetime.now(P.UTC).strftime("%Y%m%dT%H%M%SZ")


# --------------------------------------------------------------------------- decisions
def default_decisions():
    return {
        "_comment": [
            "The persistent editorial layer. Hand-edited, and never overwritten by the",
            "build. Keys are the stable item id from news-candidates.json.",
            "",
            "Per item, any of:",
            "  status      published | hidden | rejected   (hidden and rejected never ship)",
            "  is_top      true pins the item to Top Developments regardless of score",
            "  priority    integer, lower sorts first among pinned items",
            "  title       a corrected headline, used instead of the provider's",
            "  description a corrected or human-written factual line",
            "  country     a corrected primary_gcc_country",
            "  topic       a corrected primary_topic",
            "  event_type  a corrected event type",
            "  drop_orgs   list of register_ids whose match was wrong",
            "  cluster_id  force this item into a cluster, to merge coverage by hand",
            "  note        an editor's note, shown to nobody, kept for the record",
            "",
            "Blocked domains and blocked ids apply to every future run."
        ],
        "blocked_domains": [],
        "blocked_ids": [],
        "items": {}
    }


def apply_decisions(items, dec):
    """Returns (kept, stats). Corrections are recorded on the item so the run report can
    say how many were applied, which is the only way to notice that the decisions file has
    silently stopped matching anything."""
    blocked_domains = {d.lower() for d in dec.get("blocked_domains") or []}
    blocked_ids = set(dec.get("blocked_ids") or [])
    per_item = dec.get("items") or {}
    stats = {"blocked_domain": 0, "blocked_id": 0, "hidden": 0, "corrected": 0,
             "pinned": 0, "unmatched_decisions": 0}
    out = []
    for it in items:
        if it["publisher_domain"] in blocked_domains:
            stats["blocked_domain"] += 1
            continue
        if it["id"] in blocked_ids:
            stats["blocked_id"] += 1
            continue
        d = per_item.get(it["id"])
        if d:
            applied = False
            st = d.get("status")
            if st in ("hidden", "rejected"):
                stats["hidden"] += 1
                continue
            if st:
                it["editorial"]["status"] = st
            for src, dst in (("title", "title"), ("description", "description"),
                             ("country", "primary_gcc_country"),
                             ("topic", "primary_topic"),
                             ("event_type", "event_type")):
                if d.get(src):
                    it[dst] = d[src]
                    applied = True
            if d.get("is_top"):
                it["editorial"]["is_top"] = True
                it["editorial"]["priority"] = d.get("priority")
                stats["pinned"] += 1
            if d.get("drop_orgs"):
                drop = set(d["drop_orgs"])
                it["organisations"] = [o for o in it["organisations"]
                                       if o.get("register_id") not in drop]
                applied = True
            if d.get("cluster_id"):
                it["cluster_id"] = d["cluster_id"]
                applied = True
            if d.get("note"):
                it["editorial"]["editor_note"] = d["note"]
            it["editorial"]["reviewed"] = True
            if applied:
                stats["corrected"] += 1
        out.append(it)
    ids = {i["id"] for i in items}
    stats["unmatched_decisions"] = len([k for k in per_item if k not in ids])
    return out, stats


# --------------------------------------------------------------------------- the run
def main(argv):
    offline = "--offline" in argv
    dry = "--dry" in argv
    rid = run_id()
    started = time.time()

    reg = jload(REGISTER)
    if not reg or "rows" not in reg or "keys" not in reg:
        print("FATAL: data.json is missing or malformed. The register is the matching source.")
        return 2
    index, skipped = P.build_register_index(reg)
    print("register: %d rows, %d names indexed for matching, %d skipped as too generic"
          % (len(reg["rows"]), len(index), skipped))

    statuses, raws = [], []
    if offline:
        cand = jload(CANDIDATES) or {}
        items = cand.get("items") or []
        print("offline: %d candidates read from news-candidates.json" % len(items))
        statuses = cand.get("provider_status") or []
    else:
        srcs = enabled_sources()
        print("fetching %d enabled sources (%d defined, %d disabled with a stated reason)"
              % (len(srcs), len(SOURCES), len(SOURCES) - len(srcs)))
        for s in srcs:
            got, st = fetch_source(s)
            raws.extend(got)
            statuses.extend(st)
            for x in st:
                print("  %-18s %-28s http=%-5s records=%-4s %s"
                      % (s["id"], (x.get("query") or "-")[:28], x.get("http"),
                         x.get("records"), x.get("error") or ""))

        # normalise
        items, rejects = [], {}
        for r in raws:
            it, why = P.normalise(r, index, source_by_id)
            if it is None:
                rejects[why] = rejects.get(why, 0) + 1
                continue
            it["provenance"]["ingestion_run_id"] = rid
            items.append(it)
        print("\nnormalised: %d admitted of %d raw candidates" % (len(items), len(raws)))
        print("rejected, by reason:")
        for why, n in sorted(rejects.items(), key=lambda kv: -kv[1])[:14]:
            print("  %-4d %s" % (n, why))

    # THE HORIZON IS A FLAG HERE, NOT A DELETION. Marked before deduplication so that a
    # fresh item is never dropped as the duplicate of one that will not be published, and
    # kept in the candidates file either way, because that file is the record of what the run
    # actually saw. Only the feed is pruned.
    cutoff = dt.datetime.now(P.UTC) - dt.timedelta(days=HORIZON_DAYS)
    stale_n = 0
    for it in items:
        t = P.parse_iso(it.get("published_at"))
        it["beyond_horizon"] = bool(t and t < cutoff)
        if it["beyond_horizon"]:
            stale_n += 1
    # deduplication prefers a publishable item over one that is past the horizon, so the
    # survivor of a pair is the one that can actually ship
    items.sort(key=lambda x: (x.get("beyond_horizon", False),))
    print("horizon: %d of %d items are older than %d days. They stay in candidates and are "
          "not published." % (stale_n, len(items), HORIZON_DAYS))

    # deduplicate and cluster
    kept, dropped, notes = P.deduplicate(items)
    print("\ndeduplication: %s" % "; ".join(notes))

    # the persistent editorial layer
    dec = jload(DECISIONS)
    if dec is None:
        dec = default_decisions()
        if not dry:
            jwrite_atomic(DECISIONS, dec)
            print("created news-decisions.json (empty, hand-editable)")
    kept, dstats = apply_decisions(kept, dec)
    print("decisions applied: %s" % ", ".join("%s=%s" % kv for kv in dstats.items()))
    if dstats["unmatched_decisions"]:
        print("  NOTE: %d decisions reference ids not in this run. Expected as items age "
              "out; investigate if it grows." % dstats["unmatched_decisions"])

    # rank
    now = dt.datetime.now(P.UTC)
    top = P.pick_top([i for i in kept if not i.get("beyond_horizon")], now)
    rank = {t["id"]: n + 1 for n, t in enumerate(top)}
    for it in kept:
        it["is_top"] = it["id"] in rank
        it["editorial"]["is_top"] = it["id"] in rank
        # the ORDER, carried explicitly. The page must not re-derive the ranking from the
        # feed's date sort, which is what made the newest top item the lead.
        it["editorial"]["top_rank"] = rank.get(it["id"])

    kept.sort(key=lambda x: (x["published_at"] or "", x["id"]), reverse=True)

    # candidates: everything, with the working fields, for debugging and for the decisions
    # file to be written against
    if not dry and not offline:
        jwrite_atomic(CANDIDATES, {
            "schema_version": SCHEMA_VERSION, "generated_at": P.now_iso(),
            "ingestion_run_id": rid, "registry_version": REGISTRY_VERSION,
            "provider_status": statuses,
            "items": [strip_working(dict(i), keep_debug=True) for i in kept],
        })

    # the public feed: inside the horizon, trimmed, with the working fields removed
    publishable = [i for i in kept if not i.get("beyond_horizon")]
    feed_items = [strip_working(dict(i)) for i in publishable[:FEED_LIMIT]]
    counts = {}
    for i in feed_items:
        counts[i["discovered_via"]] = counts.get(i["discovered_via"], 0) + 1
    publishers = sorted({i["publisher"] for i in feed_items})
    # THE FRESHNESS TIMESTAMP IS WHEN A SOURCE WAS LAST CONTACTED, not when this script ran.
    # --offline reads candidates from disk and previously stamped feed_updated_at = now, which
    # cleared the stale notice and told readers the feed had just refreshed when nothing had
    # been fetched at all.
    if offline:
        cand_meta = jload(CANDIDATES) or {}
        contacted = cand_meta.get("generated_at") or (jload(FEED) or {}).get("feed_updated_at")
        if not contacted:
            print("FATAL: --offline cannot establish when a source was last contacted, so it "
                  "cannot honestly stamp the feed.")
            return 4
        print("offline: feed_updated_at stays at %s, when the sources were last contacted"
              % contacted)
    else:
        contacted = P.now_iso()

    feed = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": P.now_iso(),
        "feed_updated_at": contacted,
        "ingestion_run_id": rid,
        "registry_version": REGISTRY_VERSION,
        "stale_after_hours": STALE_HOURS,
        "horizon_days": HORIZON_DAYS,
        "coverage": {
            "items": len(feed_items),
            "publishers": len(publishers),
            "sources_enabled": len([s for s in SOURCES if s.get("enabled")]),
            "sources_defined": len(SOURCES),
            "by_discovery": counts,
            "register_names_indexed": len(index),
        },
        "provider_status": [{k: v for k, v in s.items() if k != "url"} for s in statuses],
        "items": feed_items,
    }

    # THE PUBLICATION GUARD. A scheduled job that can replace a good feed with an empty one
    # is worse than a job that sometimes does nothing.
    prev = jload(FEED) or {}
    prev_n = len(prev.get("items") or [])
    ok_sources = len([s for s in statuses if s.get("ok") and s.get("records")])
    refuse = None
    if not offline and ok_sources == 0:
        refuse = ("no provider returned a usable record. Publishing now would replace a "
                  "feed of %d items with nothing." % prev_n)
    elif prev_n >= 10 and len(feed_items) < prev_n * 0.5:
        refuse = ("the item count collapsed from %d to %d, which is more likely an outage "
                  "than the news. Publishing is refused; the previous feed stands."
                  % (prev_n, len(feed_items)))
    elif not feed_items and prev_n:
        refuse = "this build has no publishable items and the previous feed has %d." % prev_n

    if refuse:
        print("\nREFUSED TO PUBLISH: " + refuse)
        print("news-candidates.json was still written, so the run can be inspected.")
        return 3

    if dry:
        print("\n--dry: nothing written. %d items would ship, %d top developments."
              % (len(feed_items), len(top)))
    else:
        jwrite_atomic(FEED, feed)
        print("\nwrote news-feed.json: %d items, %d publishers, %d top developments, %d bytes"
              % (len(feed_items), len(publishers), len(top), os.path.getsize(FEED)))

    print("\nTOP DEVELOPMENTS chosen (score is internal and never rendered):")
    for t in top:
        print("  %5.1f  %-22s %-26s %s" % (t["_score"], t["primary_gcc_country"][:22],
                                           t["primary_topic"][:26], t["title"][:70]))
    if len(top) < 4:
        print("  (%d of 4 slots filled. Weak positions are left empty by design.)" % len(top))
    print("\nrun %s finished in %.1fs" % (rid, time.time() - started))
    return 0


WORKING = ("_title_key", "_title_letters", "_periodic", "_dupes", "_also", "_sig",
           "_score", "_score_parts", "is_top")


def strip_working(it, keep_debug=False):
    if keep_debug:
        it["_also"] = sorted(it.get("_also") or [])
        it.pop("_sig", None)
        return it
    for k in WORKING:
        it.pop(k, None)
    return it


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
