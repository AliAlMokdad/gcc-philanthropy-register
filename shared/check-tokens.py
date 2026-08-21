# Prove shared/tokens.css still says exactly what index.html says.
#
# WHY THIS IS NOT OPTIONAL. tokens.css is a transcription of the :root block in index.html, because
# index.html is too load-bearing to refactor for the sake of the smaller pages. A transcription is
# only as good as the thing that checks it, and without this script the comment at the top of
# tokens.css would be a hope rather than a fact. Run it after touching either file.
#
# It compares VALUES, not text, so a reordered line or a different comment is not a failure and a
# changed colour is. It also reports a property that exists in one file and not the other, in both
# directions, because a token quietly added to index.html is exactly how the two drift apart.
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.S)


def props(block):
    """Every custom property in a block, as a name to value map.

    Values are compared with their internal whitespace collapsed, so a line break inside a
    gradient is not reported as a difference."""
    out = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;}]+)", strip_comments(block)):
        out[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
    return out


def first_root(css):
    m = re.search(r":root\s*\{(.*?)\n\}", css, re.S)
    return m.group(1) if m else ""


def dark_root(css):
    m = re.search(r"@media\s*\(prefers-color-scheme\s*:\s*dark\s*\)\s*\{\s*:root\s*\{(.*?)\n\s*\}",
                  css, re.S)
    return m.group(1) if m else ""


index_css = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
shared_css = io.open(os.path.join(HERE, "tokens.css"), encoding="utf-8").read()

pairs = [
    ("light", props(first_root(index_css)), props(first_root(shared_css))),
    ("dark", props(dark_root(index_css)), props(dark_root(shared_css))),
]

problems = []
print("Comparing shared/tokens.css against the :root blocks in index.html")
print()
for label, origin, copy in pairs:
    missing = sorted(set(origin) - set(copy))
    extra = sorted(set(copy) - set(origin))
    changed = sorted(k for k in (set(origin) & set(copy)) if origin[k] != copy[k])
    print("  %-6s %3d properties in index.html, %3d in tokens.css" % (label, len(origin), len(copy)))
    for k in missing:
        problems.append("%s: %s is in index.html and not in tokens.css" % (label, k))
    for k in extra:
        problems.append("%s: %s is in tokens.css and not in index.html" % (label, k))
    for k in changed:
        problems.append("%s: %s differs\n        index.html : %s\n        tokens.css : %s"
                        % (label, k, origin[k], copy[k]))

print()
if problems:
    print("DRIFT, %d problem(s):" % len(problems))
    for p in problems:
        print("   " + p)
    sys.exit(1)

print("No drift. Every token matches, in both schemes.")

# and the thing the whole exercise was for: nothing may redeclare a canonical token elsewhere
print()
print("Checking no other stylesheet quietly redeclares a canonical token")
canonical = set(props(first_root(shared_css)))
offenders = []
for rel in ("members/style.css", "toolkit/index.html"):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        continue
    css = strip_comments(io.open(path, encoding="utf-8", errors="replace").read())
    # A DARK-SCHEME OVERRIDE IS NOT DRIFT. The first version of this check read every declaration
    # in the file and reported the toolkit's entire dark palette as divergence: --ink #EEF0F6 is a
    # pale ink for a dark ground, which is the system working, not breaking. Only declarations that
    # apply in the default scheme are comparable, so the dark blocks are cut out first.
    css = re.sub(r"@media[^{]*prefers-color-scheme\s*:\s*dark[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}",
                 " ", css, flags=re.S)
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;}]+)", css):
        name = m.group(1)
        if name in canonical:
            val = re.sub(r"\s+", " ", m.group(2)).strip()
            if val != props(first_root(shared_css))[name]:
                offenders.append((rel, name, val, props(first_root(shared_css))[name]))

if offenders:
    print("  These override a shared token with a different value:")
    for rel, name, got, want in offenders:
        print("     %-22s %-16s is %s, canonical is %s" % (rel, name, got, want))
    print()
    print("  That is allowed only if it is deliberate. If it is not, delete the local declaration.")
    sys.exit(2)

print("  None. Every page takes its tokens from the shared file.")
