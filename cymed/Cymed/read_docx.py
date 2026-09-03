import zipfile
import xml.etree.ElementTree as ET
import sys

z = zipfile.ZipFile(sys.argv[1], 'rb')
r = ET.fromstring(z.read('word/document.xml'))
t = [x.text or '' for x in r.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')]
print(''.join(t))
