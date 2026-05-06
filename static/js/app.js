/**
 * Main Application Controller for Library Barcode Label Generator.
 */
const App = {
  currentJobId: null,
  pollInterval: null,

  init() {
    Settings.init();
    DataInput.init();
    Preview.init();

    // Tab navigation
    document.querySelectorAll('.sidebar-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
      });
    });

    // Generate
    document.getElementById('btnGenerate').addEventListener('click', () => this.startGeneration());
    document.getElementById('btnCancel').addEventListener('click', () => this.cancelJob());

    // Templates
    document.getElementById('btnSaveTemplate').addEventListener('click', () => this.openSaveModal());
    document.getElementById('modalCancel').addEventListener('click', () => this.closeSaveModal());
    document.getElementById('modalSave').addEventListener('click', () => this.saveTemplate());
    document.getElementById('templateSelect').addEventListener('change', (e) => {
      if (e.target.value) this.loadTemplate(e.target.value);
    });
    document.getElementById('btnDeleteTemplate').addEventListener('click', () => this.deleteTemplate());
    document.getElementById('saveTemplateModal').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) this.closeSaveModal();
    });

    Utils.updateCounts();
    this.refreshTemplateList();
    setTimeout(() => Preview.refresh(), 600);
  },

  async startGeneration() {
    const total = Utils.calcTotalItems();
    if (total === 0) {
      Utils.toast('No data to generate. Configure input first.', 'error');
      return;
    }

    const inputData = DataInput.getInputData();
    const settings = Settings.getBarcodeSettings();
    const layout = Settings.getLayoutSettings();
    const outputFormat = Utils.val('outputFormat');

    try {
      const btn = document.getElementById('btnGenerate');
      btn.disabled = true;
      btn.innerHTML = '⏳ Starting…';

      const result = await Utils.apiPost('/api/generate', {
        ...inputData, settings, layout, output_format: outputFormat,
      });

      this.currentJobId = result.job_id;
      Utils.toast(`Generating ${result.total} barcode labels…`, 'info');
      this._showProgress(true);
      this.pollInterval = setInterval(() => this.pollStatus(), 800);
    } catch (err) {
      Utils.toast('Generation failed: ' + err.message, 'error');
      this._resetBtn();
    }
  },

  async pollStatus() {
    if (!this.currentJobId) return;
    try {
      const status = await Utils.apiGet(`/api/job/${this.currentJobId}/status`);
      document.getElementById('progressFill').style.width = status.percent + '%';
      document.getElementById('progressText').textContent =
        `${status.progress} / ${status.total} (${status.percent}%)`;

      if (status.status === 'completed') {
        this._stopPolling();
        Utils.toast('Done! Downloading your labels…', 'success');
        this._showProgress(false);
        this._resetBtn();
        window.location.href = status.download_url;
      } else if (status.status === 'failed') {
        this._stopPolling();
        Utils.toast('Failed: ' + (status.error || 'Unknown error'), 'error');
        this._showProgress(false);
        this._resetBtn();
      } else if (status.status === 'cancelled') {
        this._stopPolling();
        Utils.toast('Generation cancelled', 'info');
        this._showProgress(false);
        this._resetBtn();
      }
    } catch (err) { /* network error, keep polling */ }
  },

  async cancelJob() {
    if (!this.currentJobId) return;
    try { await Utils.apiPost(`/api/job/${this.currentJobId}/cancel`, {}); } catch (e) {}
  },

  _showProgress(show) {
    document.getElementById('progressWrap').classList.toggle('active', show);
    document.getElementById('btnCancel').style.display = show ? 'inline-flex' : 'none';
    if (show) {
      document.getElementById('progressFill').style.width = '0%';
      document.getElementById('progressText').textContent = 'Starting…';
    }
  },

  _resetBtn() {
    const btn = document.getElementById('btnGenerate');
    btn.disabled = false;
    btn.innerHTML = '🖨️ Generate Labels';
  },

  _stopPolling() {
    if (this.pollInterval) { clearInterval(this.pollInterval); this.pollInterval = null; }
    this.currentJobId = null;
  },

  openSaveModal() { document.getElementById('saveTemplateModal').classList.add('active'); },
  closeSaveModal() { document.getElementById('saveTemplateModal').classList.remove('active'); },

  async saveTemplate() {
    const name = Utils.val('templateName').trim();
    if (!name) { Utils.toast('Name required', 'error'); return; }
    try {
      await Utils.apiPost('/api/templates', {
        name, description: Utils.val('templateDesc'),
        settings: Settings.getBarcodeSettings(), layout: Settings.getLayoutSettings(),
      });
      Utils.toast(`Template "${name}" saved!`, 'success');
      this.closeSaveModal();
      this.refreshTemplateList();
    } catch (err) { Utils.toast('Save failed: ' + err.message, 'error'); }
  },

  async loadTemplate(name) {
    try {
      const data = await Utils.apiGet(`/api/templates/${name.replace(/\s/g, '_')}`);
      Settings.applyTemplate(data);
      Utils.toast(`Template "${data.name}" loaded`, 'success');
      Preview.refresh();
    } catch (err) { Utils.toast('Load failed: ' + err.message, 'error'); }
  },

  async deleteTemplate() {
    const name = document.getElementById('templateSelect').value;
    if (!name) { Utils.toast('Select a template first', 'error'); return; }
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await Utils.apiDelete(`/api/templates/${name.replace(/\s/g, '_')}`);
      Utils.toast('Deleted', 'success');
      this.refreshTemplateList();
    } catch (err) { Utils.toast('Delete failed: ' + err.message, 'error'); }
  },

  async refreshTemplateList() {
    try {
      const data = await Utils.apiGet('/api/templates');
      const select = document.getElementById('templateSelect');
      select.innerHTML = '<option value="">Load Template…</option>';
      (data.templates || []).forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.name;
        opt.textContent = t.name + (t.description ? ` — ${t.description}` : '');
        select.appendChild(opt);
      });
    } catch (err) {}
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
