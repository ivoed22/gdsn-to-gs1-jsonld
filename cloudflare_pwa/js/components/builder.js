// Manual JSON-LD Prototype Builder workflow (Options API). Manifest-driven form
// that authors prototype GS1 Web Vocabulary JSON-LD by hand, using the exact
// serializer/validator ported from jsonld_builder.py.

import { store, loadIndividuals } from '../store.js';
import {
  PROTOTYPE_GOVERNANCE_WARNING,
  buildPropertyMetadataIndex,
  getBuilderGroups,
  getBuilderFields,
  inferInputType,
  objectSubfieldKey,
  updateBuilderValue,
  validateBuilderState,
  serializeBuilderStateToJsonld,
  fullCodelistOptions,
} from '../core/builder.js';
import { jsonldString } from '../core/jsonld.js';
import { downloadText, extractGtin } from '../core/reports.js';
import { StatusBadge, JsonTree } from './shared.js';

const AUTOSAVE_KEY = 'builder-draft-v1';

export const BuilderWorkflow = {
  name: 'BuilderWorkflow',
  components: { StatusBadge, JsonTree },
  data() {
    return {
      store,
      rootClass: 'Product',
      category: 'General Product',
      defaultLanguage: 'en',
      inputs: {}, // pid or objectSubfieldKey -> raw value
      langs: {}, // pid/key -> language tag
      units: {}, // pid/key -> unit code
      openGroups: {}, // group key -> boolean
      fullList: {}, // code pid -> show full WebVoc code list
      individualsReady: !!store.individualsByClass,
      prototypeWarning: PROTOTYPE_GOVERNANCE_WARNING,
    };
  },
  computed: {
    manifest() {
      return store.builderManifest;
    },
    categories() {
      return (this.manifest.product_categories || []).map((item) => item.label);
    },
    languageOptions() {
      return this.manifest.default_language_options || ['en'];
    },
    metadataIndex() {
      return buildPropertyMetadataIndex(this.manifest, store.webvocProperties);
    },
    groups() {
      return getBuilderGroups(this.manifest, this.category);
    },
    // Assembled builder state from the flat input maps (mirrors update_builder_value).
    // Language tags only attach when the field has a value, so seeded language
    // defaults never create spurious empty entries.
    state() {
      let s = { root_class: this.rootClass, default_language: this.defaultLanguage, values: {} };
      const put = (key, value, language, unitCode) => {
        const isEmpty = value == null || value === '';
        s = updateBuilderValue(s, key, value, isEmpty ? undefined : language, unitCode);
      };
      for (const group of this.groups) {
        for (const field of getBuilderFields(this.manifest, group)) {
          const pid = field.property_id;
          const inputType = this.fieldInputType(field);
          if (inputType === 'object') {
            for (const sub of field.object_fields || []) {
              const key = objectSubfieldKey(pid, sub.property_id);
              put(key, this.inputs[key], this.langs[key], this.units[key]);
            }
          } else {
            put(pid, this.inputs[pid], this.langs[pid], this.units[pid]);
          }
        }
      }
      return s;
    },
    prototypeJsonld() {
      return serializeBuilderStateToJsonld(this.state, this.metadataIndex);
    },
    warnings() {
      return validateBuilderState(this.state, this.metadataIndex);
    },
    filledCount() {
      return Object.keys(this.state.values).length;
    },
  },
  created() {
    this.restoreDraft();
    this.seedLanguageDefaults();
  },
  watch: {
    // Autosave the draft so a refresh never loses hand-authored work.
    inputs: { handler: 'saveDraft', deep: true },
    langs: { handler: 'saveDraft', deep: true },
    units: { handler: 'saveDraft', deep: true },
    category: 'saveDraft',
    defaultLanguage: 'saveDraft',
  },
  methods: {
    saveDraft() {
      try {
        localStorage.setItem(
          AUTOSAVE_KEY,
          JSON.stringify({
            category: this.category,
            defaultLanguage: this.defaultLanguage,
            inputs: this.inputs,
            langs: this.langs,
            units: this.units,
          })
        );
      } catch (err) {
        /* storage full / disabled — non-fatal */
      }
    },
    restoreDraft() {
      try {
        const raw = localStorage.getItem(AUTOSAVE_KEY);
        if (!raw) return;
        const draft = JSON.parse(raw);
        if (draft.category) this.category = draft.category;
        if (draft.defaultLanguage) this.defaultLanguage = draft.defaultLanguage;
        this.inputs = draft.inputs || {};
        this.langs = draft.langs || {};
        this.units = draft.units || {};
      } catch (err) {
        /* corrupt draft — ignore */
      }
    },
    async toggleFullList(propertyId) {
      this.fullList[propertyId] = !this.fullList[propertyId];
      if (this.fullList[propertyId] && !store.individualsByClass) {
        await loadIndividuals();
        this.individualsReady = true;
      }
    },
    codeOptions(field) {
      if (this.fullList[field.property_id] && store.individualsByClass) {
        const meta = this.metadataIndex[field.property_id] || {};
        const full = fullCodelistOptions(meta.range || [], store.individualsByClass);
        if (full.length) return full;
      }
      return field.options || [];
    },
    fieldInputType(field) {
      const metadata = this.metadataIndex[field.property_id] || { term_id: field.property_id };
      return inferInputType(metadata, field.input_type_override);
    },
    subInputType(sub) {
      const metadata = this.metadataIndex[sub.property_id] || { term_id: sub.property_id };
      return inferInputType(metadata, sub.input_type_override);
    },
    fieldLabel(propertyId) {
      const meta = this.metadataIndex[propertyId];
      if (meta && meta.label) return meta.label;
      return propertyId.includes(':') ? propertyId.split(':').slice(1).join(':') : propertyId;
    },
    fieldRange(propertyId) {
      const meta = this.metadataIndex[propertyId];
      return meta && meta.range && meta.range.length ? meta.range.join(', ') : 'range unavailable';
    },
    isGroupOpen(groupKey) {
      return !!this.openGroups[groupKey];
    },
    toggleGroup(groupKey) {
      this.openGroups[groupKey] = !this.openGroups[groupKey];
    },
    // Seed language tags for language_text fields so they emit without extra clicks.
    seedLanguageDefaults() {
      for (const group of this.groups) {
        for (const field of getBuilderFields(this.manifest, group)) {
          if (this.fieldInputType(field) === 'language_text' && !this.langs[field.property_id]) {
            this.langs[field.property_id] = this.defaultLanguage;
          }
          if (this.fieldInputType(field) === 'object') {
            for (const sub of field.object_fields || []) {
              const key = objectSubfieldKey(field.property_id, sub.property_id);
              if (this.subInputType(sub) === 'language_text' && !this.langs[key]) {
                this.langs[key] = this.defaultLanguage;
              }
            }
          }
        }
      }
    },
    onCategoryChange() {
      this.seedLanguageDefaults();
    },
    reset() {
      this.inputs = {};
      this.langs = {};
      this.units = {};
      this.fullList = {};
      try {
        localStorage.removeItem(AUTOSAVE_KEY);
      } catch (err) {
        /* ignore */
      }
      this.seedLanguageDefaults();
    },
    download() {
      const gtin = extractGtin(this.prototypeJsonld) || 'prototype';
      downloadText(
        `prototype_${gtin}.jsonld`,
        jsonldString(this.prototypeJsonld),
        'application/ld+json'
      );
    },
  },
  template: `
  <section class="workflow">
    <header class="workflow__head">
      <h2>Manual JSON-LD Prototype Builder</h2>
      <p class="muted">
        Author prototype GS1 Web Vocabulary JSON-LD by hand from the
        {{ manifest.groups.length }}-group manifest. Range-aware inputs; the exact
        serializer and validator from the converter project.
      </p>
    </header>

    <p class="alert alert--warning">{{ prototypeWarning }}</p>

    <div class="grid grid--two">
      <div class="card">
        <h3 class="card__title">Setup</h3>
        <div class="field">
          <label class="field__label">Product category</label>
          <select class="input" v-model="category" @change="onCategoryChange">
            <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field__label">Default language</label>
          <select class="input" v-model="defaultLanguage">
            <option v-for="l in languageOptions" :key="l" :value="l">{{ l }}</option>
          </select>
        </div>
        <p class="muted">{{ filledCount }} field(s) with a value · {{ groups.length }} group(s) shown.</p>
        <button class="btn" type="button" @click="reset">Reset fields</button>
      </div>

      <div class="card">
        <h3 class="card__title">Validation warnings ({{ warnings.length }})</h3>
        <ul class="list list--warning">
          <li v-for="(w, i) in warnings" :key="i">{{ w }}</li>
        </ul>
      </div>
    </div>

    <div class="card" v-for="group in groups" :key="group.key">
      <button class="group-head" type="button" @click="toggleGroup(group.key)">
        <span>{{ isGroupOpen(group.key) ? '▾' : '▸' }} {{ group.label }}</span>
        <span class="muted">{{ getBuilderFields(manifest, group).length }} fields</span>
      </button>
      <div v-show="isGroupOpen(group.key)" class="group-body">
        <div class="field builder-field" v-for="field in getBuilderFields(manifest, group)" :key="field.property_id">
          <label class="field__label">
            {{ fieldLabel(field.property_id) }}
            <span class="req" v-if="field.requirement === 'required'">*</span>
            <span class="muted">· {{ fieldInputType(field) }}</span>
          </label>
          <p class="muted note" v-if="field.help_text">{{ field.help_text }}</p>

          <!-- object -->
          <div v-if="fieldInputType(field) === 'object'" class="objectfield">
            <p class="muted"><code>{{ field.object_type }}</code></p>
            <div class="field" v-for="sub in field.object_fields" :key="sub.property_id">
              <label class="field__label">{{ fieldLabel(sub.property_id) }} <span class="muted">· {{ subInputType(sub) }}</span></label>
              <div class="inline" v-if="subInputType(sub) === 'language_text'">
                <input class="input" type="text" v-model="inputs[objectSubfieldKey(field.property_id, sub.property_id)]" />
                <select class="input input--sm" v-model="langs[objectSubfieldKey(field.property_id, sub.property_id)]">
                  <option v-for="l in languageOptions" :key="l" :value="l">{{ l }}</option>
                </select>
              </div>
              <input v-else class="input" :type="subInputType(sub) === 'url' ? 'url' : 'text'"
                v-model="inputs[objectSubfieldKey(field.property_id, sub.property_id)]" />
            </div>
          </div>

          <!-- language_text -->
          <div v-else-if="fieldInputType(field) === 'language_text'" class="inline">
            <input class="input" type="text" v-model="inputs[field.property_id]"
              :placeholder="field.example_value || ''" />
            <select class="input input--sm" v-model="langs[field.property_id]">
              <option v-for="l in languageOptions" :key="l" :value="l">{{ l }}</option>
            </select>
          </div>

          <!-- quantity -->
          <div v-else-if="fieldInputType(field) === 'quantity'" class="inline">
            <input class="input" type="number" step="any" v-model="inputs[field.property_id]"
              :placeholder="field.example_value || 'value'" />
            <input class="input input--sm" type="text" v-model="units[field.property_id]" placeholder="unitCode" />
          </div>

          <!-- code -->
          <template v-else-if="fieldInputType(field) === 'code'">
            <select class="input" v-model="inputs[field.property_id]" :aria-label="fieldLabel(field.property_id)">
              <option value="">— none —</option>
              <option v-for="opt in codeOptions(field)" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <label class="checkline note" v-if="(metadataIndex[field.property_id] || {}).range">
              <input type="checkbox" :checked="!!fullList[field.property_id]" @change="toggleFullList(field.property_id)" />
              show full code list ({{ codeOptions(field).length }})
            </label>
          </template>

          <!-- checkbox -->
          <label v-else-if="fieldInputType(field) === 'checkbox'" class="checkline">
            <input type="checkbox" v-model="inputs[field.property_id]" /> {{ fieldLabel(field.property_id) }}
          </label>

          <!-- scalar inputs -->
          <input v-else class="input"
            :type="fieldInputType(field) === 'url' ? 'url' :
                   fieldInputType(field) === 'date' ? 'date' :
                   fieldInputType(field) === 'datetime' ? 'datetime-local' :
                   (fieldInputType(field) === 'number' || fieldInputType(field) === 'integer') ? 'number' : 'text'"
            step="any"
            v-model="inputs[field.property_id]" :placeholder="field.example_value || ''" />
        </div>
      </div>
    </div>

    <div class="card">
      <h3 class="card__title">Prototype JSON-LD</h3>
      <json-tree :value="prototypeJsonld" />
      <div class="btn-row">
        <button class="btn btn--primary" type="button" @click="download"><app-icon name="download" :size="16" /> Download prototype JSON-LD</button>
      </div>
    </div>
  </section>
  `,
};

// getBuilderFields / objectSubfieldKey are referenced in the template; attach
// them to the component's methods so template expressions can resolve them.
BuilderWorkflow.methods.getBuilderFields = getBuilderFields;
BuilderWorkflow.methods.objectSubfieldKey = objectSubfieldKey;
