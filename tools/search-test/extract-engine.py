# Slices the search engine out of index.html into engine.gen.js so the test runs the code
# that actually ships, not a copy of it. Regenerate after any edit to the search functions.
#
#   "C:\Users\Ali Al Mokdad\AppData\Local\Python\bin\python.exe" tools/search-test/extract-engine.py
#
# The interpreter is not on PATH.
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
INDEX = os.path.join(ROOT, "index.html")
if not os.path.exists(INDEX):
    ROOT = os.path.dirname(HERE)
    ROOT = os.path.dirname(ROOT)
    INDEX = os.path.join(ROOT, "index.html")
html = io.open(INDEX, encoding="utf-8").read()


def block(start_sig, end_sig):
    i = html.index(start_sig)
    j = html.index(end_sig, i) + len(end_sig)
    return html[i:j]


NORM_END = ('return txt(s).toLowerCase().replace(/[^\\p{L}\\p{N}]+/gu," ")'
            '.replace(/\\s+/g," ").trim();\n}')
ENGINE_END = ("function matchRow(r,q){\n  if(!q) return true;\n  var P=plan(q);\n"
              "  return P ? !!scoreRow(r,P) : true;\n}")

normsrc = block("function norm(s){", NORM_END)
eng = block("/* ============================ SEARCH ENGINE", ENGINE_END)

prelude = """/* GENERATED FILE. The search engine sliced verbatim out of index.html so a test cannot
   drift from what ships. Do not edit; regenerate with extract-engine.py. */
var ROWS=[], NORM=null;
function txt(s){ return s==null ? "" : String(s); }
"""
tail = """
module.exports={ setCorpus:function(rows,normMap){ ROWS=rows; NORM=normMap; buildDF(); },
  norm:norm, plan:plan, scoreRow:scoreRow, stems:stems, hit:hit, matchRow:matchRow,
  CONCEPTS:CONCEPTS, BROADENS:BROADENS };
"""
out = prelude + normsrc + "\n\n" + eng + "\n" + tail
dest = os.path.join(HERE, "engine.gen.js")
io.open(dest, "w", encoding="utf-8", newline="").write(out)
sys.stdout.write("wrote %s, %d chars\n" % (os.path.basename(dest), len(out)))
