# -*- coding: utf-8 -*-
"""
Re-encode .bat files as UTF-8 with BOM so cmd.exe can handle Chinese characters
properly when chcp 65001 is used.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def read_utf8(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_utf8_bom(path, content):
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)

def main():
    # Read source content from .txt files
    start_content = read_utf8(os.path.join(SCRIPTS_DIR, 'start_content.txt'))
    stop_content = read_utf8(os.path.join(SCRIPTS_DIR, 'stop_content.txt'))

    # Find existing Chinese-named .bat files and overwrite them
    start_bat = None
    stop_bat = None
    for name in os.listdir(BASE_DIR):
        if name.endswith('.bat'):
            if '\u555f\u52d5' in name:  # 啟動
                start_bat = os.path.join(BASE_DIR, name)
            elif '\u505c\u6b62' in name:  # 停止
                stop_bat = os.path.join(BASE_DIR, name)

    if start_bat:
        write_utf8_bom(start_bat, start_content)
        print(f"OK: Re-encoded {os.path.basename(start_bat)} as UTF-8 with BOM")
    else:
        fallback = os.path.join(BASE_DIR, 'start_pdf_system.bat')
        write_utf8_bom(fallback, start_content)
        print(f"WARN: Chinese-named start bat not found, created {os.path.basename(fallback)}")

    if stop_bat:
        write_utf8_bom(stop_bat, stop_content)
        print(f"OK: Re-encoded {os.path.basename(stop_bat)} as UTF-8 with BOM")
    else:
        fallback = os.path.join(BASE_DIR, 'stop_pdf_system.bat')
        write_utf8_bom(fallback, stop_content)
        print(f"WARN: Chinese-named stop bat not found, created {os.path.basename(fallback)}")

    # Clean up ASCII-named duplicates if Chinese-named ones exist
    for ascii_name in ['start_pdf_system.bat', 'stop_pdf_system.bat']:
        ascii_path = os.path.join(BASE_DIR, ascii_name)
        if os.path.exists(ascii_path) and (start_bat or stop_bat):
            os.remove(ascii_path)
            print(f"Cleaned up duplicate: {ascii_name}")

if __name__ == '__main__':
    main()
