# -*- coding: utf-8 -*-
import os

base = r"c:\Users\JY\Desktop\PDF_check_windows_migration_20260412"
for name in os.listdir(base):
    if name.endswith(".bat"):
        path = os.path.join(base, name)
        with open(path, "rb") as f:
            raw = f.read()
        has_bom = raw[:3] == b"\xef\xbb\xbf"
        size = len(raw)
        # Try to decode as utf-8 to verify
        try:
            text = raw.decode("utf-8-sig")
            valid_utf8 = True
            # Check first few meaningful lines
            lines = [l for l in text.split("\n") if l.strip()][:5]
        except:
            valid_utf8 = False
            lines = []
        print(f"File: {name}")
        print(f"  BOM: {has_bom}, Size: {size}, Valid UTF-8: {valid_utf8}")
        for l in lines:
            print(f"  | {l.rstrip()}")
        print()
