import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

for tmpl in sorted(["1","2","3","4","5","r-6","r-7","r-8","r-9","r-10"]):
    idx = Path(f"templates/{tmpl}/index.html")
    if not idx.exists():
        print(f"{tmpl}: NO index.html")
        continue
    c = idx.read_text(encoding="utf-8", errors="replace")
    emails = [m for m in re.findall(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", c, re.I)
              if not any(x in m for x in ["google","gstatic","unsplash","w3.org","schema"])]
    title_m = re.search(r"<title[^>]*>(.*?)</title>", c, re.I)
    title = title_m.group(1)[:55] if title_m else "?"
    has_ph = "{{title}}" in c
    pages = len(list(Path(f"templates/{tmpl}").rglob("*.html")))
    print(f"{tmpl:6}  pages={pages:2d}  has_ph={has_ph}  emails={emails[:2]}")
    print(f"       title_tag={title!r}")
