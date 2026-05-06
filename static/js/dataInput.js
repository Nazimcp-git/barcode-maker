/**
 * Data Input module — handles input mode switching, file upload, and column selection.
 * Updated for Library Barcode Label Generator (no logo upload needed).
 */
const DataInput = {
  currentMode: 'range',
  fileId: null,
  fileRowCount: 0,

  init() {
    // Input mode switching
    document.querySelectorAll('.input-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.input-mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentMode = btn.dataset.mode;

        document.getElementById('mode-range').style.display = this.currentMode === 'range' ? 'block' : 'none';
        document.getElementById('mode-text').style.display = this.currentMode === 'text' ? 'block' : 'none';
        document.getElementById('mode-file').style.display = this.currentMode === 'file' ? 'block' : 'none';

        Utils.updateCounts();
      });
    });

    this._initFileUpload();
  },

  _initFileUpload() {
    const dropZone = document.getElementById('fileDropZone');
    const fileInput = document.getElementById('fileInput');

    if (!dropZone || !fileInput) return;

    // Click to browse
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag & drop
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      if (e.dataTransfer.files.length > 0) this._handleFileUpload(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) this._handleFileUpload(fileInput.files[0]);
    });

    // Remove file
    const removeBtn = document.getElementById('fileRemove');
    if (removeBtn) {
      removeBtn.addEventListener('click', () => {
        this.fileId = null;
        this.fileRowCount = 0;
        document.getElementById('fileInfo').style.display = 'none';
        document.getElementById('columnSelector').style.display = 'none';
        document.getElementById('fileDropZone').style.display = 'block';
        Utils.updateCounts();
      });
    }
  },

  async _handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      Utils.toast('Uploading file…', 'info');
      const result = await Utils.apiPost('/api/upload', formData, true);

      this.fileId = result.file_id;
      this.fileRowCount = result.total_rows;

      // Show file info
      document.getElementById('fileDropZone').style.display = 'none';
      document.getElementById('fileInfo').style.display = 'flex';
      document.getElementById('fileName').textContent = `${result.filename} (${result.total_rows} rows)`;

      // Show column selector
      const select = document.getElementById('columnSelect');
      select.innerHTML = '';
      result.columns.forEach(col => {
        const opt = document.createElement('option');
        opt.value = col;
        opt.textContent = col;
        select.appendChild(opt);
      });
      document.getElementById('columnSelector').style.display = 'block';

      // Show preview table
      this._showDataPreview(result.columns, result.preview);

      Utils.updateCounts();
      Utils.toast(`File loaded: ${result.total_rows} rows`, 'success');
    } catch (err) {
      Utils.toast('File upload failed: ' + err.message, 'error');
    }
  },

  _showDataPreview(columns, rows) {
    const container = document.getElementById('dataPreview');
    if (!container) return;
    if (!rows || rows.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted); font-size:0.8rem;">No data to preview</div>';
      return;
    }

    let html = '<table class="data-preview-table"><thead><tr>';
    columns.forEach(col => { html += `<th>${col}</th>`; });
    html += '</tr></thead><tbody>';
    rows.forEach(row => {
      html += '<tr>';
      row.forEach(cell => { html += `<td>${cell}</td>`; });
      html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /**
   * Get input data for generation API call.
   */
  getInputData() {
    if (this.currentMode === 'range') {
      return {
        input_mode: 'range',
        input_data: {
          start: Utils.val('rangeStart'),
          end: Utils.val('rangeEnd'),
          step: Utils.val('rangeStep'),
          prefix: Utils.val('rangePrefix'),
          suffix: Utils.val('rangeSuffix'),
        }
      };
    } else if (this.currentMode === 'text') {
      return {
        input_mode: 'text',
        input_data: { text: Utils.val('textInput') }
      };
    } else {
      return {
        input_mode: 'file',
        input_data: {
          file_id: this.fileId || '',
          column: Utils.val('columnSelect'),
        }
      };
    }
  }
};
