// WebVocabulary Explore workflow (Options API): browse/search GS1 Web
// Vocabulary properties and classes, with mapping evidence joined from the
// bundled catalog. Accepts a deep-linked ?term= from the Convert workflow.

import { store } from '../store.js';
import { StatusBadge } from './shared.js';

function termFromHash() {
  const match = /[?&]term=([^&]+)/.exec(location.hash);
  return match ? decodeURIComponent(match[1]) : '';
}

export const ExploreWorkflow = {
  name: 'ExploreWorkflow',
  components: { StatusBadge },
  data() {
    return {
      store,
      tab: 'properties',
      query: '',
      linkTypeOnly: false,
      selectedTermId: '',
    };
  },
  computed: {
    catalogIndex() {
      const index = {};
      for (const row of store.mappingCatalog) {
        const key = row.jsonld_property || row.recommended_jsonld_property;
        if (!key) continue;
        if (!index[key]) index[key] = [];
        index[key].push(row);
      }
      return index;
    },
    properties() {
      return store.webvocProperties;
    },
    filteredProperties() {
      const q = this.query.trim().toLowerCase();
      return this.properties.filter((property) => {
        if (this.linkTypeOnly && !property.is_link_type) return false;
        if (!q) return true;
        return (
          (property.term_id || '').toLowerCase().includes(q) ||
          (property.label || '').toLowerCase().includes(q) ||
          (property.comment || '').toLowerCase().includes(q)
        );
      });
    },
    filteredClasses() {
      const q = this.query.trim().toLowerCase();
      return store.webvocClasses.filter((klass) => {
        if (!q) return true;
        return (
          (klass.term_id || '').toLowerCase().includes(q) ||
          (klass.label || '').toLowerCase().includes(q) ||
          (klass.comment || '').toLowerCase().includes(q)
        );
      });
    },
    selected() {
      if (!this.selectedTermId) return null;
      const source = this.tab === 'properties' ? this.properties : store.webvocClasses;
      return source.find((item) => item.term_id === this.selectedTermId) || null;
    },
    selectedEvidence() {
      if (!this.selected) return [];
      return this.catalogIndex[this.selected.term_id] || [];
    },
  },
  mounted() {
    this.syncFromHash();
    this._onHash = () => this.syncFromHash();
    window.addEventListener('hashchange', this._onHash);
  },
  unmounted() {
    window.removeEventListener('hashchange', this._onHash);
  },
  methods: {
    syncFromHash() {
      const term = termFromHash();
      if (!term) return;
      const isClass = store.webvocClasses.some((c) => c.term_id === term);
      this.tab = isClass ? 'classes' : 'properties';
      this.query = term;
      this.selectedTermId = term;
    },
    coverageTone(termId) {
      return this.catalogIndex[termId] ? 'success' : 'neutral';
    },
    coverageLabel(termId) {
      return this.catalogIndex[termId] ? 'mapped' : 'no catalog evidence';
    },
    select(termId) {
      this.selectedTermId = termId;
    },
    switchTab(tab) {
      this.tab = tab;
      this.selectedTermId = '';
    },
  },
  template: `
  <section class="workflow">
    <header class="workflow__head">
      <h2>Explore GS1 Web Vocabulary</h2>
      <p class="muted">Offline browser over {{ properties.length }} properties and {{ store.webvocClasses.length }} classes (WebVoc 1.17 snapshot), with mapping evidence from the catalog.</p>
    </header>

    <div class="card">
      <div class="tabs" role="tablist">
        <button class="tab" role="tab" :aria-selected="tab === 'properties'" :class="{ 'tab--active': tab === 'properties' }" @click="switchTab('properties')">Properties</button>
        <button class="tab" role="tab" :aria-selected="tab === 'classes'" :class="{ 'tab--active': tab === 'classes' }" @click="switchTab('classes')">Classes</button>
      </div>
      <div class="field">
        <label class="field__label" for="explore-search">Search</label>
        <input id="explore-search" class="input" type="search" v-model="query" placeholder="Search term id, label, or comment…" />
      </div>
      <label class="checkline" v-if="tab === 'properties'"><input type="checkbox" v-model="linkTypeOnly" /> Link types only</label>
    </div>

    <div class="grid grid--explore">
      <div class="card card--list">
        <h3 class="card__title" v-if="tab === 'properties'">{{ filteredProperties.length }} properties</h3>
        <h3 class="card__title" v-else>{{ filteredClasses.length }} classes</h3>
        <ul class="reslist">
          <template v-if="tab === 'properties'">
            <li v-for="p in filteredProperties" :key="p.term_id">
              <button class="reslist__btn" :class="{ 'reslist__btn--active': p.term_id === selectedTermId }" @click="select(p.term_id)">
                <code>{{ p.term_id }}</code>
                <span class="reslist__label">{{ p.label }}</span>
                <status-badge :label="coverageLabel(p.term_id)" :tone="coverageTone(p.term_id)" />
              </button>
            </li>
          </template>
          <template v-else>
            <li v-for="c in filteredClasses" :key="c.term_id">
              <button class="reslist__btn" :class="{ 'reslist__btn--active': c.term_id === selectedTermId }" @click="select(c.term_id)">
                <code>{{ c.term_id }}</code>
                <span class="reslist__label">{{ c.label }}</span>
              </button>
            </li>
          </template>
        </ul>
      </div>

      <div class="card">
        <p class="muted" v-if="!selected">Select a term to see its detail.</p>
        <template v-else>
          <h3 class="card__title">{{ selected.label }}</h3>
          <p><code>{{ selected.term_id }}</code> <status-badge :label="selected.term_status" tone="neutral" /></p>
          <p>{{ selected.comment }}</p>
          <table class="table table--compact">
            <tbody>
              <tr v-if="selected.domain"><th scope="row">Domain</th><td>{{ (selected.domain || []).join(', ') || '—' }}</td></tr>
              <tr v-if="selected.range"><th scope="row">Range</th><td>{{ (selected.range || []).join(', ') || '—' }}</td></tr>
              <tr v-if="selected.sub_class_of"><th scope="row">Subclass of</th><td>{{ (selected.sub_class_of || []).join(', ') || '—' }}</td></tr>
              <tr v-if="selected.sub_property_of"><th scope="row">Sub-property of</th><td>{{ (selected.sub_property_of || []).join(', ') || '—' }}</td></tr>
              <tr v-if="'is_link_type' in selected"><th scope="row">Link type</th><td>{{ selected.is_link_type ? 'yes' : 'no' }}</td></tr>
              <tr><th scope="row">Last modified</th><td>{{ selected.last_modified || '—' }}</td></tr>
            </tbody>
          </table>

          <template v-if="tab === 'properties'">
            <h4 class="subhead">Mapping evidence ({{ selectedEvidence.length }})</h4>
            <p class="muted" v-if="!selectedEvidence.length">No mapping-catalog evidence links this property.</p>
            <div class="table-scroll" v-else>
              <table class="table">
                <thead><tr><th>Source attribute</th><th>BMS id</th><th>Status</th><th>Confidence</th><th>Scope</th></tr></thead>
                <tbody>
                  <tr v-for="(ev, i) in selectedEvidence" :key="i">
                    <td>{{ ev.gdsn_attribute_name }}</td>
                    <td>{{ ev.gdsn_bms_id }}</td>
                    <td><code>{{ ev.mapping_status }}</code></td>
                    <td>{{ ev.confidence }}</td>
                    <td>{{ ev.scope_group }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </template>
      </div>
    </div>
  </section>
  `,
};
