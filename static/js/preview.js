/**
 * Preview module for barcode label previews.
 */
const Preview = {
  currentMode: 'single',
  currentPage: 1,
  totalPages: 1,

  init() {
    document.querySelectorAll('.preview-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.preview-mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentMode = btn.dataset.preview;
        this.refresh();
      });
    });

    document.getElementById('btnRefreshPreview').addEventListener('click', () => this.refresh());

    document.getElementById('prevPage').addEventListener('click', () => {
      if (this.currentPage > 1) { this.currentPage--; this.refreshLayout(); }
    });
    document.getElementById('nextPage').addEventListener('click', () => {
      if (this.currentPage < this.totalPages) { this.currentPage++; this.refreshLayout(); }
    });

    // Auto-refresh on settings change
    const debouncedRefresh = Utils.debounce(() => this.refresh(), 600);
    document.querySelectorAll('.form-input, .form-select, .form-input-color').forEach(el => {
      el.addEventListener('change', debouncedRefresh);
    });
    // Also refresh on toggle clicks
    document.querySelectorAll('.switch-track').forEach(el => {
      el.addEventListener('click', () => setTimeout(debouncedRefresh, 100));
    });
  },

  async refresh() {
    if (this.currentMode === 'single') {
      await this.refreshSingle();
    } else {
      await this.refreshLayout();
    }
  },

  async refreshSingle() {
    try {
      const settings = Settings.getBarcodeSettings();
      let sampleData = '100001';
      if (DataInput.currentMode === 'range') {
        const prefix = Utils.val('rangePrefix');
        const start = Utils.val('rangeStart');
        const suffix = Utils.val('rangeSuffix');
        sampleData = `${prefix}${start}${suffix}`;
      }

      const result = await Utils.apiPost('/api/preview', {
        sample_data: sampleData,
        settings: settings,
      });

      document.getElementById('previewImg').src = 'data:image/png;base64,' + result.image;
      document.getElementById('previewPlaceholder').style.display = 'none';
      document.getElementById('previewImage').style.display = 'block';
      document.getElementById('previewPagination').style.display = 'none';
    } catch (err) {
      Utils.toast('Preview failed: ' + err.message, 'error');
    }
  },

  async refreshLayout() {
    try {
      const settings = Settings.getBarcodeSettings();
      const layout = Settings.getLayoutSettings();
      const totalItems = Utils.calcTotalItems();

      let sampleData = '100001';
      if (DataInput.currentMode === 'range') {
        const prefix = Utils.val('rangePrefix');
        const start = Utils.val('rangeStart');
        const suffix = Utils.val('rangeSuffix');
        sampleData = `${prefix}${start}${suffix}`;
        if (!sampleData) sampleData = String(start);
      }

      const result = await Utils.apiPost('/api/preview-layout', {
        settings,
        layout,
        sample_data: sampleData,
        total_items: totalItems,
      });

      document.getElementById('previewImg').src = 'data:image/png;base64,' + result.image;
      document.getElementById('previewPlaceholder').style.display = 'none';
      document.getElementById('previewImage').style.display = 'block';

      this.totalPages = result.pages || 1;
      document.getElementById('pageInfo').textContent = `Page ${this.currentPage} of ${this.totalPages}`;
      document.getElementById('previewPagination').style.display =
        this.totalPages > 1 ? 'flex' : 'none';
    } catch (err) {
      Utils.toast('Layout preview failed: ' + err.message, 'error');
    }
  }
};
