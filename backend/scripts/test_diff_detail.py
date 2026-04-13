"""Test: parse two different PDFs and inspect diff details and bbox quality."""
import sys, json
sys.path.insert(0, "/app")

from services.parser_service import parse_pdf
from services.diff_service import diff_paragraphs, diff_tables, merge_diff_results

# List all available uploads
import glob
old_pdfs = sorted(glob.glob("/app/runtime/uploads/old/*.pdf"))
new_pdfs = sorted(glob.glob("/app/runtime/uploads/new/*.pdf"))

print("=== Available uploads ===")
for p in old_pdfs:
    print(f"  OLD: {p}")
for p in new_pdfs:
    print(f"  NEW: {p}")

if not old_pdfs or not new_pdfs:
    print("Not enough files to test")
    sys.exit(1)

# Use the most recent pair
old_pdf = old_pdfs[-1]
new_pdf = new_pdfs[-1]
print(f"\nTesting: {old_pdf} vs {new_pdf}")

print("\nParsing old PDF...")
old_doc = parse_pdf(old_pdf)
print(f"  Engine: {old_doc.raw_json.get('engine')}, Pages: {old_doc.pages}, Paragraphs: {len(old_doc.paragraphs)}, Tables: {len(old_doc.tables)}")

print("Parsing new PDF...")
new_doc = parse_pdf(new_pdf)
print(f"  Engine: {new_doc.raw_json.get('engine')}, Pages: {new_doc.pages}, Paragraphs: {len(new_doc.paragraphs)}, Tables: {len(new_doc.tables)}")

# Run diff
text_diffs = diff_paragraphs(old_doc.paragraphs, new_doc.paragraphs)
table_diffs = diff_tables(old_doc.tables, new_doc.tables)
all_diffs = merge_diff_results(text_diffs, table_diffs, None)

print(f"\n=== Diff Results ===")
print(f"Text diffs: {len(text_diffs)}")
print(f"Table diffs: {len(table_diffs)}")
print(f"Total merged: {len(all_diffs)}")

# Show first 10 diffs with details
print(f"\n--- First 10 diffs ---")
for d in all_diffs[:10]:
    bbox = d.new_bbox or d.old_bbox
    bbox_str = f"page={bbox.page} ({bbox.x0:.1f},{bbox.y0:.1f},{bbox.x1:.1f},{bbox.y1:.1f})" if bbox else "NO BBOX"
    print(f"  [{d.id}] {d.diff_type.value} | {bbox_str}")
    print(f"    old: {(d.old_value or '(none)')[:80]}")
    print(f"    new: {(d.new_value or '(none)')[:80]}")
    print(f"    confidence: {d.confidence:.2f}")

# Analyze bbox distribution - check for overlapping/problematic bboxes
print(f"\n--- BBox Analysis ---")
page_bboxes = {}
for d in all_diffs:
    bbox = d.new_bbox or d.old_bbox
    if bbox:
        page_bboxes.setdefault(bbox.page, []).append((d.id, bbox))

for page, items in sorted(page_bboxes.items()):
    print(f"  Page {page}: {len(items)} diffs")
    for did, b in items[:5]:
        w = b.x1 - b.x0
        h = b.y1 - b.y0
        print(f"    {did}: x0={b.x0:.1f} y0={b.y0:.1f} x1={b.x1:.1f} y1={b.y1:.1f} (w={w:.1f} h={h:.1f})")

# Check for tiny/degenerate bboxes
tiny = [(d.id, d.new_bbox or d.old_bbox) for d in all_diffs 
        if (d.new_bbox or d.old_bbox) and 
        ((d.new_bbox or d.old_bbox).x1 - (d.new_bbox or d.old_bbox).x0) < 2]
print(f"\nTiny width bboxes (< 2pt): {len(tiny)}")
for did, b in tiny[:5]:
    print(f"  {did}: w={b.x1-b.x0:.1f} h={b.y1-b.y0:.1f}")

# Check for very large bboxes (likely table bboxes covering whole page)
large = [(d.id, d.new_bbox or d.old_bbox) for d in all_diffs 
         if (d.new_bbox or d.old_bbox) and 
         ((d.new_bbox or d.old_bbox).x1 - (d.new_bbox or d.old_bbox).x0) > 400]
print(f"Very large bboxes (> 400pt wide): {len(large)}")
for did, b in large[:5]:
    print(f"  {did}: w={b.x1-b.x0:.1f} h={b.y1-b.y0:.1f}")
