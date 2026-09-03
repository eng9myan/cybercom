import zipfile
import xml.etree.ElementTree as ET

path = r'C:\Users\User\Downloads\Hakeem System Gap Analysis.docx'
with zipfile.ZipFile(path, 'r') as z:
    root = ET.fromstring(z.read('word/document.xml'))
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    texts = []
    for t in root.iter('{%s}t' % ns):
        texts.append(t.text or '')
    full_text = ''.join(texts)
    print(full_text)
    with open(r'D:\cybercom\cymed\Cymed\gap_analysis.txt', 'w', encoding='utf-8') as out:
        out.write(full_text)
