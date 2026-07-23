// Convert GDSN XML → GS1 JSON-LD workflow (Options API).

import { store, loadSampleText, governedTerms } from '../store.js';
import { createBrowserXPath, XMLParseError } from '../core/xml.js';
import { convertXmlToJsonld } from '../core/mapping.js';
import { jsonldString } from '../core/jsonld.js';
import { assessReadiness } from '../core/readiness.js';
import { buildTermSets, checkJsonld } from '../core/jsonld_check.js';
import {
  DIGITAL_LINK_CAVEAT,
  DigitalLinkError,
  buildDigitalLinkUri,
  digitalLinkQrSvg,
} from '../core/digitallink.js';
import {
  jsonString,
  mappingReportCsv,
  mappingReportXlsx,
  buildProductReportHtml,
  extractGtin,
  extractProductName,
  downloadText,
  downloadBytes,
} from '../core/reports.js';
import { pushToast } from '../toast.js';
import { StatusBadge, JsonTree, FileDrop } from './shared.js';

const READINESS_LABELS = {
  structurally_ready: 'Structurally ready',
  attention_points: 'Attention points',
  review_required: 'Review required',
};
const READINESS_TONES = {
  structurally_ready: 'success',
  attention_points: 'warning',
  review_required: 'error',
};
const DIMENSION_LABELS = {
  structural_validation: 'Structural validation',
  mapping_coverage: 'Mapping coverage',
  codelist_conformance: 'Codelist conformance',
  dpp_relevance: 'DPP relevance',
};
const CONSENSUS_LABELS = {
  unanimous_accept: 'Unanimous AI acceptance',
  strong_accept_consensus: 'Strong AI consensus',
  accept_consensus: 'AI acceptance consensus',
  conflicted: 'Conflicting reviews',
  human_review: 'Human review required',
  no_equivalent_consensus: 'No-equivalent consensus',
  insufficient_review: 'Insufficient review',
};
const CONSENSUS_SHARES = {
  unanimous_accept: '15.3% of catalog',
  strong_accept_consensus: '21.2% of catalog',
  accept_consensus: '8.3% of catalog',
  human_review: '39.2% of catalog',
  conflicted: '16.0% of catalog',
};

export const ConvertWorkflow = {
  name: 'ConvertWorkflow',
  components: { StatusBadge, JsonTree, FileDrop },
  data() {
    return {
      store,
      xmlText: '',
      fileName: '',
      selectedSample: '',
      selectedProfileId: 'v0_5',
      result: null,
      convertedProfileLabel: '',
      errorMessage: '',
      qrSvg: '',
      digitalLinkUri: '',
      digitalLinkCaveat: DIGITAL_LINK_CAVEAT,
      dimensionLabels: DIMENSION_LABELS,
      highlightRowId: '',
    };
  },
  computed: {
    profiles() {
      return store.mappingProfiles;
    },
    activeProfile() {
      return store.mappingProfiles.find((profile) => profile.id === this.selectedProfileId);
    },
    profileTargets() {
      if (!this.activeProfile) return [];
      const cfg = this.activeProfile.config;
      const terms = [];
      for (const f of cfg.fields || []) terms.push(f.jsonld_property);
      for (const om of cfg.object_mappings || []) terms.push(om.jsonld_property);
      return [...new Set(terms)];
    },
    identity() {
      if (!this.result) return null;
      const data = this.result.jsonld_data;
      return {
        gtin: extractGtin(data) || '—',
        name: extractProductName(data) || '—',
        id: data['@id'] || '—',
      };
    },
    readiness() {
      if (!this.result) return null;
      return assessReadiness(this.result);
    },
    readinessLabel() {
      return this.readiness ? READINESS_LABELS[this.readiness.readiness_level] : '';
    },
    readinessTone() {
      return this.readiness ? READINESS_TONES[this.readiness.readiness_level] : 'neutral';
    },
    mappingRows() {
      return this.result ? this.result.mapping_report_rows : [];
    },
    unmappedElements() {
      return this.result ? this.result.unmapped_fields.unmapped_elements : [];
    },
    mappingSuggestions() {
      return this.result ? this.result.unmapped_fields.mapping_suggestions || [] : [];
    },
    strongSuggestionCount() {
      return this.mappingSuggestions.filter((item) => Number(item.match_percentage) >= 90).length;
    },
    reviewSuggestionCount() {
      return this.mappingSuggestions.length - this.strongSuggestionCount;
    },
    reviewCandidateNodeCount() {
      if (!this.result) return 0;
      const value = this.result.jsonld_data['schema:additionalProperty'];
      if (value == null) return 0;
      return Array.isArray(value) ? value.length : 1;
    },
    termCheck() {
      if (!this.result) return null;
      const sets = buildTermSets(store.webvocProperties, store.webvocClasses, governedTerms());
      return checkJsonld(this.result.jsonld_data, sets);
    },
    highlightSet() {
      const ids =
        this.result && this.highlightRowId
          ? this.result.trace.row_source_ids[this.highlightRowId] || []
          : [];
      return new Set(ids);
    },
  },
  methods: {
    rowTone(status) {
      if (status === 'mapped') return 'success';
      if (status === 'missing_required' || status === 'validation_error' || status === 'transform_error') {
        return 'error';
      }
      if (status === 'missing_optional') return 'neutral';
      return 'warning';
    },
    displayValue(value) {
      if (value == null) return '—';
      if (typeof value === 'object') return JSON.stringify(value);
      return String(value);
    },
    consensusLabel(status) {
      return CONSENSUS_LABELS[status] || 'Human review required';
    },
    consensusShare(status) {
      return CONSENSUS_SHARES[status] || '';
    },
    isVocabTerm(prop) {
      return typeof prop === 'string' && (prop.startsWith('gs1:') || prop.startsWith('schema:'));
    },
    goExplore(term) {
      location.hash = `#/explore?term=${encodeURIComponent(term)}`;
    },
    async onFiles(files) {
      const file = files[0];
      if (!file) return;
      this.fileName = file.name;
      this.selectedSample = '';
      this.xmlText = await file.text();
    },
    async trySample() {
      this.selectedSample = 'example';
      await this.onSampleChange();
      this.convert();
    },
    jump(id) {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },
    async onSampleChange() {
      if (!this.selectedSample) return;
      const sample = store.samples.find((item) => item.id === this.selectedSample);
      if (!sample) return;
      try {
        this.xmlText = await loadSampleText(sample.file);
        this.fileName = sample.file.split('/').pop();
      } catch (err) {
        this.errorMessage = err.message;
      }
    },
    convert() {
      this.errorMessage = '';
      this.result = null;
      this.qrSvg = '';
      this.digitalLinkUri = '';
      this.highlightRowId = '';
      if (!this.xmlText.trim()) {
        this.errorMessage = 'Provide GDSN XML (paste, upload, or load a sample) first.';
        return;
      }
      const profile = this.activeProfile;
      if (!profile) {
        this.errorMessage = 'Select a mapping profile.';
        return;
      }
      try {
        const adapter = createBrowserXPath();
        this.result = convertXmlToJsonld(
          adapter,
          this.xmlText,
          profile.config,
          store.mappingSuggestions
        );
        this.convertedProfileLabel = profile.label;
        store.lastConversion = {
          jsonld_data: this.result.jsonld_data,
          profileLabel: profile.label,
        };
        this.buildDigitalLink();
        pushToast('Conversion complete.', { tone: 'success' });
        this.$nextTick(() => {
          const el = document.getElementById('convert-results');
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      } catch (err) {
        if (err instanceof XMLParseError) {
          this.errorMessage = err.message;
        } else {
          this.errorMessage = `Conversion failed: ${err.message}`;
        }
      }
    },
    buildDigitalLink() {
      const gtin = extractGtin(this.result.jsonld_data);
      if (!gtin) return;
      try {
        this.digitalLinkUri = buildDigitalLinkUri(gtin);
        this.qrSvg = digitalLinkQrSvg(this.digitalLinkUri);
      } catch (err) {
        if (!(err instanceof DigitalLinkError)) throw err;
        this.digitalLinkUri = '';
        this.qrSvg = '';
      }
    },
    highlightRow(rowId) {
      this.highlightRowId = this.highlightRowId === rowId ? '' : rowId;
      if (!this.highlightRowId) return;
      this.$nextTick(() => {
        const ids = this.result.trace.row_source_ids[rowId] || [];
        if (!ids.length) return;
        const el = document.querySelector(`#source-tree [data-xmlid="${ids[0]}"]`);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    },
    gtinForFile() {
      return extractGtin(this.result.jsonld_data) || 'unknown';
    },
    downloadJsonld() {
      downloadText(`product_${this.gtinForFile()}.jsonld`, jsonldString(this.result.jsonld_data), 'application/ld+json');
    },
    downloadMappingCsv() {
      downloadText(`mapping_report_${this.gtinForFile()}.csv`, mappingReportCsv(this.result.mapping_report_rows), 'text/csv');
    },
    downloadMappingXlsx() {
      downloadBytes(
        `mapping_report_${this.gtinForFile()}.xlsx`,
        mappingReportXlsx(this.result.mapping_report_rows),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
    },
    downloadValidation() {
      downloadText(`validation_report_${this.gtinForFile()}.json`, jsonString(this.result.validation_report), 'application/json');
    },
    downloadUnmapped() {
      downloadText(`unmapped_fields_${this.gtinForFile()}.json`, jsonString(this.result.unmapped_fields), 'application/json');
    },
    downloadReport() {
      downloadText(`product_report_${this.gtinForFile()}.html`, buildProductReportHtml(this.result), 'text/html');
    },
  },
  template: `
  <section class="workflow">
    <header class="workflow__head">
      <h2>Convert GDSN XML</h2>
      <p class="muted">Upload → Mapping → Validate → Export. XML is parsed and converted entirely in your browser — nothing is uploaded.</p>
    </header>

    <div class="hero" v-if="!result">
      <span class="hero__eyebrow"><app-icon name="sparkles" :size="15" /> GDSN → GS1 Web Vocabulary</span>
      <h3 class="hero__title">Turn a GDSN product message into traceable GS1 JSON-LD.</h3>
      <p class="hero__sub">Byte-for-byte faithful to the reference converter, fully offline. Every field traces back to its source XML element, and nothing you drop here leaves the browser.</p>
      <div class="btn-row">
        <button class="btn btn--primary" type="button" @click="trySample"><app-icon name="sparkles" :size="16" /> Try the sample</button>
      </div>
    </div>

    <div class="grid grid--two">
      <div class="card">
        <h3 class="card__title">1 · Provide GDSN XML</h3>
        <div class="field">
          <label class="field__label" for="sample-select">Load a bundled sample</label>
          <select id="sample-select" class="input" v-model="selectedSample" @change="onSampleChange">
            <option value="">— choose a sample —</option>
            <option v-for="s in store.samples" :key="s.id" :value="s.id">{{ s.label }}</option>
          </select>
        </div>
        <div class="field">
          <span class="field__label">…or drop / choose a file</span>
          <file-drop input-id="convert-file" accept=".xml,text/xml,application/xml" @files="onFiles"
            label="Drag & drop a .xml file, or click to choose" />
        </div>
        <div class="field">
          <label class="field__label" for="xml-text">…or paste XML <span v-if="fileName" class="muted">({{ fileName }})</span></label>
          <textarea id="xml-text" class="input input--mono" rows="7" v-model="xmlText"
            placeholder="&lt;catalogueItemNotificationMessage&gt;…"></textarea>
        </div>
      </div>

      <div class="card">
        <h3 class="card__title">2 · Mapping profile</h3>
        <p class="muted">The mapping profile is the data-driven contract that maps GDSN XPaths to GS1 Web Vocabulary properties.</p>
        <div class="field">
          <label class="field__label" for="profile-select">Profile</label>
          <select id="profile-select" class="input" v-model="selectedProfileId">
            <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.label }}</option>
          </select>
        </div>
        <p class="muted" v-if="activeProfile">
          {{ activeProfile.config.fields.length }} scalar field(s),
          {{ (activeProfile.config.object_mappings || []).length }} object mapping(s).
        </p>
        <div class="field" v-if="profileTargets.length">
          <span class="field__label">Maps to</span>
          <div class="chips">
            <code class="chip" v-for="term in profileTargets" :key="term">{{ term }}</code>
          </div>
        </div>
        <button class="btn btn--primary" type="button" @click="convert"><app-icon name="convert" :size="16" /> Convert</button>
        <p class="alert alert--error" role="alert" v-if="errorMessage">{{ errorMessage }}</p>
      </div>
    </div>

    <div id="convert-results"></div>
    <div v-if="result" class="reveal">
      <div class="jumpbar result-section--nav">
        <button class="jumpbar__item" type="button" @click="jump('sec-downloads')">Downloads</button>
        <button class="jumpbar__item" type="button" @click="jump('sec-output')">Output</button>
        <button class="jumpbar__item" type="button" @click="jump('sec-checks')">Checks</button>
        <button class="jumpbar__item" v-if="mappingSuggestions.length" type="button" @click="jump('sec-suggestions')">Suggestions</button>
        <button class="jumpbar__item" type="button" @click="jump('sec-trace')">Traceability</button>
        <button class="jumpbar__item" type="button" @click="jump('sec-report')">Report</button>
      </div>
      <div class="card result-section--identity" v-if="identity">
        <div class="card__row">
          <h3 class="card__title">Product identity</h3>
        </div>
        <div class="identity">
          <div><span class="muted">Name</span><strong>{{ identity.name }}</strong></div>
          <div><span class="muted">GTIN</span><strong>{{ identity.gtin }}</strong></div>
          <div><span class="muted">@id</span><code>{{ identity.id }}</code></div>
          <div><span class="muted">Profile</span><span>{{ convertedProfileLabel }}</span></div>
        </div>
      </div>

      <div id="sec-checks" class="grid grid--two result-section--checks">
        <div class="card">
          <h3 class="card__title">Validation</h3>
          <p><status-badge :label="result.validation_report.valid ? 'Valid' : 'Errors present'" :tone="result.validation_report.valid ? 'success' : 'error'" /></p>
          <template v-if="result.validation_report.errors.length">
            <h4 class="subhead">Errors</h4>
            <ul class="list list--error" role="alert"><li v-for="(e, i) in result.validation_report.errors" :key="'e'+i">{{ e }}</li></ul>
          </template>
          <template v-if="result.validation_report.warnings.length">
            <h4 class="subhead">Warnings</h4>
            <ul class="list list--warning"><li v-for="(w, i) in result.validation_report.warnings" :key="'w'+i">{{ w }}</li></ul>
          </template>
          <p class="muted" v-if="!result.validation_report.errors.length && !result.validation_report.warnings.length">No errors or warnings.</p>
        </div>

        <div class="card">
          <h3 class="card__title">DPP readiness</h3>
          <p><status-badge :label="readinessLabel" :tone="readinessTone" /></p>
          <table class="table table--compact">
            <tbody>
              <tr v-for="(dim, key) in readiness.dimensions" :key="key">
                <th scope="row">{{ dimensionLabels[key] }}</th><td><code>{{ dim.status }}</code></td>
              </tr>
            </tbody>
          </table>
          <p class="muted note">{{ readiness.scope_note }}</p>
        </div>
      </div>

      <div class="card result-section--digital-link" v-if="digitalLinkUri">
        <h3 class="card__title">GS1 Digital Link</h3>
        <div class="digitallink">
          <div class="digitallink__qr" v-html="qrSvg"></div>
          <div><p><code>{{ digitalLinkUri }}</code></p><p class="muted note">{{ digitalLinkCaveat }}</p></div>
        </div>
      </div>

      <div id="sec-output" class="card result-section--output">
        <div class="card__row">
          <h3 class="card__title">Generated GS1 Web Vocabulary JSON-LD</h3>
          <status-badge v-if="termCheck" :label="termCheck.ok ? 'Terms resolve' : termCheck.issues.length + ' unknown term(s)'" :tone="termCheck.ok ? 'success' : 'warning'" />
        </div>
        <p class="alert alert--warning" v-if="reviewCandidateNodeCount">
          This JSON-LD contains {{ reviewCandidateNodeCount }} removable review-candidate node(s) under
          <code>schema:additionalProperty</code>. Their proposed GS1 properties are recorded as text and are not asserted mappings.
        </p>
        <json-tree :value="result.jsonld_data" />
        <details class="details" v-if="termCheck">
          <summary>Structural term check</summary>
          <p class="muted note">{{ termCheck.note }}</p>
          <p class="muted note">Checked {{ termCheck.checked_properties }} propertie(s), {{ termCheck.checked_types }} type(s). External (schema.org, not checked): {{ termCheck.external.length }}.</p>
          <ul class="list" v-if="termCheck.issues.length"><li v-for="(iss, i) in termCheck.issues" :key="i"><code>{{ iss.term }}</code> — {{ iss.kind }} at <code>{{ iss.path }}</code></li></ul>
        </details>
      </div>

      <div id="sec-trace" class="card result-section--trace">
        <h3 class="card__title">Traceability — mapping ↔ source XML</h3>
        <p class="muted note">Select a mapping row to highlight the source element(s) it came from.</p>
        <div class="grid grid--two trace">
          <div class="table-scroll">
            <table class="table">
              <thead><tr><th>Field</th><th>JSON-LD property</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="row in mappingRows" :key="row.id"
                  class="trace__row" :class="{ 'trace__row--active': highlightRowId === row.id }"
                  @click="highlightRow(row.id)">
                  <td><strong>{{ row.id }}</strong></td>
                  <td>
                    <code>{{ row.jsonld_property }}</code>
                    <button v-if="isVocabTerm(row.jsonld_property)" class="linkbtn" type="button"
                      @click.stop="goExplore(row.jsonld_property)" title="View in Explore">↗</button>
                  </td>
                  <td><status-badge :label="row.status" :tone="rowTone(row.status)" /></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div id="source-tree" class="card--nested xmltree">
            <xml-tree-node :node="result.trace.tree" :highlight="highlightSet" />
          </div>
        </div>
      </div>

      <div id="sec-report" class="card result-section--report">
        <h3 class="card__title">Mapping report</h3>
        <div class="table-scroll">
          <table class="table">
            <thead><tr><th>Field</th><th>JSON-LD property</th><th>Status</th><th>Value</th></tr></thead>
            <tbody>
              <tr v-for="row in mappingRows" :key="row.id">
                <td><strong>{{ row.id }}</strong><br /><span class="muted">{{ row.description }}</span></td>
                <td><code>{{ row.jsonld_property }}</code></td>
                <td><status-badge :label="row.status" :tone="rowTone(row.status)" /></td>
                <td class="cell--value">{{ displayValue(row.value) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card result-section--unmapped">
        <h3 class="card__title">Unmapped source elements ({{ unmappedElements.length }})</h3>
        <p class="muted" v-if="!unmappedElements.length">Every populated source element was covered by the profile.</p>
        <div class="table-scroll" v-else>
          <table class="table table--unmapped">
            <colgroup><col class="col--element" /><col class="col--parent" /><col class="col--path" /><col class="col--count" /><col class="col--context" /></colgroup>
            <thead><tr><th>Element</th><th>Parent</th><th>Path</th><th>Count</th><th>Context</th></tr></thead>
            <tbody>
              <tr v-for="(u, i) in unmappedElements" :key="i">
                <td><code>{{ u.element }}</code></td>
                <td>{{ u.parent || '—' }}</td>
                <td class="cell--path"><code>{{ u.path }}</code></td>
                <td>{{ u.count }}</td>
                <td>{{ u.context ? JSON.stringify(u.context) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div id="sec-suggestions" class="card result-section--suggestions" v-if="mappingSuggestions.length">
        <div class="card__row">
          <h3 class="card__title">Possible mappings for this upload ({{ mappingSuggestions.length }})</h3>
          <status-badge label="Review required" tone="warning" />
        </div>
        <p class="alert alert--warning">
          Similarity-based suggestions are included only as removable <code>schema:PropertyValue</code> review evidence.
          The proposed GS1 property is not asserted. Verify semantics, domain, range, structure and codelists before promotion.
        </p>
        <div class="metrics metrics--two">
          <div class="metric"><span>Strong candidates (90%+)</span><strong>{{ strongSuggestionCount }}</strong></div>
          <div class="metric"><span>Review candidates (60–&lt;90%)</span><strong>{{ reviewSuggestionCount }}</strong></div>
        </div>
        <div class="table-scroll">
          <table class="table">
            <thead><tr><th>Source field</th><th>Possible WebVoc property</th><th>Match</th><th>AI review consensus</th><th>Status</th></tr></thead>
            <tbody>
              <tr v-for="(item, i) in mappingSuggestions" :key="i">
                <td><code>{{ item.source_element }}</code><br /><span class="muted">{{ item.gdsn_attribute_name }}</span></td>
                <td><code>{{ item.proposed_webvoc_property }}</code><br /><span class="muted">{{ item.proposed_webvoc_label }}</span></td>
                <td><strong>{{ Number(item.match_percentage).toFixed(1) }}%</strong></td>
                <td>{{ consensusLabel(item.review_consensus_status) }}<br /><span class="muted">{{ consensusShare(item.review_consensus_status) }} · {{ item.accept_count || 0 }} accept vote(s)</span></td>
                <td>{{ Number(item.match_percentage) >= 90 ? 'Strong candidate — review required' : 'Possible match — review required' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="muted note">Score reasons and alternative candidates are included in the Unmapped fields JSON download.</p>
      </div>

      <div id="sec-downloads" class="card result-section--downloads">
        <h3 class="card__title">Downloads</h3>
        <div class="btn-row">
          <button class="btn" type="button" @click="downloadJsonld"><app-icon name="download" :size="16" /> JSON-LD</button>
          <button class="btn" type="button" @click="downloadMappingCsv"><app-icon name="download" :size="16" /> Mapping report (CSV)</button>
          <button class="btn" type="button" @click="downloadMappingXlsx"><app-icon name="download" :size="16" /> Mapping report (xlsx)</button>
          <button class="btn" type="button" @click="downloadValidation"><app-icon name="download" :size="16" /> Validation (JSON)</button>
          <button class="btn" type="button" @click="downloadUnmapped"><app-icon name="download" :size="16" /> Unmapped fields (JSON)</button>
          <button class="btn" type="button" @click="downloadReport"><app-icon name="file" :size="16" /> HTML product report</button>
        </div>
      </div>
    </div>
  </section>
  `,
};
