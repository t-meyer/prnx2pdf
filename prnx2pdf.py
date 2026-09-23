import sys, os, gzip, base64, io, re
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

U = 72 / 300.0  # document units are 1/300 inch

F = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts') + os.sep
for name, fn in [('Arial', 'arial.ttf'), ('Arial-Bold', 'arialbd.ttf'), ('Arial-Italic', 'ariali.ttf'),
                 ('Arial-BoldItalic', 'arialbi.ttf'), ('ArialBlack', 'ariblk.ttf'),
                 ('Times', 'times.ttf'), ('Times-B', 'timesbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, F + fn))

NAMED = {'Black': (0, 0, 0), 'White': (1, 1, 1), 'WhiteSmoke': (245/255, 245/255, 245/255),
         'PeachPuff': (1, 218/255, 185/255), 'Transparent': None}


def color(v):
    if not v or v == 'Transparent':
        return None
    if v in NAMED:
        return NAMED[v]
    parts = [p.strip() for p in v.split(',')]
    if len(parts) >= 3 and all(p.isdigit() for p in parts):
        nums = [int(p) / 255 for p in parts]
        return tuple(nums[-3:]) if len(nums) == 4 and nums[0] == 0 else tuple(nums[-3:])
    c = colors.toColor(v.lower()) if hasattr(colors, v.lower()) else colors.black
    return (c.red, c.green, c.blue)


def parse_font(v):
    v = v or 'Arial, 9.75pt'
    parts = [p.strip() for p in v.split(',')]
    fam = parts[0]
    size = float(parts[1].replace('pt', '')) if len(parts) > 1 else 9.75
    style = ''
    for p in parts[2:]:
        if p.startswith('style='):
            style = p[6:]
    bold = 'Bold' in style
    ital = 'Italic' in style
    if fam == 'Arial Black':
        name = 'ArialBlack'
    elif fam.startswith('Times'):
        name = 'Times-B' if bold else 'Times'
    else:
        name = 'Arial' + ('-Bold' if bold and not ital else '-Italic' if ital and not bold
                          else '-BoldItalic' if bold and ital else '')
    return name, size


class Style:
    def __init__(self, e):
        self.font, self.size = parse_font(e.get('Font'))
        self.fore = color(e.get('ForeColor', 'Black')) or (0, 0, 0)
        self.back = color(e.get('BackColor'))
        self.bcol = color(e.get('BorderColor', 'Black')) or (0, 0, 0)
        sides = e.get('Sides', 'None')
        self.sides = {'Left', 'Top', 'Right', 'Bottom'} if sides == 'All' else \
            set(s.strip() for s in sides.split(',')) - {'None'}
        self.bw = float(e.get('BorderWidthSerializable', '1'))
        pad = [float(x) for x in e.get('Padding', '0,0,0,0,96').split(',')]
        k = 300.0 / pad[4]
        self.pad = [p * k for p in pad[:4]]  # L R T B
        self.align = e.get('TextAlignment', 'TopLeft')


def rect(e):
    return [float(x) for x in e.get('Rect').split(',')]


class Renderer:
    def __init__(self, root, out):
        self.root = root
        o = root.find('Options')
        self.styles = {s.get('Index'): Style(s) for s in o.find('SharedStyles')}
        self.shared_img = {}
        si = o.find('SharedImages')
        if si is not None:
            for it in si:
                self.shared_img[it.get('Index')] = it.get('Image')
        pd = o.find('PageData')[0]
        w, h = [float(x) for x in pd.get('Size').split(',')]  # 1/100 inch
        self.pw, self.ph = w * 0.72, h * 0.72
        self.c = canvas.Canvas(out, pagesize=(self.pw, self.ph))
        self.c.setTitle(o.get('Name', 'Bericht'))
        self.imgcache = {}

    def Y(self, y):
        return self.ph - y * U

    def run(self):
        pages = [p for p in self.root if re.fullmatch(r'Page\d+', p.tag)]
        pages.sort(key=lambda p: int(p.tag[4:]))
        for i, p in enumerate(pages):
            self.pageno = i + 1
            self.walk(p, 0, 0, top=True)
            self.c.showPage()
        self.c.save()

    def children(self, e):
        for tag in ('InnerBricks', 'Bricks'):
            b = e.find(tag)
            if b is not None:
                yield from b

    def walk(self, e, ox, oy, top=False):
        if top:
            for ch in self.children(e):
                self.walk(ch, ox, oy)
            return
        x, y, w, h = rect(e)
        x += ox
        y += oy
        bt = e.get('BrickType')
        st = self.styles.get(e.get('Style'))
        if st and st.back:
            self.c.setFillColorRGB(*st.back)
            self.c.rect(x * U, self.Y(y + h), w * U, h * U, stroke=0, fill=1)
        if bt in ('Label', 'Text', 'PageInfoText'):
            txt = e.get('Text')
            if bt == 'PageInfoText':
                txt = str(self.pageno)
            if txt:
                self.text(txt, x, y, w, h, st)
        elif bt == 'Image':
            self.image(e, x, y, w, h)
        elif bt == 'Line':
            self.line(e, x, y, w, h, st)
        for ch in self.children(e):
            self.walk(ch, x, y)
        if st and st.sides and bt != 'Line':
            self.borders(x, y, w, h, st)

    def borders(self, x, y, w, h, st):
        c = self.c
        c.setStrokeColorRGB(*st.bcol)
        c.setLineWidth(max(st.bw, 0.5) * 0.75)
        x0, x1, y0, y1 = x * U, (x + w) * U, self.Y(y), self.Y(y + h)
        if 'Left' in st.sides: c.line(x0, y0, x0, y1)
        if 'Right' in st.sides: c.line(x1, y0, x1, y1)
        if 'Top' in st.sides: c.line(x0, y0, x1, y0)
        if 'Bottom' in st.sides: c.line(x0, y1, x1, y1)

    def line(self, e, x, y, w, h, st):
        c = self.c
        c.setStrokeColorRGB(*(st.fore if st else (0, 0, 0)))
        c.setLineWidth(float(e.get('LineWidth', '1')) * 0.75)
        d = e.get('HtmlLineDirection', 'Horizontal')
        if d == 'Vertical':
            c.line((x + w / 2) * U, self.Y(y), (x + w / 2) * U, self.Y(y + h))
        elif d == 'Slant':
            c.line(x * U, self.Y(y + h), (x + w) * U, self.Y(y))
        elif d == 'BackSlant':
            c.line(x * U, self.Y(y), (x + w) * U, self.Y(y + h))
        else:
            c.line(x * U, self.Y(y + h / 2), (x + w) * U, self.Y(y + h / 2))

    def image(self, e, x, y, w, h):
        ie = e.find('ImageEntry')
        data = ie.get('Image') if ie is not None else self.shared_img.get(e.get('ImageEntry'))
        if not data:
            return
        key = hash(data)
        if key not in self.imgcache:
            self.imgcache[key] = ImageReader(io.BytesIO(base64.b64decode(data)))
        img = self.imgcache[key]
        iw, ih = img.getSize()
        mode = e.get('SizeMode', 'Normal')
        if mode in ('ZoomImage', 'Squeeze'):
            s = min(w / iw, h / ih)
            if mode == 'Squeeze':
                s = min(s, 1)
            dw, dh = iw * s, ih * s
            al = e.get('ImageAlignment', 'MiddleCenter')
            dx = x + (w - dw) / 2 if 'Center' in al else x if 'Left' in al else x + w - dw
            dy = y + (h - dh) / 2 if al.startswith('Middle') else y if al.startswith('Top') else y + h - dh
        elif mode == 'StretchImage':
            dx, dy, dw, dh = x, y, w, h
        else:
            dx, dy, dw, dh = x, y, iw * 300 / 96, ih * 300 / 96
        self.c.drawImage(img, dx * U, self.Y(dy + dh), dw * U, dh * U, mask='auto')

    def wrap(self, txt, font, size, maxw):
        lines = []
        for para in txt.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
            para = para.replace('\t', '    ')
            words = para.split(' ')
            cur = ''
            for wd in words:
                t = wd if not cur else cur + ' ' + wd
                if pdfmetrics.stringWidth(t, font, size) <= maxw or not cur:
                    cur = t
                    while pdfmetrics.stringWidth(cur, font, size) > maxw * 1.5 and len(cur) > 1:
                        k = len(cur)
                        while k > 1 and pdfmetrics.stringWidth(cur[:k], font, size) > maxw:
                            k -= 1
                        lines.append(cur[:k])
                        cur = cur[k:]
                else:
                    lines.append(cur)
                    cur = wd
            lines.append(cur)
        return lines

    def text(self, txt, x, y, w, h, st):
        st = st or self.styles['1']
        c = self.c
        L, R, T, B = st.pad
        bx, by, bw, bh = (x + L) * U, (y + T) * U, (w - L - R) * U, (h - T - B) * U
        font, size = st.font, st.size
        lead = size * 1.15
        lines = self.wrap(txt, font, size, bw * 1.04 + 1.5)
        maxl = max(1, int((bh + 0.01 * size) // lead)) if bh > 0 else 1
        lines = lines[:max(maxl, 1)]
        th = len(lines) * lead
        al = st.align
        if al.startswith('Top'):
            ty = by
        elif al.startswith('Bottom'):
            ty = by + bh - th
        else:
            ty = by + (bh - th) / 2
        c.setFillColorRGB(*st.fore)
        c.setFont(font, size)
        asc = size * 0.905
        for i, ln in enumerate(lines):
            base = self.ph - (ty + i * lead + asc + (lead - size * 1.15) / 2)
            lw = pdfmetrics.stringWidth(ln, font, size)
            if al.endswith('Right'):
                lx = bx + bw - lw
            elif al.endswith('Center'):
                lx = bx + (bw - lw) / 2
            else:
                lx = bx
            c.drawString(lx, base, ln)


def convert(src, out):
    raw = open(src, 'rb').read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    root = ET.fromstring(raw)
    Renderer(root, out).run()


def pick_files():
    import tkinter
    from tkinter import filedialog
    tk = tkinter.Tk()
    tk.withdraw()
    files = filedialog.askopenfilenames(title='PRNX-Datei auswählen',
                                        filetypes=[('DevExpress-Dokument', '*.prnx'), ('Alle Dateien', '*.*')])
    tk.destroy()
    return list(files)


def main(args):
    files = args or pick_files()
    ok = True
    for src in files:
        out = os.path.splitext(src)[0] + '.pdf'
        print(f'{os.path.basename(src)} -> {os.path.basename(out)} ... ', end='', flush=True)
        try:
            convert(src, out)
            print('fertig')
        except Exception as e:
            ok = False
            print(f'FEHLER: {e}')
    return ok


if __name__ == '__main__':
    ok = main(sys.argv[1:])
    if getattr(sys, 'frozen', False):
        input('\nEnter drücken zum Beenden ...')
    sys.exit(0 if ok else 1)
