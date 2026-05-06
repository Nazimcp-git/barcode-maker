"""
Barcode Generation Engine for Library Labels.

Generates barcodes (Code128, Code39, ISBN13, EAN13) with
library-specific label content: library name, accession number,
call number, book title, etc.
"""
import io
import base64
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont


# Supported barcode types
BARCODE_TYPES = {
    'code128': 'code128',
    'code39': 'code39',
    'ean13': 'ean13',
    'isbn13': 'isbn13',
    'isbn10': 'isbn10',
}


def _get_font(size, bold=False):
    """Get a PIL font, falling back to default if custom fonts unavailable."""
    try:
        import os
        font_names = [
            'arialbd.ttf' if bold else 'arial.ttf',
            'Arial Bold.ttf' if bold else 'Arial.ttf',
        ]
        for fname in font_names:
            try:
                return ImageFont.truetype(fname, size)
            except (OSError, IOError):
                continue
        win_font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        font_file = 'arialbd.ttf' if bold else 'arial.ttf'
        return ImageFont.truetype(os.path.join(win_font_dir, font_file), size)
    except Exception:
        return ImageFont.load_default()


def generate_barcode_image(data, settings):
    """
    Generate a barcode image.

    Args:
        data (str): The data to encode.
        settings (dict): Barcode settings.

    Returns:
        PIL.Image: The barcode image.
    """
    barcode_type = settings.get('barcode_type', 'code128')
    bc_class = barcode.get_barcode_class(BARCODE_TYPES.get(barcode_type, 'code128'))

    writer = ImageWriter()

    # Writer options — render at 300 DPI for print-quality output
    writer_options = {
        'module_height': float(settings.get('module_height', 10)),
        'module_width': float(settings.get('module_width', 0.25)),
        'font_size': int(settings.get('barcode_font_size', 8)),
        'text_distance': float(settings.get('text_distance', 2)),
        'quiet_zone': float(settings.get('quiet_zone', 2)),
        'foreground': settings.get('fg_color', '#000000') if settings.get('fg_color', '#000000').startswith('#') else '#' + settings.get('fg_color', '000000'),
        'background': settings.get('bg_color', '#FFFFFF') if settings.get('bg_color', '#FFFFFF').startswith('#') else '#' + settings.get('bg_color', 'FFFFFF'),
        'write_text': settings.get('show_barcode_text', True),
        'dpi': 600,
    }

    try:
        bc = bc_class(str(data), writer=writer)
    except Exception:
        # Fallback to code128 if data doesn't match selected format
        bc_class = barcode.get_barcode_class('code128')
        bc = bc_class(str(data), writer=writer)

    # Render to BytesIO
    buffer = io.BytesIO()
    bc.write(buffer, options=writer_options)
    buffer.seek(0)

    img = Image.open(buffer).convert('RGB')
    return img


def generate_label_image(data, settings):
    """
    Generate a complete library label with barcode and text fields.

    Label layout (top to bottom):
      - Library name (header)
      - Barcode
      - Accession number / value
      - Call number (optional)

    Args:
        data (str): The barcode data / accession number.
        settings (dict): Full label settings.

    Returns:
        PIL.Image: Complete label image.
    """
    # Label dimensions in pixels (at 600 DPI — matches preview style, print-sharp)
    dpi = 600
    mm_to_px = dpi / 25.4
    label_w = int(float(settings.get('label_width_mm', 64)) * mm_to_px)
    label_h = int(float(settings.get('label_height_mm', 34)) * mm_to_px)

    bg_color = settings.get('bg_color', '#FFFFFF')
    fg_color = settings.get('fg_color', '#000000')

    # Create label canvas
    label = Image.new('RGB', (label_w, label_h), bg_color)
    draw = ImageDraw.Draw(label)

    padding = int(2 * mm_to_px)
    y_cursor = padding

    # 1. Library name (header)
    library_name = settings.get('library_name', '').strip()
    if library_name:
        header_size = int(settings.get('header_font_size', 9))
        # Convert pt size to px: 1pt = 1/72 inch; at 300 DPI → pt * 300/72 ≈ pt * 4.17
        header_font = _get_font(int(header_size * mm_to_px / 2.83), bold=True)
        bbox = draw.textbbox((0, 0), library_name, font=header_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (label_w - text_w) // 2
        draw.text((x, y_cursor), library_name, fill=fg_color, font=header_font)
        y_cursor += text_h + int(1.5 * mm_to_px)

    # 2. Barcode
    barcode_img = generate_barcode_image(data, settings)

    # Calculate barcode area
    barcode_area_h = label_h - y_cursor - padding
    # Reserve space for text below barcode
    accession_label = settings.get('accession_label', '').strip()
    call_number = settings.get('call_number_text', '').strip()

    text_lines_below = 0
    if accession_label or settings.get('show_value_text', True):
        text_lines_below += 1
    if call_number:
        text_lines_below += 1

    text_size = int(settings.get('value_font_size', 8))
    # Convert pt size to px correctly at 300 DPI (1pt = 1/72 inch; 300 DPI → pt * 4.17)
    text_font = _get_font(int(text_size * mm_to_px / 2.83))
    line_height = int(text_size * mm_to_px / 2.83) + int(0.5 * mm_to_px)
    text_total_h = text_lines_below * line_height + int(0.5 * mm_to_px)

    barcode_area_h = barcode_area_h - text_total_h

    if barcode_area_h > 20:
        # Resize barcode to fit
        bc_w, bc_h = barcode_img.size
        scale = min((label_w - 2 * padding) / bc_w, barcode_area_h / bc_h)
        new_w = int(bc_w * scale)
        new_h = int(bc_h * scale)
        barcode_img = barcode_img.resize((new_w, new_h), Image.LANCZOS)

        bc_x = (label_w - new_w) // 2
        label.paste(barcode_img, (bc_x, y_cursor))
        y_cursor += new_h + int(0.5 * mm_to_px)

    # 3. Accession number / value text
    show_value = settings.get('show_value_text', True)
    if show_value or accession_label:
        display_text = ''
        if accession_label:
            display_text = accession_label.replace('{value}', str(data))
        else:
            display_text = str(data)

        bbox = draw.textbbox((0, 0), display_text, font=text_font)
        text_w = bbox[2] - bbox[0]
        alignment = settings.get('text_alignment', 'center')
        if alignment == 'center':
            x = (label_w - text_w) // 2
        elif alignment == 'left':
            x = padding
        else:
            x = label_w - text_w - padding
        draw.text((x, y_cursor), display_text, fill=fg_color, font=text_font)
        y_cursor += line_height

    # 4. Call number
    if call_number:
        call_text = call_number.replace('{value}', str(data))
        bbox = draw.textbbox((0, 0), call_text, font=text_font)
        text_w = bbox[2] - bbox[0]
        x = (label_w - text_w) // 2
        draw.text((x, y_cursor), call_text, fill=fg_color, font=text_font)

    # Draw label border if enabled
    if settings.get('label_border', False):
        border_color = settings.get('label_border_color', '#CCCCCC')
        draw.rectangle([0, 0, label_w - 1, label_h - 1], outline=border_color, width=1)

    return label


def generate_preview_base64(data, settings):
    """Generate a label preview as base64 PNG."""
    img = generate_label_image(data, settings)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')
