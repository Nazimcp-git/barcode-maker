"""
PDF & Output Builder.

Generates print-ready PDF, ZIP archives of individual images,
and PNG sheet outputs from barcode label images.

PDF output uses native ReportLab vector drawing (vector barcodes + vector text)
for crystal-clear, resolution-independent output at any print size.
"""
import os
import io
import zipfile
from PIL import Image
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4, A5, letter, legal
from reportlab.lib import colors as rl_colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader

# Map page size names to ReportLab page sizes
PAGE_SIZE_MAP = {
    'A4': A4,
    'A5': A5,
    'Letter': letter,
    'Legal': legal,
}


def _get_page_dimensions(layout):
    page_size_name = layout.get('page_size', 'A4')
    orientation = layout.get('orientation', 'portrait')

    if page_size_name == 'Custom':
        w = float(layout.get('custom_width_mm', 210)) * mm
        h = float(layout.get('custom_height_mm', 297)) * mm
    else:
        page_size = PAGE_SIZE_MAP.get(page_size_name, A4)
        w, h = page_size

    if orientation == 'landscape':
        w, h = h, w
    return w, h


def _calc_grid(layout, page_w, page_h):
    margin_top    = float(layout.get('margin_top_mm',    10)) * mm
    margin_bottom = float(layout.get('margin_bottom_mm', 10)) * mm
    margin_left   = float(layout.get('margin_left_mm',  10)) * mm
    margin_right  = float(layout.get('margin_right_mm', 10)) * mm
    label_w = float(layout.get('label_width_mm',  40)) * mm
    label_h = float(layout.get('label_height_mm', 50)) * mm
    gap_h   = float(layout.get('gap_h_mm', 5)) * mm
    gap_v   = float(layout.get('gap_v_mm', 5)) * mm

    avail_w = page_w - margin_left - margin_right
    avail_h = page_h - margin_top  - margin_bottom

    cols = layout.get('columns')
    rows = layout.get('rows')
    if not cols or cols == 'auto':
        cols = max(1, int((avail_w + gap_h) / (label_w + gap_h)))
    else:
        cols = int(cols)
    if not rows or rows == 'auto':
        rows = max(1, int((avail_h + gap_v) / (label_h + gap_v)))
    else:
        rows = int(rows)

    return {
        'cols': cols, 'rows': rows,
        'items_per_page': cols * rows,
        'margin_top': margin_top, 'margin_bottom': margin_bottom,
        'margin_left': margin_left, 'margin_right': margin_right,
        'label_w': label_w, 'label_h': label_h,
        'gap_h': gap_h, 'gap_v': gap_v,
    }


# ---------------------------------------------------------------------------
# Vector label drawing — pure ReportLab, no raster pixels
# ---------------------------------------------------------------------------

def _hex_color(h, default='#000000'):
    h = (h or default).strip()
    if not h.startswith('#'):
        h = '#' + h
    try:
        return rl_colors.HexColor(h)
    except Exception:
        return rl_colors.black


def _draw_aligned(c, label_x, label_w, y, text, font_name, font_size, alignment, pad):
    if alignment == 'center':
        c.drawCentredString(label_x + label_w / 2, y, text)
    elif alignment == 'left':
        c.drawString(label_x + pad, y, text)
    else:
        tw = c.stringWidth(text, font_name, font_size)
        c.drawString(label_x + label_w - tw - pad, y, text)


def _draw_vector_barcode(c, label_x, label_w, bc_bottom, avail_w, avail_h,
                          data, bc_type, human_readable, font_size_pt):
    """Draw a native ReportLab vector barcode, centred horizontally."""
    try:
        bc_type = (bc_type or 'code128').lower()

        if bc_type == 'code39':
            from reportlab.graphics.barcode.code39 import Standard39
            bc = Standard39(
                data, barWidth=0.38 * mm, barHeight=avail_h,
                humanReadable=human_readable,
                fontSize=font_size_pt * 0.75,
                checksum=0, bearers=0, quiet=True,
            )

        elif bc_type in ('ean13', 'isbn13'):
            from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics import renderPDF
            digits = ''.join(ch for ch in data if ch.isdigit())
            digits = (digits + '0' * 12)[:12]
            wid = Ean13BarcodeWidget(digits)
            sc = min(avail_w / wid.width, avail_h / wid.height, 1.0)
            d = Drawing(wid.width * sc, wid.height * sc)
            wid.transform = (sc, 0, 0, sc, 0, 0)
            d.add(wid)
            cx = label_x + (label_w - wid.width * sc) / 2
            renderPDF.draw(d, c, cx, bc_bottom)
            return

        elif bc_type == 'ean8':
            from reportlab.graphics.barcode.eanbc import Ean8BarcodeWidget
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics import renderPDF
            digits = ''.join(ch for ch in data if ch.isdigit())
            digits = (digits + '0' * 7)[:7]
            wid = Ean8BarcodeWidget(digits)
            sc = min(avail_w / wid.width, avail_h / wid.height, 1.0)
            d = Drawing(wid.width * sc, wid.height * sc)
            wid.transform = (sc, 0, 0, sc, 0, 0)
            d.add(wid)
            cx = label_x + (label_w - wid.width * sc) / 2
            renderPDF.draw(d, c, cx, bc_bottom)
            return

        else:  # code128 (default)
            from reportlab.graphics.barcode.code128 import Code128
            bc = Code128(
                data, barWidth=0.32 * mm, barHeight=avail_h,
                humanReadable=human_readable,
                fontSize=font_size_pt * 0.75,
                quiet=True, lquiet=2 * mm, rquiet=2 * mm,
            )

        # Scale down barWidth if barcode is wider than available space
        if bc.width > avail_w:
            ratio = avail_w / bc.width
            if bc_type == 'code39':
                from reportlab.graphics.barcode.code39 import Standard39
                bc = Standard39(
                    data, barWidth=0.38 * mm * ratio, barHeight=avail_h,
                    humanReadable=human_readable,
                    fontSize=font_size_pt * 0.75,
                    checksum=0, bearers=0, quiet=True,
                )
            else:
                from reportlab.graphics.barcode.code128 import Code128
                bc = Code128(
                    data, barWidth=0.32 * mm * ratio, barHeight=avail_h,
                    humanReadable=human_readable,
                    fontSize=font_size_pt * 0.75,
                    quiet=True, lquiet=2 * mm, rquiet=2 * mm,
                )

        bc_x = label_x + (label_w - bc.width) / 2
        bc.drawOn(c, bc_x, bc_bottom)

    except Exception:
        # Fallback: simple box placeholder
        c.setLineWidth(0.4)
        c.rect(label_x + 2 * mm, bc_bottom, avail_w, avail_h, stroke=1, fill=0)
        c.setFont('Helvetica', 6)
        c.drawCentredString(label_x + label_w / 2, bc_bottom + avail_h / 2 - 3, str(data))


def _draw_label_vector(c, x, y, label_w, label_h, data, settings):
    """
    Draw one barcode label directly on the ReportLab canvas using
    pure vector graphics — no raster pixels, infinite sharpness.
    """
    pad = 1.5 * mm

    bg  = _hex_color(settings.get('bg_color',  '#FFFFFF'))
    fg  = _hex_color(settings.get('fg_color',  '#000000'))

    # Background fill
    c.setFillColor(bg)
    c.rect(x, y, label_w, label_h, fill=1, stroke=0)

    # Border
    if settings.get('label_border', False):
        c.setStrokeColor(_hex_color(settings.get('label_border_color', '#CCCCCC')))
        c.setLineWidth(0.4)
        c.rect(x, y, label_w, label_h, fill=0, stroke=1)

    c.setFillColor(fg)

    header_pt  = float(settings.get('header_font_size', 9))
    value_pt   = float(settings.get('value_font_size',  8))
    show_bc_text = bool(settings.get('show_barcode_text', True))
    show_value   = bool(settings.get('show_value_text',   True))
    acc_label    = settings.get('accession_label',   '').strip()
    call_num     = settings.get('call_number_text',  '').strip()
    library      = settings.get('library_name',      '').strip()
    bc_type      = settings.get('barcode_type', 'code128')
    alignment    = settings.get('text_alignment', 'center')

    # Vertical layout (top → bottom)
    cursor = y + label_h - pad   # descending cursor

    # 1. Library name header
    if library:
        c.setFont('Helvetica-Bold', header_pt)
        cursor -= header_pt
        c.drawCentredString(x + label_w / 2, cursor, library)
        cursor -= 1.5 * mm

    # 2. Reserve space for text lines below barcode
    text_lines = 0
    if show_value or acc_label:
        text_lines += 1
    if call_num:
        text_lines += 1
    text_area_h = text_lines * (value_pt + 1.5 * mm)

    # 3. Draw barcode in remaining space
    bc_top    = cursor
    bc_bottom = y + pad + text_area_h
    bc_avail_h = bc_top - bc_bottom
    bc_avail_w = label_w - 2 * pad

    if bc_avail_h > 4 * mm:
        _draw_vector_barcode(
            c, x, label_w, bc_bottom, bc_avail_w, bc_avail_h,
            str(data), bc_type, show_bc_text, value_pt,
        )

    # 4. Text below barcode
    c.setFont('Helvetica', value_pt)
    c.setFillColor(fg)
    y_txt = y + pad + text_area_h

    if show_value or acc_label:
        disp = acc_label.replace('{value}', str(data)) if acc_label else str(data)
        y_txt -= value_pt + 1.5 * mm
        _draw_aligned(c, x, label_w, y_txt, disp, 'Helvetica', value_pt, alignment, pad)

    if call_num:
        call_text = call_num.replace('{value}', str(data))
        y_txt -= value_pt + 1.5 * mm
        _draw_aligned(c, x, label_w, y_txt, call_text, 'Helvetica', value_pt, 'center', pad)


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def build_pdf(qr_items, layout, output_path, settings=None):
    """
    Build a print-ready PDF.

    When `settings` is provided the labels are drawn natively with
    ReportLab vector graphics (crystal-clear at any resolution).
    When `settings` is None the pre-rendered PIL images are embedded.

    Args:
        qr_items (list[dict]): [{'image': PIL.Image, 'data': str, 'label': str}]
        layout   (dict): Layout/page settings.
        output_path (str): Destination .pdf path.
        settings (dict | None): Label style settings for vector drawing.
    """
    page_w, page_h = _get_page_dimensions(layout)
    grid = _calc_grid(layout, page_w, page_h)

    c = canvas.Canvas(output_path, pagesize=(page_w, page_h))
    c.setTitle('Barcode Labels')
    c.setCreator('Barcode Label Generator')

    total       = len(qr_items)
    per_page    = grid['items_per_page']
    page_count  = (total + per_page - 1) // per_page

    # Points-per-pixel at 300 DPI (used only for raster fallback)
    PX_TO_PT = 72.0 / 300.0

    for page in range(page_count):
        if page > 0:
            c.showPage()

        start = page * per_page
        end   = min(start + per_page, total)

        for i in range(start, end):
            local = i - start
            col   = local % grid['cols']
            row   = local // grid['cols']

            x = grid['margin_left'] + col * (grid['label_w'] + grid['gap_h'])
            y = page_h - grid['margin_top'] - (row + 1) * grid['label_h'] - row * grid['gap_v']

            item = qr_items[i]

            if settings is not None:
                # ---- VECTOR PATH: crystal clear ----
                _draw_label_vector(
                    c, x, y, grid['label_w'], grid['label_h'],
                    item['data'], settings,
                )
            else:
                # ---- RASTER FALLBACK: embed PIL image ----
                img = item['image']
                buf = io.BytesIO()
                img.save(buf, format='PNG', dpi=(300, 300), optimize=False)
                buf.seek(0)
                reader = ImageReader(buf)

                iw_pt = img.width  * PX_TO_PT
                ih_pt = img.height * PX_TO_PT
                scale = min(
                    grid['label_w'] / iw_pt,
                    grid['label_h'] / ih_pt,
                    1.0,
                )
                draw_w = iw_pt * scale
                draw_h = ih_pt * scale
                c.drawImage(
                    reader,
                    x + (grid['label_w'] - draw_w) / 2,
                    y + (grid['label_h'] - draw_h) / 2,
                    width=draw_w, height=draw_h,
                    mask='auto',
                )

    c.save()


def build_zip(qr_items, output_path):
    """Build a ZIP of individual 300-DPI PNG images."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, item in enumerate(qr_items):
            buf = io.BytesIO()
            item['image'].save(buf, format='PNG', dpi=(300, 300))
            buf.seek(0)
            zf.writestr(f"{_safe_filename(item['data'], i)}.png", buf.getvalue())


def build_png_sheet(qr_items, layout, output_path):
    """Build a 300-DPI PNG sheet (first page only)."""
    page_size_name = layout.get('page_size', 'A4')
    orientation    = layout.get('orientation', 'portrait')
    dpi = 300
    mm_to_px = dpi / 25.4

    sizes_mm = {
        'A4': (210, 297), 'A5': (148, 210),
        'Letter': (215.9, 279.4), 'Legal': (215.9, 355.6),
    }
    if page_size_name == 'Custom':
        pw_mm = float(layout.get('custom_width_mm', 210))
        ph_mm = float(layout.get('custom_height_mm', 297))
    else:
        pw_mm, ph_mm = sizes_mm.get(page_size_name, (210, 297))

    if orientation == 'landscape':
        pw_mm, ph_mm = ph_mm, pw_mm

    pw_px = int(pw_mm * mm_to_px)
    ph_px = int(ph_mm * mm_to_px)

    margin_top  = int(float(layout.get('margin_top_mm',  10)) * mm_to_px)
    margin_left = int(float(layout.get('margin_left_mm', 10)) * mm_to_px)
    label_w = int(float(layout.get('label_width_mm',  40)) * mm_to_px)
    label_h = int(float(layout.get('label_height_mm', 50)) * mm_to_px)
    gap_h   = int(float(layout.get('gap_h_mm', 5)) * mm_to_px)
    gap_v   = int(float(layout.get('gap_v_mm', 5)) * mm_to_px)

    cols = layout.get('columns', 4)
    rows = layout.get('rows', 5)
    cols = int(cols) if not isinstance(cols, str) else 4
    rows = int(rows) if not isinstance(rows, str) else 5

    sheet = Image.new('RGB', (pw_px, ph_px), 'white')
    per_page = cols * rows

    for i in range(min(len(qr_items), per_page)):
        col = i % cols
        row = i // cols
        x = margin_left + col * (label_w + gap_h)
        y = margin_top  + row * (label_h + gap_v)
        img = qr_items[i]['image'].resize((label_w, label_h), Image.LANCZOS)
        sheet.paste(img, (x, y))

    sheet.save(output_path, dpi=(300, 300))


def _safe_filename(data, index):
    safe = ''.join(c if c.isalnum() or c in '-_' else '_' for c in str(data))[:50]
    return f"barcode_{index + 1:05d}_{safe}" if safe else f"barcode_{index + 1:05d}"


def generate_layout_preview(qr_items, layout, max_items=20):
    """Generate a low-res preview image for the frontend (base64 PNG)."""
    import base64
    from PIL import ImageDraw

    sizes_mm = {
        'A4': (210, 297), 'A5': (148, 210),
        'Letter': (215.9, 279.4), 'Legal': (215.9, 355.6),
    }
    page_size_name = layout.get('page_size', 'A4')
    orientation    = layout.get('orientation', 'portrait')

    if page_size_name == 'Custom':
        pw_mm = float(layout.get('custom_width_mm', 210))
        ph_mm = float(layout.get('custom_height_mm', 297))
    else:
        pw_mm, ph_mm = sizes_mm.get(page_size_name, (210, 297))

    if orientation == 'landscape':
        pw_mm, ph_mm = ph_mm, pw_mm

    px_per_mm = 3
    pw = int(pw_mm * px_per_mm)
    ph = int(ph_mm * px_per_mm)

    margin_top   = int(float(layout.get('margin_top_mm',   10)) * px_per_mm)
    margin_left  = int(float(layout.get('margin_left_mm',  10)) * px_per_mm)
    margin_right = int(float(layout.get('margin_right_mm', 10)) * px_per_mm)
    margin_bottom= int(float(layout.get('margin_bottom_mm',10)) * px_per_mm)
    label_w = int(float(layout.get('label_width_mm',  40)) * px_per_mm)
    label_h = int(float(layout.get('label_height_mm', 50)) * px_per_mm)
    gap_h   = int(float(layout.get('gap_h_mm', 5)) * px_per_mm)
    gap_v   = int(float(layout.get('gap_v_mm', 5)) * px_per_mm)

    cols = layout.get('columns', 4)
    rows = layout.get('rows', 5)
    cols = int(cols) if not isinstance(cols, str) else 4
    rows = int(rows) if not isinstance(rows, str) else 5

    sheet = Image.new('RGB', (pw, ph), '#FFFFFF')
    draw  = ImageDraw.Draw(sheet)
    draw.rectangle(
        [margin_left, margin_top, pw - margin_right, ph - margin_bottom],
        outline='#E0E0E0', width=1,
    )

    per_page  = cols * rows
    num_items = min(len(qr_items) if qr_items else per_page, per_page, max_items)

    for i in range(num_items):
        col = i % cols
        row = i // cols
        x = margin_left + col * (label_w + gap_h)
        y = margin_top  + row * (label_h + gap_v)

        if qr_items and i < len(qr_items):
            img = qr_items[i]['image'].resize((label_w, label_h), Image.LANCZOS)
            sheet.paste(img, (x, y))
        else:
            draw.rectangle([x, y, x + label_w, y + label_h],
                           outline='#CCCCCC', fill='#F5F5F5')
            ic = min(label_w, label_h) // 3
            cx, cy = x + label_w // 2, y + label_h // 2
            draw.rectangle([cx - ic, cy - ic, cx + ic, cy + ic],
                           outline='#AAAAAA', width=1)

    buf = io.BytesIO()
    sheet.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')
