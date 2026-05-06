"""
REST API routes for barcode label generation, file upload, and job management.
"""
import os
from flask import Blueprint, request, jsonify, send_file, current_app

from services.barcode_generator import generate_preview_base64
from services.file_parser import (
    parse_range, parse_csv, parse_excel, parse_text, get_file_columns
)
from services.pdf_builder import generate_layout_preview

api_bp = Blueprint('api', __name__, url_prefix='/api')


def get_processor():
    return current_app.config['BATCH_PROCESSOR']


@api_bp.route('/preview', methods=['POST'])
def preview_barcode():
    """Generate a single barcode label preview. Returns base64 PNG."""
    try:
        data = request.get_json()
        sample_data = data.get('sample_data', '100001')
        settings = data.get('settings', {})
        base64_img = generate_preview_base64(sample_data, settings)
        return jsonify({'image': base64_img})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/preview-layout', methods=['POST'])
def preview_layout():
    """Generate a layout preview showing barcode placement on a page."""
    try:
        data = request.get_json()
        layout = data.get('layout', {})
        settings = data.get('settings', {})
        sample_data = data.get('sample_data', '100001')

        from services.barcode_generator import generate_label_image
        cols = int(layout.get('columns', 3))
        rows = int(layout.get('rows', 8))
        sample_count = min(cols * rows, 24)

        label_settings = {**settings}
        label_settings['label_width_mm'] = layout.get('label_width_mm', 64)
        label_settings['label_height_mm'] = layout.get('label_height_mm', 34)

        items = []
        for i in range(sample_count):
            val = f"{sample_data[:-len(str(i+1))] if len(sample_data) > len(str(i+1)) else ''}{int(sample_data) + i if sample_data.isdigit() else i + 1}"
            try:
                val = str(int(sample_data) + i)
            except ValueError:
                val = f"{sample_data}-{i+1}"
            img = generate_label_image(val, label_settings)
            items.append({'image': img, 'data': val, 'label': val})

        preview_b64 = generate_layout_preview(items, layout)
        total_items = int(data.get('total_items', sample_count))
        items_per_page = cols * rows
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

        return jsonify({
            'image': preview_b64,
            'pages': total_pages,
            'items_per_page': items_per_page,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a CSV or Excel file and return column information."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'csv', 'xlsx', 'xls'})
        if ext not in allowed:
            return jsonify({'error': f'File type .{ext} not supported. Use CSV or Excel.'}), 400

        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        import uuid
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_folder, f'{file_id}.{ext}')
        file.save(file_path)

        info = get_file_columns(file_path)
        info['file_id'] = file_id
        info['filename'] = file.filename
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/generate', methods=['POST'])
def generate():
    """Start a batch barcode label generation job."""
    try:
        data = request.get_json()
        input_mode = data.get('input_mode', 'range')
        input_data = data.get('input_data', {})
        settings = data.get('settings', {})
        layout = data.get('layout', {})
        output_format = data.get('output_format', 'pdf')

        data_list = _parse_input(input_mode, input_data)

        if not data_list:
            return jsonify({'error': 'No data to generate. Check your input.'}), 400

        max_batch = current_app.config.get('MAX_BATCH_SIZE', 50000)
        if len(data_list) > max_batch:
            return jsonify({'error': f'Batch size {len(data_list)} exceeds max {max_batch}.'}), 400

        processor = get_processor()
        job_id = processor.submit_job(data_list, settings, layout, output_format)
        return jsonify({'job_id': job_id, 'total': len(data_list)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/job/<job_id>/status', methods=['GET'])
def job_status(job_id):
    processor = get_processor()
    status = processor.get_status(job_id)
    if status is None:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(status)


@api_bp.route('/job/<job_id>/download', methods=['GET'])
def job_download(job_id):
    processor = get_processor()
    status = processor.get_status(job_id)
    if status is None:
        return jsonify({'error': 'Job not found'}), 404
    if status['status'] != 'completed':
        return jsonify({'error': 'Job not yet completed'}), 400
    output_path = processor.get_output_path(job_id)
    if not output_path or not os.path.exists(output_path):
        return jsonify({'error': 'Output file not found'}), 404
    return send_file(output_path, as_attachment=True, download_name=status.get('filename', 'barcodes.pdf'))


@api_bp.route('/job/<job_id>/cancel', methods=['POST'])
def job_cancel(job_id):
    processor = get_processor()
    success = processor.cancel_job(job_id)
    if success:
        return jsonify({'message': 'Job cancelled'})
    return jsonify({'error': 'Job not found or already completed'}), 404


def _parse_input(mode, input_data):
    if mode == 'range':
        return parse_range(
            start=int(input_data.get('start', 1)),
            end=int(input_data.get('end', 100)),
            step=int(input_data.get('step', 1)),
            prefix=input_data.get('prefix', ''),
            suffix=input_data.get('suffix', ''),
        )
    elif mode == 'text':
        return parse_text(input_data.get('text', ''))
    elif mode == 'file':
        file_id = input_data.get('file_id', '')
        column = input_data.get('column', '')
        upload_folder = current_app.config['UPLOAD_FOLDER']
        for fname in os.listdir(upload_folder):
            if fname.startswith(file_id):
                file_path = os.path.join(upload_folder, fname)
                ext = fname.rsplit('.', 1)[-1].lower()
                if ext == 'csv':
                    return parse_csv(file_path, column or None)
                else:
                    return parse_excel(file_path, column_name=column or None)
        raise ValueError('Uploaded file not found. Please re-upload.')
    else:
        raise ValueError(f'Unknown input mode: {mode}')
