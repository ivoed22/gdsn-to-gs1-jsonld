// Bulk conversion workflow (Options API): convert many GDSN XML files (or a ZIP
// of them) client-side, show a per-file table + aggregate summary, and export a
// ZIP of the JSON-LD outputs plus a summary (CSV / xlsx).

import { store } from '../store.js';
import { createBrowserXPath, XMLParseError } from '../core/xml.js';
import { convertXmlToJsonld } from '../core/mapping.js';
import { jsonldString } from '../core/jsonld.js';
import { unzipTextEntries, zipFiles } from '../core/zip.js';
import { buildXlsx } from '../core/xlsx.js';
import { extractGtin, downloadBytes } from '../core/reports.js';
import { pushToast } from '../toast.js';
import { StatusBadge, FileDrop } from './shared.js';

const LIMITS = {
  maxFiles: 100,
  maxFileSize: 10 * 1024 * 1024,
  maxTotalSize: 100 * 1024 * 1024,
};

const SUMMARY_COLUMNS = ['file', 'status', 'gtin', 'validation', 'message'];

function validationStatus(report) {
  if (!report.valid) return 'errors';
  return report.warnings.length ? 'valid_with_warnings' : 'valid';
}

export const BulkWorkflow = {
  name: 'BulkWorkflow',
  components: { StatusBadge, FileDrop },
  data() {
    return {
      store,
      selectedProfileId: 'v0_5',
      results: [],
      errorMessage: '',
      busy: false,
    };
  },
  computed: {
    profiles() {
      return store.mappingProfiles;
    },
    activeProfile() {
      return store.mappingProfiles.find((p) => p.id === this.selectedProfileId);
    },
    summary() {
      const total = this.results.length;
      const success = this.results.filter((r) => r.status === 'success').length;
      return { total, success, failed: total - success };
    },
  },
  methods: {
    statusTone(status) {
      return status === 'success' ? 'success' : 'error';
    },
    async onFiles(files) {
      this.errorMessage = '';
      this.results = [];
      this.busy = true;
      try {
        const inputs = await this.collectInputs(files);
        if (inputs.error) {
          this.errorMessage = inputs.error;
          return;
        }
        this.runConversions(inputs.items);
        if (this.results.length) pushToast(`Converted ${this.summary.success}/${this.results.length} file(s).`, { tone: 'success' });
      } finally {
        this.busy = false;
      }
    },
    async collectInputs(files) {
      const items = [];
      let totalSize = 0;
      for (const file of files) {
        if (file.size > LIMITS.maxFileSize) {
          return { error: `${file.name} exceeds the ${LIMITS.maxFileSize / 1024 / 1024} MB per-file limit.` };
        }
        totalSize += file.size;
        if (file.name.toLowerCase().endsWith('.zip')) {
          const bytes = new Uint8Array(await file.arrayBuffer());
          let entries;
          try {
            entries = unzipTextEntries(bytes, ['.xml']);
          } catch (err) {
            return { error: `Could not read ${file.name}: ${err.message}` };
          }
          for (const entry of entries) items.push({ name: entry.name, text: entry.text });
        } else {
          items.push({ name: file.name, text: await file.text() });
        }
        if (items.length > LIMITS.maxFiles) {
          return { error: `More than ${LIMITS.maxFiles} files — reduce the batch.` };
        }
        if (totalSize > LIMITS.maxTotalSize) {
          return { error: `Total size exceeds the ${LIMITS.maxTotalSize / 1024 / 1024} MB limit.` };
        }
      }
      if (!items.length) return { error: 'No .xml files found in the selection.' };
      return { items };
    },
    runConversions(items) {
      const adapter = createBrowserXPath();
      const profile = this.activeProfile;
      const results = [];
      for (const item of items) {
        try {
          const result = convertXmlToJsonld(adapter, item.text, profile.config);
          results.push({
            name: item.name,
            status: 'success',
            gtin: extractGtin(result.jsonld_data) || 'unknown',
            validation: validationStatus(result.validation_report),
            message: '',
            jsonld: jsonldString(result.jsonld_data),
          });
        } catch (err) {
          results.push({
            name: item.name,
            status: 'error',
            gtin: '',
            validation: '',
            message: err instanceof XMLParseError ? err.message : String(err.message || err),
            jsonld: null,
          });
        }
      }
      this.results = results;
    },
    summaryRows() {
      return this.results.map((r) => [r.name, r.status, r.gtin, r.validation, r.message]);
    },
    buildOutputZip() {
      const files = {};
      const used = {};
      for (const r of this.results) {
        if (r.status !== 'success') continue;
        let base = `product_${r.gtin}`;
        used[base] = (used[base] || 0) + 1;
        if (used[base] > 1) base = `${base}_${used[base]}`;
        files[`${base}.jsonld`] = r.jsonld;
      }
      const csv = [SUMMARY_COLUMNS.join(',')]
        .concat(this.summaryRows().map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')))
        .join('\r\n');
      files['summary.csv'] = csv;
      return zipFiles(files);
    },
    downloadZip() {
      downloadBytes('bulk_conversion.zip', this.buildOutputZip(), 'application/zip');
    },
    downloadSummaryXlsx() {
      downloadBytes(
        'bulk_summary.xlsx',
        buildXlsx('Bulk summary', [SUMMARY_COLUMNS, ...this.summaryRows()]),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
    },
  },
  template: `
  <section class="workflow">
    <header class="workflow__head">
      <h2>Bulk conversion</h2>
      <p class="muted">Convert many GDSN XML files, or a ZIP of them, at once — all in your browser. Limits: {{ 100 }} files, 10 MB each, 100 MB total.</p>
    </header>

    <div class="card">
      <div class="field">
        <label class="field__label" for="bulk-profile">Mapping profile</label>
        <select id="bulk-profile" class="input" v-model="selectedProfileId">
          <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.label }}</option>
        </select>
      </div>
      <file-drop input-id="bulk-file" :multiple="true" accept=".xml,.zip"
        label="Drag & drop .xml files or a .zip, or click to choose" @files="onFiles" />
      <p class="alert alert--error" role="alert" v-if="errorMessage">{{ errorMessage }}</p>
      <p class="muted" v-if="busy">Converting…</p>
    </div>

    <template v-if="results.length">
      <div class="card">
        <h3 class="card__title">Summary</h3>
        <div class="statrow">
          <div class="stat"><span class="stat__num">{{ summary.total }}</span><span class="stat__label">files</span></div>
          <div class="stat"><span class="stat__num stat__num--ok">{{ summary.success }}</span><span class="stat__label">converted</span></div>
          <div class="stat"><span class="stat__num" :class="{ 'stat__num--err': summary.failed }">{{ summary.failed }}</span><span class="stat__label">failed</span></div>
        </div>
        <div class="btn-row">
          <button class="btn btn--primary" type="button" @click="downloadZip"><app-icon name="download" :size="16" /> Download ZIP (JSON-LD + summary)</button>
          <button class="btn" type="button" @click="downloadSummaryXlsx"><app-icon name="download" :size="16" /> Summary (xlsx)</button>
        </div>
      </div>

      <div class="card">
        <h3 class="card__title">Per-file results</h3>
        <div class="table-scroll">
          <table class="table">
            <thead><tr><th>File</th><th>Status</th><th>GTIN</th><th>Validation</th><th>Message</th></tr></thead>
            <tbody>
              <tr v-for="(r, i) in results" :key="i">
                <td>{{ r.name }}</td>
                <td><status-badge :label="r.status" :tone="statusTone(r.status)" /></td>
                <td>{{ r.gtin || '—' }}</td>
                <td>{{ r.validation || '—' }}</td>
                <td class="cell--value">{{ r.message || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </section>
  `,
};
