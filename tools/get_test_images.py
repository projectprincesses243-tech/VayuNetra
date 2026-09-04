"""
Fetch a few public test images containing people, so the detector has
positive cases to find. These stand in for aerial survivor imagery until
the project dataset is available.
"""

import urllib.request
from pathlib import Path

# Public sample images used in computer-vision documentation and demos
SOURCES = {
    "people_01.jpg": "https://ultralytics.com/images/bus.jpg",
    "people_02.jpg": "https://ultralytics.com/images/zidane.jpg",
}

out = Path("perception/samples")
out.mkdir(parents=True, exist_ok=True)

for name, url in SOURCES.items():
    dest = out / name
    if dest.exists():
        print(f"  already have {name}")
        continue
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  downloaded {name}")
    except Exception as e:
        print(f"  FAILED {name}: {e}")

print(f"\nsaved to {out.resolve()}")