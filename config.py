"""
Application configuration for Library Barcode Label Generator.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'barcode-label-generator-2025')

    # --- File Upload ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
    TEMPLATES_FOLDER = os.path.join(BASE_DIR, 'saved_templates')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

    # --- Batch Processing ---
    MAX_BATCH_SIZE = 50000
    MAX_WORKERS = 4
    JOB_CLEANUP_MINUTES = 30

    # --- Barcode Defaults ---
    DEFAULT_BARCODE_SETTINGS = {
        'barcode_type': 'code128',
        'width_mm': 50,
        'height_mm': 25,
        'module_height': 10,   # bar height in mm
        'font_size': 8,
        'text_distance': 2,
        'quiet_zone': 2,
        'fg_color': '#000000',
        'bg_color': '#FFFFFF',
    }

    # --- Label Defaults (for library stickers) ---
    DEFAULT_LAYOUT = {
        'page_size': 'A4',
        'orientation': 'portrait',
        'margin_top_mm': 12,
        'margin_bottom_mm': 12,
        'margin_left_mm': 7,
        'margin_right_mm': 7,
        'label_width_mm': 64,
        'label_height_mm': 34,
        'gap_h_mm': 3,
        'gap_v_mm': 0,
        'columns': 3,
        'rows': 8,
    }

    # --- Page Sizes (mm) ---
    PAGE_SIZES = {
        'A4': (210, 297),
        'A5': (148, 210),
        'Letter': (215.9, 279.4),
        'Legal': (215.9, 355.6),
    }

    PRINT_DPI = 300
