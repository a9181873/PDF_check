"""Test: copy same PDF to two paths and parse both - simulates real upload scenario."""
import shutil, sys
sys.path.insert(0, "/app")

from services.parser_service import parse_pdf
from services.diff_service import diff_paragraphs, diff_tables, merge_diff_results

# Copy same file to two different paths
src = "/tmp/test_old.pdf"
path_a = "/tmp/upload_a.pdf"
path_b = "/tmp/upload_b.pdf"
shutil.copy2(src, path_a)
shutil.copy2(src, path_b)

print("Parsing path A...")
doc_a = parse_pdf(path_a)
print(f"  Engine={doc_a.raw_json.get('engine')}, Paragraphs={len(doc_a.paragraphs)}, Tables={len(doc_a.tables)}")

print("Parsing path B...")
doc_b = parse_pdf(path_b)
print(f"  Engine={doc_b.raw_json.get('engine')}, Paragraphs={len(doc_b.paragraphs)}, Tables={len(doc_b.tables)}")

# Check paragraph-level consistency
para_text_mismatches = 0
for i in range(min(len(doc_a.paragraphs), len(doc_b.paragraphs))):
    if doc_a.paragraphs[i].text != doc_b.paragraphs[i].text:
        para_text_mismatches += 1
        if para_text_mismatches <= 5:
            print(f"  PARAGRAPH TEXT MISMATCH [{i}]:")
            print(f"    A: '{doc_a.paragraphs[i].text[:80]}'")
            print(f"    B: '{doc_b.paragraphs[i].text[:80]}'")
print(f"Paragraph count: {len(doc_a.paragraphs)} vs {len(doc_b.paragraphs)}")
print(f"Paragraph text mismatches: {para_text_mismatches}")

# Check table-level consistency
for i in range(min(len(doc_a.tables), len(doc_b.tables))):
    ta = doc_a.tables[i]
    tb = doc_b.tables[i]
    cols_a = [str(c) for c in ta.dataframe.columns]
    cols_b = [str(c) for c in tb.dataframe.columns]
    if cols_a != cols_b:
        print(f"  TABLE {i} COLUMN MISMATCH:")
        print(f"    A cols: {cols_a[:8]}")
        print(f"    B cols: {cols_b[:8]}")
    if ta.dataframe.shape != tb.dataframe.shape:
        print(f"  TABLE {i} SHAPE MISMATCH: {ta.dataframe.shape} vs {tb.dataframe.shape}")
    elif not ta.dataframe.empty:
        for r in range(ta.dataframe.shape[0]):
            for c in range(ta.dataframe.shape[1]):
                va = str(ta.dataframe.iloc[r, c]).strip()
                vb = str(tb.dataframe.iloc[r, c]).strip()
                if va != vb:
                    print(f"  TABLE {i} CELL MISMATCH [{r},{c}]: '{va[:50]}' vs '{vb[:50]}'")

# Run full diff
text_diffs = diff_paragraphs(doc_a.paragraphs, doc_b.paragraphs)
table_diffs = diff_tables(doc_a.tables, doc_b.tables)
all_diffs = merge_diff_results(text_diffs, table_diffs, None)
print(f"\nDiff results: text={len(text_diffs)}, table={len(table_diffs)}, total={len(all_diffs)}")

for d in all_diffs[:10]:
    print(f"  [{d.id}] {d.diff_type.value}: old='{(d.old_value or '')[:60]}' new='{(d.new_value or '')[:60]}'")
    print(f"    context: {d.context}")
