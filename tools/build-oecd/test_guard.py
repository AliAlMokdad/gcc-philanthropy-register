# Feeds the guard deliberately corrupted builds and requires it to refuse each one.
#
#   python tools/build-oecd/test_guard.py
#
# Every mutation below is one that an earlier version of check_oecd.py accepted and would
# therefore have published. A guard nobody attacks is a guard nobody has tested.
import io, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LIVE = os.path.join(ROOT, "oecd.json")
CHECK = os.path.join(HERE, "check_oecd.py")
good = json.load(io.open(LIVE, encoding="utf-8"))


PREV = os.path.join(tempfile.gettempdir(), "oecd_prev_for_test.json")


def run():
    """The guard is given the previous file, exactly as the scheduled job gives it, because
    a uniform shift is invisible without history and that is the whole point of the check."""
    r = subprocess.run([sys.executable, CHECK, PREV], capture_output=True, text=True, cwd=ROOT)
    return r.returncode, (r.stdout + r.stderr).strip()


def mutate(name, fn, expect_reject=True):
    backup = LIVE + ".bak"
    shutil.copy(LIVE, backup)
    try:
        d = json.loads(json.dumps(good))
        out = fn(d)
        text = out if isinstance(out, str) else json.dumps(d, ensure_ascii=False,
                                                           separators=(",", ":"), sort_keys=True)
        io.open(LIVE, "w", encoding="utf-8", newline="\n").write(text)
        code, msg = run()
        rejected = code != 0
        ok = rejected == expect_reject
        first = [l.strip() for l in msg.splitlines() if l.strip().startswith(("the ", "SAU", "ARE",
                 "QAT", "KWT", "file", "no ", "oecd", "%d" % 0 if False else "zz"))]
        why = ""
        if rejected:
            lines = [l.strip() for l in msg.splitlines()[1:] if l.strip()]
            why = lines[0][:78] if lines else ""
        print("  %-4s %-46s %s" % ("PASS" if ok else "FAIL", name,
              ("refused: " + why) if rejected else "ACCEPTED"))
        return ok
    finally:
        shutil.move(backup, LIVE)


shutil.copy(LIVE, PREV)          # the known good file stands in for last month's
print("attacking the guard with builds that must never be published")
results = []

results.append(mutate("the file is unchanged and correct",
                      lambda d: None, expect_reject=False))
results.append(mutate("every headline figure doubled", lambda d: d["oda"].update(
    {c: {y: v * 2 for y, v in d["oda"][c].items()} for c in d["oda"]})))
results.append(mutate("headline figures in thousands, not millions", lambda d: d["oda"].update(
    {c: {y: v * 1000 for y, v in d["oda"][c].items()} for c in d["oda"]})))
results.append(mutate("the latest year of channel data is missing",
    lambda d: [d["channels"]["SAU"].pop(max(d["channels"]["SAU"], key=int))]))
results.append(mutate("half the channel rows lost",
    lambda d: [d["channels"]["SAU"][y].update({k: (0 if i % 2 else v)
        for i, (k, v) in enumerate(d["channels"]["SAU"][y].items()) if k != "_T"})
        for y in d["channels"]["SAU"]]))
results.append(mutate("a negative NGO share",
    lambda d: d["channels"]["QAT"][max(d["channels"]["QAT"], key=int)].update({"20000": -5.0})))
results.append(mutate("a CRS total removed",
    lambda d: d["crs_total"]["ARE"].pop(max(d["crs_total"]["ARE"], key=int))))
results.append(mutate("the measure quietly changed to net cash",
    lambda d: d["meta"]["queries"]["headline"].update({"measure": "1010", "flow": "1140"})))
results.append(mutate("NaN in a figure",
    lambda d: json.dumps(d, separators=(",", ":")).replace(
        '"' + max(d["oda"]["SAU"], key=int) + '":' + repr(d["oda"]["SAU"][max(d["oda"]["SAU"], key=int)]),
        '"' + max(d["oda"]["SAU"], key=int) + '":NaN', 1)))
results.append(mutate("a sector group that no longer sums to its total",
    lambda d: [d["sectors"]["SAU"][y].update({"100": d["sectors"]["SAU"][y].get("100", 0) + 900})
               for y in list(d["sectors"]["SAU"])[:1]]))
results.append(mutate("a recipient larger than the whole year",
    lambda d: d["recipients"]["KWT"][max(d["recipients"]["KWT"], key=int)].update(
        {"IRQ": d["crs_total"]["KWT"][max(d["crs_total"]["KWT"], key=int)] * 3})))
results.append(mutate("the channel names failed to load",
    lambda d: d.update({"channel_names": {}})))
results.append(mutate("a headline year in the future",
    lambda d: d["oda"]["QAT"].update({"2031": 900.0})))
results.append(mutate("units switched so a figure is absurd",
    lambda d: d["oda"]["SAU"].update({max(d["oda"]["SAU"], key=int): 95000.0})))

print("")
if all(results):
    print("all %d attacks handled" % len(results))
    sys.exit(0)
print("%d of %d NOT handled, the guard would publish corrupt data"
      % (results.count(False), len(results)))
sys.exit(1)
