/**
 * Settings panel logic for Library Barcode Label Generator.
 */
const Settings = {
  init() {
    // Color picker sync
    this._syncColor('fgColor', 'fgColorHex');
    this._syncColor('bgColor', 'bgColorHex');

    // Custom page size toggle
    document.getElementById('pageSize').addEventListener('change', (e) => {
      document.getElementById('customPageSize').style.display =
        e.target.value === 'Custom' ? 'block' : 'none';
    });

    // Auto-grid button
    document.getElementById('btnAutoGrid').addEventListener('click', () => {
      this.autoCalculateGrid();
    });

    // Toggle switches
    this._initToggle('showBarcodeText');
    this._initToggle('showValueText');
    this._initToggle('labelBorderToggle');

    // Listen for changes to update counts
    const updateInputs = [
      'rangeStart', 'rangeEnd', 'rangeStep', 'gridColumns', 'gridRows',
      'labelWidth', 'labelHeight', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight',
      'gapH', 'gapV', 'pageSize', 'pageOrientation'
    ];
    updateInputs.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', Utils.debounce(() => Utils.updateCounts(), 200));
    });

    const textInput = document.getElementById('textInput');
    if (textInput) {
      textInput.addEventListener('input', Utils.debounce(() => Utils.updateCounts(), 300));
    }
  },

  _syncColor(pickerId, hexId) {
    const picker = document.getElementById(pickerId);
    const hex = document.getElementById(hexId);
    if (!picker || !hex) return;
    picker.addEventListener('input', () => { hex.value = picker.value; });
    hex.addEventListener('input', () => {
      if (/^#[0-9A-Fa-f]{6}$/.test(hex.value)) picker.value = hex.value;
    });
  },

  _initToggle(id) {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('click', function () {
        this.classList.toggle('active');
      });
    }
  },

  autoCalculateGrid() {
    const pageSize = Utils.val('pageSize');
    const orientation = Utils.val('pageOrientation');
    let pageW, pageH;

    const sizes = { A4: [210, 297], A5: [148, 210], Letter: [215.9, 279.4], Legal: [215.9, 355.6] };
    if (pageSize === 'Custom') {
      pageW = Utils.val('customPageW');
      pageH = Utils.val('customPageH');
    } else {
      [pageW, pageH] = sizes[pageSize] || [210, 297];
    }
    if (orientation === 'landscape') [pageW, pageH] = [pageH, pageW];

    const mT = Utils.val('marginTop'), mB = Utils.val('marginBottom');
    const mL = Utils.val('marginLeft'), mR = Utils.val('marginRight');
    const lW = Utils.val('labelWidth'), lH = Utils.val('labelHeight');
    const gH = Utils.val('gapH'), gV = Utils.val('gapV');

    const availW = pageW - mL - mR;
    const availH = pageH - mT - mB;

    const cols = Math.max(1, Math.floor((availW + gH) / (lW + gH)));
    const rows = Math.max(1, Math.floor((availH + gV) / (lH + gV)));

    Utils.setVal('gridColumns', cols);
    Utils.setVal('gridRows', rows);
    Utils.updateCounts();
    Utils.toast(`Grid: ${cols} × ${rows} = ${cols * rows} labels per page`, 'success');
  },

  getBarcodeSettings() {
    return {
      barcode_type: Utils.val('barcodeType'),
      module_height: Utils.val('moduleHeight'),
      module_width: Utils.val('moduleWidth'),
      quiet_zone: Utils.val('quietZone'),
      text_distance: Utils.val('textDistance'),
      barcode_font_size: Utils.val('barcodeFontSize'),
      show_barcode_text: document.getElementById('showBarcodeText').classList.contains('active'),
      fg_color: Utils.val('fgColor'),
      bg_color: Utils.val('bgColor'),
      // Label text settings
      library_name: Utils.val('libraryName'),
      show_value_text: document.getElementById('showValueText').classList.contains('active'),
      accession_label: Utils.val('accessionLabel'),
      call_number_text: Utils.val('callNumber'),
      header_font_size: Utils.val('headerFontSize'),
      value_font_size: Utils.val('valueFontSize'),
      text_alignment: Utils.val('textAlignment'),
      label_border: document.getElementById('labelBorderToggle').classList.contains('active'),
      // Label dimensions (used in barcode_generator)
      label_width_mm: Utils.val('labelWidth'),
      label_height_mm: Utils.val('labelHeight'),
    };
  },

  getLayoutSettings() {
    return {
      page_size: Utils.val('pageSize'),
      custom_width_mm: Utils.val('customPageW'),
      custom_height_mm: Utils.val('customPageH'),
      orientation: Utils.val('pageOrientation'),
      margin_top_mm: Utils.val('marginTop'),
      margin_bottom_mm: Utils.val('marginBottom'),
      margin_left_mm: Utils.val('marginLeft'),
      margin_right_mm: Utils.val('marginRight'),
      label_width_mm: Utils.val('labelWidth'),
      label_height_mm: Utils.val('labelHeight'),
      gap_h_mm: Utils.val('gapH'),
      gap_v_mm: Utils.val('gapV'),
      columns: Utils.val('gridColumns'),
      rows: Utils.val('gridRows'),
    };
  },

  applyTemplate(data) {
    const s = data.settings || {};
    const l = data.layout || {};

    if (s.barcode_type) Utils.setVal('barcodeType', s.barcode_type);
    if (s.module_height) Utils.setVal('moduleHeight', s.module_height);
    if (s.module_width) Utils.setVal('moduleWidth', s.module_width);
    if (s.quiet_zone !== undefined) Utils.setVal('quietZone', s.quiet_zone);
    if (s.text_distance !== undefined) Utils.setVal('textDistance', s.text_distance);
    if (s.fg_color) { Utils.setVal('fgColor', s.fg_color); Utils.setVal('fgColorHex', s.fg_color); }
    if (s.bg_color) { Utils.setVal('bgColor', s.bg_color); Utils.setVal('bgColorHex', s.bg_color); }
    if (s.library_name !== undefined) Utils.setVal('libraryName', s.library_name);
    if (s.accession_label) Utils.setVal('accessionLabel', s.accession_label);
    if (s.call_number_text !== undefined) Utils.setVal('callNumber', s.call_number_text);

    if (l.page_size) Utils.setVal('pageSize', l.page_size);
    if (l.orientation) Utils.setVal('pageOrientation', l.orientation);
    if (l.margin_top_mm !== undefined) Utils.setVal('marginTop', l.margin_top_mm);
    if (l.margin_bottom_mm !== undefined) Utils.setVal('marginBottom', l.margin_bottom_mm);
    if (l.margin_left_mm !== undefined) Utils.setVal('marginLeft', l.margin_left_mm);
    if (l.margin_right_mm !== undefined) Utils.setVal('marginRight', l.margin_right_mm);
    if (l.label_width_mm) Utils.setVal('labelWidth', l.label_width_mm);
    if (l.label_height_mm) Utils.setVal('labelHeight', l.label_height_mm);
    if (l.gap_h_mm !== undefined) Utils.setVal('gapH', l.gap_h_mm);
    if (l.gap_v_mm !== undefined) Utils.setVal('gapV', l.gap_v_mm);
    if (l.columns) Utils.setVal('gridColumns', l.columns);
    if (l.rows) Utils.setVal('gridRows', l.rows);

    document.getElementById('customPageSize').style.display =
      l.page_size === 'Custom' ? 'block' : 'none';

    Utils.updateCounts();
  }
};
