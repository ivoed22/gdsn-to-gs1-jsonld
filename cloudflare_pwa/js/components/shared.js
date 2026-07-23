// Shared Options-API components used across workflows.

import { toastState, dismissToast } from '../toast.js';

export const StatusBadge = {
  name: 'StatusBadge',
  props: {
    label: { type: String, required: true },
    tone: { type: String, default: 'neutral' },
  },
  template: `<span class="badge" :class="'badge--' + tone">{{ label }}</span>`,
};

export const Skeleton = {
  name: 'Skeleton',
  props: { lines: { type: Number, default: 3 } },
  template: `
    <div class="skeleton" aria-hidden="true">
      <div class="skeleton__line" v-for="n in lines" :key="n"
        :style="{ width: (60 + (n * 13) % 40) + '%' }"></div>
    </div>
  `,
};

// Recursive JSON tree node — collapsible objects/arrays, colored primitives.
// Registered globally as <json-tree-node> in app.js so it can recurse by name.
export const JsonTreeNode = {
  name: 'JsonTreeNode',
  props: {
    data: {},
    keyName: { default: null },
    depth: { type: Number, default: 0 },
    last: { type: Boolean, default: true },
  },
  data() {
    return { open: this.depth < 2 };
  },
  computed: {
    kind() {
      if (Array.isArray(this.data)) return 'array';
      if (this.data === null) return 'null';
      return typeof this.data;
    },
    entries() {
      if (this.kind === 'array') return this.data.map((v, i) => [i, v]);
      if (this.kind === 'object') return Object.entries(this.data);
      return [];
    },
    isContainer() {
      return this.kind === 'array' || this.kind === 'object';
    },
    primitiveText() {
      if (this.kind === 'string') return JSON.stringify(this.data);
      return String(this.data);
    },
  },
  methods: {
    toggle() {
      this.open = !this.open;
    },
  },
  template: `
    <div class="jt-node">
      <template v-if="isContainer">
        <div class="jt-line">
          <button class="jt-toggle" type="button" @click="toggle" :aria-expanded="open ? 'true':'false'">
            {{ open ? '▾' : '▸' }}
          </button>
          <span v-if="keyName !== null" class="jt-key">{{ keyName }}</span><span v-if="keyName !== null">: </span>
          <span class="jt-punct">{{ kind === 'array' ? '[' : '{' }}</span>
          <span v-if="!open" class="jt-collapsed" @click="toggle">… {{ entries.length }} {{ kind === 'array' ? 'items' : 'keys' }} {{ kind === 'array' ? ']' : '}' }}</span>
        </div>
        <div v-if="open" class="jt-children">
          <json-tree-node v-for="([k, v], i) in entries" :key="i"
            :data="v" :key-name="kind === 'array' ? null : k" :depth="depth + 1"
            :last="i === entries.length - 1" />
          <div class="jt-line jt-close"><span class="jt-punct">{{ kind === 'array' ? ']' : '}' }}</span></div>
        </div>
      </template>
      <div v-else class="jt-line">
        <span v-if="keyName !== null" class="jt-key">{{ keyName }}</span><span v-if="keyName !== null">: </span>
        <span :class="'jt-' + kind">{{ primitiveText }}</span>
      </div>
    </div>
  `,
};

// Copyable JSON viewer wrapping the recursive tree.
export const JsonTree = {
  name: 'JsonTree',
  props: { value: { required: true } },
  data() {
    return { copied: false };
  },
  computed: {
    text() {
      return JSON.stringify(this.value, null, 2);
    },
  },
  methods: {
    async copy() {
      try {
        await navigator.clipboard.writeText(this.text);
        this.copied = true;
        setTimeout(() => {
          this.copied = false;
        }, 1500);
      } catch (err) {
        this.copied = false;
      }
    },
  },
  template: `
    <div class="jsonview">
      <button class="jsonview__copy" type="button" @click="copy">{{ copied ? 'Copied' : 'Copy' }}</button>
      <div class="jsontree"><json-tree-node :data="value" :depth="0" /></div>
    </div>
  `,
};

// Recursive source-XML tree node for the traceability view. Highlights the
// element(s) a selected mapping row came from. Registered globally as
// <xml-tree-node> in app.js.
export const XmlTreeNode = {
  name: 'XmlTreeNode',
  props: {
    node: { type: Object, required: true },
    highlight: { type: Object, required: true }, // Set of ids
    depth: { type: Number, default: 0 },
  },
  data() {
    return { open: true };
  },
  computed: {
    highlighted() {
      return this.highlight.has(this.node.id);
    },
    hasChildren() {
      return this.node.children && this.node.children.length > 0;
    },
  },
  methods: {
    toggle() {
      this.open = !this.open;
    },
  },
  template: `
    <div class="xt-node" :data-xmlid="node.id">
      <div class="xt-line" :class="{ 'xt-line--hl': highlighted }">
        <button v-if="hasChildren" class="jt-toggle" type="button" @click="toggle" :aria-expanded="open ? 'true':'false'">{{ open ? '▾' : '▸' }}</button>
        <span v-else class="jt-toggle jt-toggle--leaf"></span>
        <span class="xt-tag">&lt;{{ node.name }}<template v-for="a in node.attrs" :key="a.name"> <span class="xt-attr">{{ a.name }}</span>=<span class="xt-val">"{{ a.value }}"</span></template>&gt;</span>
        <span v-if="node.text" class="xt-text">{{ node.text }}</span>
      </div>
      <div v-if="hasChildren && open" class="xt-children">
        <xml-tree-node v-for="child in node.children" :key="child.id"
          :node="child" :highlight="highlight" :depth="depth + 1" />
      </div>
    </div>
  `,
};

// Drag-and-drop file zone (also click / keyboard to open the native picker).
export const FileDrop = {
  name: 'FileDrop',
  props: {
    multiple: { type: Boolean, default: false },
    accept: { type: String, default: '' },
    label: { type: String, default: 'Drag & drop a file here, or click to choose' },
    inputId: { type: String, default: 'filedrop' },
  },
  emits: ['files'],
  data() {
    return { over: false };
  },
  methods: {
    onDrop(event) {
      this.over = false;
      const files = event.dataTransfer && event.dataTransfer.files;
      if (files && files.length) this.$emit('files', [...files]);
    },
    onPick(event) {
      const files = event.target.files;
      if (files && files.length) this.$emit('files', [...files]);
      event.target.value = '';
    },
    openPicker() {
      this.$refs.input.click();
    },
  },
  template: `
    <div class="filedrop" :class="{ 'filedrop--over': over }"
      role="button" tabindex="0" :aria-label="label"
      @click="openPicker" @keydown.enter.prevent="openPicker" @keydown.space.prevent="openPicker"
      @dragover.prevent="over = true" @dragleave.prevent="over = false" @drop.prevent="onDrop">
      <app-icon name="upload" class="filedrop__icon" :size="22" />
      <span>{{ label }}</span>
      <input ref="input" :id="inputId" class="filedrop__input" type="file"
        :multiple="multiple" :accept="accept" @change="onPick" />
    </div>
  `,
};

// Command palette (Cmd/Ctrl-K). Parent controls `open` and supplies commands.
export const CommandPalette = {
  name: 'CommandPalette',
  props: {
    open: { type: Boolean, default: false },
    commands: { type: Array, default: () => [] },
  },
  emits: ['close'],
  data() {
    return { query: '', active: 0 };
  },
  computed: {
    filtered() {
      const q = this.query.trim().toLowerCase();
      const list = q
        ? this.commands.filter((c) => c.label.toLowerCase().includes(q))
        : this.commands;
      return list.slice(0, 12);
    },
  },
  watch: {
    open(value) {
      if (value) {
        this.query = '';
        this.active = 0;
        this.$nextTick(() => this.$refs.input && this.$refs.input.focus());
      }
    },
    query() {
      this.active = 0;
    },
  },
  methods: {
    move(delta) {
      const n = this.filtered.length;
      if (!n) return;
      this.active = (this.active + delta + n) % n;
    },
    run(cmd) {
      if (!cmd) return;
      this.$emit('close');
      cmd.run();
    },
    onEnter() {
      this.run(this.filtered[this.active]);
    },
  },
  template: `
    <div v-if="open" class="palette__scrim" @click="$emit('close')">
      <div class="palette" role="dialog" aria-label="Command palette" @click.stop>
        <input ref="input" class="palette__input" v-model="query"
          placeholder="Type a command…" @keydown.down.prevent="move(1)"
          @keydown.up.prevent="move(-1)" @keydown.enter.prevent="onEnter"
          @keydown.esc.prevent="$emit('close')" />
        <ul class="palette__list">
          <li v-for="(cmd, i) in filtered" :key="cmd.id"
            class="palette__item" :class="{ 'palette__item--active': i === active }"
            @mouseenter="active = i" @click="run(cmd)">
            <span>{{ cmd.label }}</span>
            <span v-if="cmd.hint" class="palette__hint">{{ cmd.hint }}</span>
          </li>
          <li v-if="!filtered.length" class="palette__empty">No matching commands.</li>
        </ul>
      </div>
    </div>
  `,
};

// Global toast host (aria-live). Rendered once by the app root.
export const ToastHost = {
  name: 'ToastHost',
  data() {
    return { toastState };
  },
  methods: {
    dismiss(id) {
      dismissToast(id);
    },
    onAction(item) {
      if (item.action) item.action();
      this.dismiss(item.id);
    },
  },
  template: `
    <div class="toasts" aria-live="polite" aria-atomic="false">
      <div v-for="item in toastState.items" :key="item.id" class="toast" :class="'toast--' + item.tone">
        <span class="toast__msg">{{ item.message }}</span>
        <button v-if="item.actionLabel" class="toast__action" type="button" @click="onAction(item)">{{ item.actionLabel }}</button>
        <button class="toast__close" type="button" aria-label="Dismiss" @click="dismiss(item.id)">×</button>
      </div>
    </div>
  `,
};
