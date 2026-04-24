import fitz
import sys

def test_extract(pdf_path, page_no):
    doc = fitz.open(pdf_path)
    page = doc[page_no]
    words = page.get_text("words")
    print(f"Total words on page {page_no}: {len(words)}")
    for i, w in enumerate(words[:10]):
        print(f"Word {i}: {w[:4]} '{w[4]}'")

if __name__ == "__main__":
    import os
    # Find a PDF in the uploads folder
    upload_dir = r"c:\Users\JY\Desktop\PDF_check_windows_migration_20260417\backend\runtime\uploads\old"
    pdfs = [f for f in os.listdir(upload_dir) if f.endswith(".pdf")]
    if pdfs:
        test_extract(os.path.join(upload_dir, pdfs[0]), 1)
    else:
        print("No PDFs found")
