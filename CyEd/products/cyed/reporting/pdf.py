"""
Minimal, dependency-free PDF canvas — enough to lay out a proper report card
(bordered tables, a school logo, headings) without a heavy PDF library.
Supports text (Helvetica / Helvetica-Bold), lines, filled/stroked rectangles,
and embedded baseline JPEG images.

Coordinate system is PDF-native (origin bottom-left, points; A4 = 595×842).
"""

PAGE_W, PAGE_H = 595, 842


def _esc(text) -> str:
    return str(text).replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def jpeg_info(data: bytes):
    """Return (width, height, components) for a baseline JPEG, or None."""
    if not data or data[:2] != b"\xff\xd8":
        return None
    i = 2
    n = len(data)
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while i + 9 < n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in sof:
            h = (data[i + 5] << 8) | data[i + 6]
            w = (data[i + 7] << 8) | data[i + 8]
            comp = data[i + 9]
            return w, h, comp
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg = (data[i + 2] << 8) | data[i + 3]
        i += 2 + seg
    return None


def wrap(text: str, width_chars: int, max_lines: int = 2):
    words = str(text or "").split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width_chars:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and (len(" ".join(lines)) < len(str(text or ""))):
        lines[-1] = lines[-1][: max(0, width_chars - 1)].rstrip() + "…"
    return lines or [""]


class PdfCanvas:
    def __init__(self, w=PAGE_W, h=PAGE_H):
        self.w, self.h = w, h
        self.ops = []
        self.images = {}  # name -> jpeg bytes

    def text(self, x, y, s, size=10, bold=False):
        font = "F2" if bold else "F1"
        self.ops.append(f"BT /{font} {size} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({_esc(s)}) Tj ET")

    def line(self, x1, y1, x2, y2, width=0.7):
        self.ops.append(f"{width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def rect(self, x, y, w, h, width=0.7, fill=None, stroke=True):
        if fill:
            r, g, b = fill
            self.ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f")
        if stroke:
            self.ops.append(f"0 0 0 RG {width:.2f} w {x:.2f} {y:.2f} {w:.2f} {h:.2f} re S")

    def image(self, name, x, y, w, h, jpeg: bytes):
        self.images[name] = jpeg
        self.ops.append(f"q {w:.2f} 0 0 {h:.2f} {x:.2f} {y:.2f} cm /{name} Do Q")

    def build(self) -> bytes:
        objects = []

        def add(obj: bytes) -> int:
            objects.append(obj)
            return len(objects)

        catalog_n = add(b"")
        pages_n = add(b"")
        add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")          # 3 = F1
        add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")     # 4 = F2

        xobject_entries = []
        for name, jpeg in self.images.items():
            info = jpeg_info(jpeg)
            if not info:
                continue
            wpx, hpx, comp = info
            cs = b"/DeviceRGB" if comp == 3 else (b"/DeviceGray" if comp == 1 else b"/DeviceCMYK")
            hdr = (
                b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
                b"/BitsPerComponent 8 /ColorSpace %s /Filter /DCTDecode /Length %d >>\nstream\n"
                % (wpx, hpx, cs, len(jpeg))
            )
            img_n = add(hdr + jpeg + b"\nendstream")
            xobject_entries.append((name, img_n))

        stream = ("\n".join(self.ops)).encode("latin-1", "replace")
        content_n = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))

        xobj = b""
        if xobject_entries:
            inner = b" ".join(b"/%s %d 0 R" % (n.encode(), o) for n, o in xobject_entries)
            xobj = b"/XObject << %s >>" % inner
        page_n = add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> %s >> /Contents %d 0 R >>"
            % (pages_n, self.w, self.h, xobj, content_n)
        )

        objects[pages_n - 1] = b"<< /Type /Pages /Kids [ %d 0 R ] /Count 1 >>" % page_n
        objects[catalog_n - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_n

        out = bytearray(b"%PDF-1.4\n")
        offsets = [0] * (len(objects) + 1)
        for i, obj in enumerate(objects, start=1):
            offsets[i] = len(out)
            out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
        xref_pos = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
        for i in range(1, len(objects) + 1):
            out += b"%010d 00000 n \n" % offsets[i]
        out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF" % (
            len(objects) + 1, catalog_n, xref_pos
        )
        return bytes(out)
