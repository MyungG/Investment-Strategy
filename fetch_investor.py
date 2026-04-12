# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

from kis_api import get_investor_realtime

data = get_investor_realtime(top=20)
with open("investor_cache.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("investor_cache.json saved:", data.get("saved_at", ""))
