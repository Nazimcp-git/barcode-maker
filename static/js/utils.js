/**
 * Utility functions: API wrapper, toast notifications, debounce, helpers.
 */
const Utils = {
  /**
   * Debounce a function call.
   */
  debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  },

  /**
   * Fetch wrapper with JSON error handling.
   */
  async apiPost(url, data, isFormData = false) {
    try {
      const options = { method: 'POST' };
      if (isFormData) {
        options.body = data;
      } else {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(data);
      }
      const res = await fetch(url, options);
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
      return json;
    } catch (err) {
      throw err;
    }
  },

  async apiGet(url) {
    try {
      const res = await fetch(url);
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
      return json;
    } catch (err) {
      throw err;
    }
  },

  async apiDelete(url) {
    try {
      const res = await fetch(url, { method: 'DELETE' });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
      return json;
    } catch (err) {
      throw err;
    }
  },

  /**
   * Show a toast notification.
   */
  toast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  /**
   * Format file size.
   */
  formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  },

  /**
   * Get value from input element.
   */
  val(id) {
    const el = document.getElementById(id);
    if (!el) return '';
    if (el.type === 'number') return parseFloat(el.value) || 0;
    return el.value;
  },

  /**
   * Set value on input element.
   */
  setVal(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
  },

  /**
   * Calculate total items based on current input mode.
   */
  calcTotalItems() {
    const mode = DataInput.currentMode;
    if (mode === 'range') {
      const start = Utils.val('rangeStart');
      const end = Utils.val('rangeEnd');
      const step = Utils.val('rangeStep') || 1;
      if (end < start || step <= 0) return 0;
      return Math.floor((end - start) / step) + 1;
    } else if (mode === 'text') {
      const text = Utils.val('textInput');
      if (!text.trim()) return 0;
      return text.trim().split('\n').filter(l => l.trim()).length;
    } else if (mode === 'file') {
      return DataInput.fileRowCount || 0;
    }
    return 0;
  },

  /**
   * Update all count displays.
   */
  updateCounts() {
    const total = Utils.calcTotalItems();
    document.getElementById('totalCount').textContent = total.toLocaleString();
    document.getElementById('bottomCount').textContent = total.toLocaleString();
    document.getElementById('summaryItems').textContent = total.toLocaleString();

    const cols = Utils.val('gridColumns') || 4;
    const rows = Utils.val('gridRows') || 5;
    const perPage = cols * rows;
    const pages = Math.max(1, Math.ceil(total / perPage));

    document.getElementById('summaryGrid').textContent = `${cols} × ${rows}`;
    document.getElementById('summaryPerPage').textContent = perPage;
    document.getElementById('summaryPages').textContent = pages;
  }
};
