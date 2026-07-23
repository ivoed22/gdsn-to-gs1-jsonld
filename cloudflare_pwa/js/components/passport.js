// Product Passport workflow (Options API): wrap GS1 JSON-LD into a prototype
// Product Passport envelope and structurally validate it. Prototype/reference
// only — not official GS1 validation, not EU DPP compliance.

import { store, loadPassportSchema } from '../store.js';
import {
  PROTOTYPE_NOTICE,
  buildMinimalProductPassport,
  validateProductPassport,
} from '../core/passport.js';
import { jsonldString } from '../core/jsonld.js';
import { extractGtin, downloadText, jsonString } from '../core/reports.js';
import { pushToast } from '../toast.js';
import { StatusBadge, JsonTree } from './shared.js';

export const PassportWorkflow = {
  name: 'PassportWorkflow',
  components: { StatusBadge, JsonTree },
  data() {
    return {
      store,
      prototypeNotice: PROTOTYPE_NOTICE,
      inputText: '',
      envelope: null,
      report: null,
      errorMessage: '',
    };
  },
  computed: {
    hasHandoff() {
      return !!store.lastConversion;
    },
  },
  methods: {
    useLastConversion() {
      if (!store.lastConversion) return;
      this.inputText = jsonldString(store.lastConversion.jsonld_data);
      this.build();
    },
    parseInput() {
      const text = this.inputText.trim();
      if (!text) throw new Error('Provide GS1 JSON-LD (use the last conversion, paste, or upload).');
      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch (err) {
        throw new Error(`Input is not valid JSON: ${err.message}`);
      }
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('GS1 JSON-LD input must be a JSON object.');
      }
      return parsed;
    },
    async build() {
      this.errorMessage = '';
      this.envelope = null;
      this.report = null;
      try {
        const gs1 = this.parseInput();
        this.envelope = buildMinimalProductPassport(gs1);
        const schema = await loadPassportSchema();
        this.report = validateProductPassport(this.envelope, schema);
        pushToast('Passport built.', { tone: 'success' });
      } catch (err) {
        this.errorMessage = err.message;
      }
    },
    async onFiles(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      this.inputText = await file.text();
      event.target.value = '';
      this.build();
    },
    gtinForFile() {
      return (this.envelope && extractGtin(this.envelope)) || 'unknown';
    },
    downloadEnvelope() {
      downloadText(`product_passport_${this.gtinForFile()}.jsonld`, jsonldString(this.envelope), 'application/ld+json');
    },
    downloadReport() {
      downloadText(`passport_validation_${this.gtinForFile()}.json`, jsonString(this.report), 'application/json');
    },
  },
  template: `
  <section class="workflow">
    <header class="workflow__head">
      <h2>Product Passport (prototype)</h2>
      <p class="muted">Wrap GS1 Web Vocabulary JSON-LD into a prototype Product Passport envelope and structurally validate it.</p>
    </header>

    <p class="alert alert--warning">{{ prototypeNotice }}</p>

    <div class="card">
      <h3 class="card__title">Input</h3>
      <div class="btn-row" v-if="hasHandoff">
        <button class="btn btn--primary" type="button" @click="useLastConversion">Use last conversion ({{ store.lastConversion.profileLabel }})</button>
      </div>
      <div class="field">
        <label class="field__label" for="passport-file">Upload GS1 JSON-LD</label>
        <input id="passport-file" class="input" type="file" accept=".json,.jsonld,application/json" @change="onFiles" />
      </div>
      <div class="field">
        <label class="field__label" for="passport-text">…or paste GS1 JSON-LD</label>
        <textarea id="passport-text" class="input input--mono" rows="7" v-model="inputText" placeholder='{ "@context": …, "@type": "gs1:Product", … }'></textarea>
      </div>
      <button class="btn btn--primary" type="button" @click="build">Build passport →</button>
      <p class="alert alert--error" role="alert" v-if="errorMessage">{{ errorMessage }}</p>
    </div>

    <template v-if="envelope">
      <div class="card" v-if="report">
        <h3 class="card__title">Structural validation</h3>
        <p><status-badge :label="report.validation_status" :tone="report.validation_status === 'valid' ? 'success' : 'error'" /> <span class="muted">against {{ report.schema_file }}</span></p>
        <ul class="list list--error" role="alert" v-if="report.errors.length"><li v-for="(e, i) in report.errors" :key="i">{{ e }}</li></ul>
        <p class="muted note">{{ report.prototype_warning }}</p>
      </div>

      <div class="card">
        <h3 class="card__title">Prototype Product Passport JSON-LD</h3>
        <json-tree :value="envelope" />
        <div class="btn-row">
          <button class="btn btn--primary" type="button" @click="downloadEnvelope"><app-icon name="download" :size="16" /> Download passport JSON-LD</button>
          <button class="btn" type="button" @click="downloadReport"><app-icon name="download" :size="16" /> Download validation (JSON)</button>
        </div>
      </div>
    </template>
  </section>
  `,
};
