"""
Batch Processor for bulk barcode label generation.

Uses ThreadPoolExecutor for background processing with progress tracking.
"""
import os
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from services.barcode_generator import generate_label_image
from services.pdf_builder import build_pdf, build_zip, build_png_sheet


class BatchProcessor:
    """Manages background barcode generation jobs."""

    def __init__(self, output_folder, max_workers=4, cleanup_minutes=30):
        self.output_folder = output_folder
        self.max_workers = max_workers
        self.cleanup_minutes = cleanup_minutes
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {}
        self._lock = threading.Lock()

        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def submit_job(self, data_list, settings, layout_settings, output_format='pdf'):
        job_id = str(uuid.uuid4())

        with self._lock:
            self.jobs[job_id] = {
                'status': 'queued',
                'progress': 0,
                'total': len(data_list),
                'percent': 0,
                'download_url': None,
                'filename': None,
                'error': None,
                'created_at': datetime.now(),
            }

        self.executor.submit(
            self._process_job,
            job_id, data_list, settings, layout_settings, output_format
        )
        return job_id

    def get_status(self, job_id):
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                return {
                    'status': job['status'],
                    'progress': job['progress'],
                    'total': job['total'],
                    'percent': job['percent'],
                    'download_url': job['download_url'],
                    'filename': job['filename'],
                    'error': job['error'],
                }
        return None

    def cancel_job(self, job_id):
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = 'cancelled'
                return True
        return False

    def _process_job(self, job_id, data_list, settings, layout_settings, output_format):
        try:
            with self._lock:
                self.jobs[job_id]['status'] = 'processing'

            label_images = []
            for i, data in enumerate(data_list):
                with self._lock:
                    if self.jobs[job_id]['status'] == 'cancelled':
                        return

                # Merge label dimensions into settings for label generation
                label_settings = {**settings}
                label_settings['label_width_mm'] = layout_settings.get('label_width_mm', 64)
                label_settings['label_height_mm'] = layout_settings.get('label_height_mm', 34)

                img = generate_label_image(data, label_settings)
                label_images.append({'image': img, 'data': data, 'label': data})

                with self._lock:
                    self.jobs[job_id]['progress'] = i + 1
                    self.jobs[job_id]['percent'] = round(((i + 1) / len(data_list)) * 90)

            with self._lock:
                self.jobs[job_id]['status'] = 'building_output'

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if output_format == 'pdf':
                filename = f'barcodes_{timestamp}.pdf'
                output_path = os.path.join(self.output_folder, filename)
                build_pdf(label_images, layout_settings, output_path)
            elif output_format == 'zip':
                filename = f'barcodes_{timestamp}.zip'
                output_path = os.path.join(self.output_folder, filename)
                build_zip(label_images, output_path)
            elif output_format == 'png':
                filename = f'barcodes_{timestamp}.png'
                output_path = os.path.join(self.output_folder, filename)
                build_png_sheet(label_images, layout_settings, output_path)
            else:
                raise ValueError(f"Unknown output format: {output_format}")

            with self._lock:
                self.jobs[job_id]['status'] = 'completed'
                self.jobs[job_id]['progress'] = len(data_list)
                self.jobs[job_id]['percent'] = 100
                self.jobs[job_id]['download_url'] = f'/api/job/{job_id}/download'
                self.jobs[job_id]['filename'] = filename

        except Exception as e:
            with self._lock:
                self.jobs[job_id]['status'] = 'failed'
                self.jobs[job_id]['error'] = str(e)

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            cutoff = datetime.now() - timedelta(minutes=self.cleanup_minutes)
            with self._lock:
                expired = [
                    jid for jid, info in self.jobs.items()
                    if info['status'] in ('completed', 'failed', 'cancelled')
                    and info['created_at'] < cutoff
                ]
            for jid in expired:
                with self._lock:
                    job = self.jobs.pop(jid, None)
                if job and job.get('filename'):
                    filepath = os.path.join(self.output_folder, job['filename'])
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except OSError:
                        pass

    def get_output_path(self, job_id):
        with self._lock:
            job = self.jobs.get(job_id)
            if job and job['filename']:
                return os.path.join(self.output_folder, job['filename'])
        return None
