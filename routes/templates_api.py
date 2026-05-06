"""
Template save/load API routes.

Manages saved layout/QR setting templates as JSON files.
"""
import os
import json
from flask import Blueprint, request, jsonify, current_app

templates_bp = Blueprint('templates_api', __name__, url_prefix='/api/templates')


def _get_templates_dir():
    """Get the templates storage directory."""
    path = current_app.config['TEMPLATES_FOLDER']
    os.makedirs(path, exist_ok=True)
    return path


@templates_bp.route('', methods=['GET'])
def list_templates():
    """
    List all saved templates.

    Returns: {'templates': [{'name': str, 'description': str, 'created_at': str}, ...]}
    """
    templates_dir = _get_templates_dir()
    templates = []

    for fname in os.listdir(templates_dir):
        if fname.endswith('.json'):
            try:
                with open(os.path.join(templates_dir, fname), 'r') as f:
                    data = json.load(f)
                templates.append({
                    'name': data.get('name', fname.replace('.json', '')),
                    'description': data.get('description', ''),
                    'created_at': data.get('created_at', ''),
                })
            except (json.JSONDecodeError, IOError):
                continue

    return jsonify({'templates': templates})


@templates_bp.route('', methods=['POST'])
def save_template():
    """
    Save current settings as a named template.

    Expects JSON body:
        - name (str): Template name
        - description (str): Optional description
        - settings (dict): QR settings
        - layout (dict): Layout settings
    """
    try:
        data = request.get_json()
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'error': 'Template name is required'}), 400

        # Sanitize filename
        safe_name = ''.join(c if c.isalnum() or c in '-_ ' else '' for c in name)
        safe_name = safe_name.strip().replace(' ', '_')

        if not safe_name:
            return jsonify({'error': 'Invalid template name'}), 400

        from datetime import datetime
        template_data = {
            'name': name,
            'description': data.get('description', ''),
            'settings': data.get('settings', {}),
            'layout': data.get('layout', {}),
            'text_settings': data.get('text_settings', {}),
            'created_at': datetime.now().isoformat(),
        }

        # Remove logo path (not portable)
        if 'logo_path' in template_data['settings']:
            del template_data['settings']['logo_path']
        if 'logo_file_id' in template_data['settings']:
            del template_data['settings']['logo_file_id']

        templates_dir = _get_templates_dir()
        filepath = os.path.join(templates_dir, f'{safe_name}.json')

        with open(filepath, 'w') as f:
            json.dump(template_data, f, indent=2)

        return jsonify({'message': f'Template "{name}" saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@templates_bp.route('/<name>', methods=['GET'])
def load_template(name):
    """
    Load a specific template by name.

    Returns: Full template data including settings and layout.
    """
    templates_dir = _get_templates_dir()
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '' for c in name)
    filepath = os.path.join(templates_dir, f'{safe_name}.json')

    if not os.path.exists(filepath):
        return jsonify({'error': f'Template "{name}" not found'}), 404

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@templates_bp.route('/<name>', methods=['DELETE'])
def delete_template(name):
    """Delete a template by name."""
    templates_dir = _get_templates_dir()
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '' for c in name)
    filepath = os.path.join(templates_dir, f'{safe_name}.json')

    if not os.path.exists(filepath):
        return jsonify({'error': f'Template "{name}" not found'}), 404

    try:
        os.remove(filepath)
        return jsonify({'message': f'Template "{name}" deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
