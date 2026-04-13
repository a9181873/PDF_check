"""Test: parse the same PDF file twice and diff them to check for false positives."""
import sys
sys.path.insert(0, "/app")

from services.parser_service import parse_pdf
from services.diff_service import diff_paragraphs, diff_tables

# Find available PDF files
import glob
pdfs = glob.glob("/app/runtime/uploads/old/*.pdf") + glob.glob("/app/runtime/uploads/new/*.pdf")
if not pdfs:
    print("No PDF files found in uploads directory")
    sys.exit(1)

test_pdf = pdfs[0]
print(f"Testing with: {test_pdf}")

# Parse same file twice
print("Parsing first time...")
doc1 = parse_pdf(test_pdf)
print(f"  Engine: {doc1.raw_json.get('engine')}")
print(f"  Paragraphs: {len(doc1.paragraphs)}")
print(f"  Tables: {len(doc1.tables)}")

print("Parsing second time...")
doc2 = parse_pdf(test_pdf)
print(f"  Engine: {doc2.raw_json.get('engine')}")
print(f"  Paragraphs: {len(doc2.paragraphs)}")
print(f"  Tables: {len(doc2.tables)}")

# Check text consistency
text_mismatches = 0
for i, (p1, p2) in enumerate(zip(doc1.paragraphs, doc2.paragraphs)):
    if p1.text != p2.text:
        text_mismatches += 1
        if text_mismatches <= 5:
            print(f"  TEXT MISMATCH [{i}]: '{p1.text[:80]}' vs '{p2.text[:80]}'")

extra1 = len(doc1.paragraphs) - len(doc2.paragraphs)
print(f"Paragraph count difference: {extra1}")
print(f"Text mismatches (in overlapping range): {text_mismatches}")

# Check bbox consistency
bbox_mismatches = 0
for i, (p1, p2) in enumerate(zip(doc1.paragraphs, doc2.paragraphs)):
    b1, b2 = p1.bbox, p2.bbox
    if (b1.page != b2.page or abs(b1.x0 - b2.x0) > 0.01 or abs(b1.y0 - b2.y0) > 0.01
            or abs(b1.x1 - b2.x1) > 0.01 or abs(b1.y1 - b2.y1) > 0.01):
        bbox_mismatches += 1
        if bbox_mismatches <= 3:
            print(f"  BBOX MISMATCH [{i}]: page={b1.page} ({b1.x0:.1f},{b1.y0:.1f},{b1.x1:.1f},{b1.y1:.1f})"
                  f" vs page={b2.page} ({b2.x0:.1f},{b2.y0:.1f},{b2.x1:.1f},{b2.y1:.1f})")
print(f"BBox mismatches: {bbox_mismatches}")

# Run diff engine
print("\nRunning diff engine on identical docs...")
text_diffs = diff_paragraphs(doc1.paragraphs, doc2.paragraphs)
table_diffs = diff_tables(doc1.tables, doc2.tables)
print(f"Text diffs found: {len(text_diffs)}")
print(f"Table diffs found: {len(table_diffs)}")

for d in text_diffs[:5]:
    print(f"  [{d.diff_type.value}] old='{(d.old_value or '')[:60]}' new='{(d.new_value or '')[:60]}'")
for d in table_diffs[:5]:
    print(f"  [TABLE {d.diff_type.value}] old='{(d.old_value or '')[:60]}' new='{(d.new_value or '')[:60]}'")

# Show some sample paragraphs with their bboxes for overlay analysis
print("\n--- Sample paragraph bboxes (first 10) ---")
for i, p in enumerate(doc1.paragraphs[:10]):
    b = p.bbox
    print(f"  [{i}] page={b.page} x0={b.x0:.1f} y0={b.y0:.1f} x1={b.x1:.1f} y1={b.y1:.1f} text='{p.text[:50]}'")

# Check page dimensions
print(f"\n--- Page info ---")
print(f"  Pages: {doc1.pages}")
print(f"  Raw JSON keys: {list(doc1.raw_json.keys())}")
