"""Pull the latest POSTED patch notes into index.html.

Reads Documents/Patch Notes, keeps patches up to the "Last posted:" number in READ ME.txt
(newer files are unposted drafts), drops the Discord ping footer, and embeds the newest
ones as JSON between the PATCHNOTES markers. Run it, then republish the page.
"""
import json, re, sys
from pathlib import Path

NOTES = Path.home() / "Documents" / "Patch Notes"
PAGE = Path(__file__).with_name("index.html")
KEEP = 6

def ver(s):
    return tuple(int(n) for n in s.split("."))

readme = (NOTES / "READ ME.txt").read_text(encoding="utf-8")
posted = ver(re.search(r"Last posted:\s*([\d.]+)", readme).group(1))

patches = []
for f in NOTES.glob("Patch *.txt"):
    m = re.fullmatch(r"Patch ([\d.]+)\.txt", f.name)
    if not m or ver(m.group(1)) > posted:
        continue
    text = f.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    text = re.sub(r"(?m)^-#\s*\|\|@.*\|\|\s*$", "", text).strip()
    patches.append({"v": m.group(1), "md": text})

patches.sort(key=lambda p: ver(p["v"]), reverse=True)
# keep whole releases: the newest KEEP large patches (x.xx) plus all their minors (x.xx.x)
groups = []
for p in patches:
    g = ".".join(p["v"].split(".")[:2])
    if g not in groups:
        groups.append(g)
keep = set(groups[:KEEP])
patches = [p for p in patches if ".".join(p["v"].split(".")[:2]) in keep]

blob = json.dumps(patches, ensure_ascii=False).replace("<", "\\u003c")
block = '<!-- PATCHNOTES:START -->\n<script type="application/json" id="patch-data">' + blob + "</script>\n<!-- PATCHNOTES:END -->"

page = PAGE.read_text(encoding="utf-8")
new, n = re.subn(r"<!-- PATCHNOTES:START -->.*?<!-- PATCHNOTES:END -->", lambda _: block, page, flags=re.S)
if n != 1:
    sys.exit("PATCHNOTES markers not found in index.html")
PAGE.write_text(new, encoding="utf-8")
print("Embedded", ", ".join(p["v"] for p in patches))
