"""Test: parse identical PDFs and sample PDFs to diagnose false positives and bbox issues."""
import sys
sys.path.insert(0, "/app")

from services.parser_service import parse_pdf
from services.diff_service import diff_paragraphs, diff_tables, merge_diff_results

# TEST 1: Parse same file as both old and new (simulate user uploading identical files)
print("=" * 60)
print("TEST 1: Identical file as old and new")
print("=" * 60)
test_file = "/tmp/test_old.pdf"
doc_a = parse_pdf(test_file)
doc_b = parse_pdf(test_file)
print(f"Paragraphs: {len(doc_a.paragraphs)} vs {len(doc_b.paragraphs)}")
print(f"Tables: {len(doc_a.tables)} vs {len(doc_b.tables)}")

text_diffs = diff_paragraphs(doc_a.paragraphs, doc_b.paragraphs)
table_diffs = diff_tables(doc_a.tables, doc_b.tables)
all_diffs = merge_diff_results(text_diffs, table_diffs, None)
print(f"Text diffs: {len(text_diffs)}, Table diffs: {len(table_diffs)}, Total: {len(all_diffs)}")

if table_diffs:
    print("TABLE DIFFS (false positives with identical files):")
    for d in table_diffs[:10]:
        print(f"  [{d.diff_type.value}] old='{(d.old_value or '')[:70]}' new='{(d.new_value or '')[:70]}'")
        print(f"    context: {d.context}")

# Check table content
print("\nTable details:")
for i, t in enumerate(doc_a.tables):
    df = t.dataframe
    print(f"  Table {i}: shape={df.shape}, cols={list(df.columns)[:5]}")
    if not df.empty:
        print(f"    First row: {df.iloc[0].tolist()[:5]}")

# TEST 2: Parse two different sample files
print("\n" + "=" * 60)
print("TEST 2: Different files (test_old vs test_new)")
print("=" * 60)
doc_old = parse_pdf("/tmp/test_old.pdf")
doc_new = parse_pdf("/tmp/test_new.pdf")
print(f"Old: pages={doc_old.pages}, paragraphs={len(doc_old.paragraphs)}, tables={len(doc_old.tables)}")
print(f"New: pages={doc_new.pages}, paragraphs={len(doc_new.paragraphs)}, tables={len(doc_new.tables)}")

text_diffs2 = diff_paragraphs(doc_old.paragraphs, doc_new.paragraphs)
table_diffs2 = diff_tables(doc_old.tables, doc_new.tables)
all_diffs2 = merge_diff_results(text_diffs2, table_diffs2, None)
print(f"Text diffs: {len(text_diffs2)}, Table diffs: {len(table_diffs2)}, Total: {len(all_diffs2)}")

# Show some diffs
print("\nFirst 15 diffs:")
for d in all_diffs2[:15]:
    bbox = d.new_bbox or d.old_bbox
    if bbox:
        w = bbox.x1 - bbox.x0
        h = bbox.y1 - bbox.y0
        bstr = f"pg{bbox.page} ({bbox.x0:.0f},{bbox.y0:.0f},{bbox.x1:.0f},{bbox.y1:.0f}) w={w:.0f} h={h:.0f}"
    else:
        bstr = "NO BBOX"
    print(f"  [{d.id}] {d.diff_type.value:15s} conf={d.confidence:.2f} {bstr}")
    if d.old_value:
        print(f"    OLD: {d.old_value[:80]}")
    if d.new_value:
        print(f"    NEW: {d.new_value[:80]}")

# Analyze bbox overlap issues
print("\n--- Overlap Analysis ---")
for page_num in range(1, max(doc_old.pages, doc_new.pages) + 1):
    page_items = [d for d in all_diffs2 if (d.new_bbox or d.old_bbox) and (d.new_bbox or d.old_bbox).page == page_num]
    if not page_items:
        continue
    overlaps = 0
    for i, a in enumerate(page_items):
        for b in page_items[i+1:]:
            ba = a.new_bbox or a.old_bbox
            bb = b.new_bbox or b.old_bbox
            if ba and bb:
                if ba.x0 < bb.x1 and ba.x1 > bb.x0 and ba.y0 < bb.y1 and ba.y1 > bb.y0:
                    overlaps += 1
    print(f"  Page {page_num}: {len(page_items)} diffs, {overlaps} overlapping pairs")
