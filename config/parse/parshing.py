import re

def remove_bold_and_header(text: str) -> str:
    # Hilangkan header markdown
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    # Hilangkan **bold** dan *italic* (markdown style)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text

# Contoh penggunaan (untuk pengujian manual):
if __name__ == "__main__":
    with open("output.txt", encoding="utf-8") as f:
        teks = f.read()
    hasil = remove_bold_and_header(teks)
    print(hasil)
