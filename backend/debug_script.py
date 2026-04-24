import fitz
import sys
import os

def debug_pdf():
    upload_dir = "/app/runtime/uploads/old"
    pdfs = [f for f in os.listdir(upload_dir) if f.endswith(".pdf")]
    if not pdfs:
        print("No PDFs found")
        return
    
    pdf_path = os.path.join(upload_dir, pdfs[0])
    doc = fitz.open(pdf_path)
    page = doc[1]  # Page 2 (0-indexed)
    
    print(f"Page 2 rect: {page.rect}")
    words = page.get_text("words")
    print(f"Total words: {len(words)}")
    
    # Let's find the word '依子女人數計算'
    target = "依子女人數計算"
    for w in words:
        if target in w[4]:
            print(f"Found '{w[4]}' at {w[:4]}")
            break
            
if __name__ == "__main__":
    debug_pdf()
