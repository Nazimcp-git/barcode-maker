"""
Library Barcode Label Generator — Flask Application Entry Point.

A web application for generating bulk barcode labels for library books
with customizable layouts and print-ready PDF output.
"""
import os
from flask import Flask
from config import Config
from services.batch_processor import BatchProcessor


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['OUTPUT_FOLDER'] = Config.OUTPUT_FOLDER
    app.config['TEMPLATES_FOLDER'] = Config.TEMPLATES_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['ALLOWED_EXTENSIONS'] = Config.ALLOWED_EXTENSIONS
    app.config['MAX_BATCH_SIZE'] = Config.MAX_BATCH_SIZE

    for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER, Config.TEMPLATES_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    app.config['BATCH_PROCESSOR'] = BatchProcessor(
        output_folder=Config.OUTPUT_FOLDER,
        max_workers=Config.MAX_WORKERS,
        cleanup_minutes=Config.JOB_CLEANUP_MINUTES,
    )

    from routes.main import main_bp
    from routes.api import api_bp
    from routes.templates_api import templates_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(templates_bp)

    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(413)
    def too_large(e):
        return {'error': 'File too large. Maximum size is 50 MB.'}, 413

    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "=" * 60)
    print("  Library Barcode Label Generator")
    print("  http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
