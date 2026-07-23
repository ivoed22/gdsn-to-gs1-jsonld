// Port of src/gdsn_to_gs1_jsonld/xml_parser.py + the XPath plumbing the
// converter relies on. Browser implementation uses DOMParser + document.evaluate.
//
// The mapping profiles use only XPath 1.0 constructs (local-name(), text(),
// @attr, ancestor:: / ancestor-or-self::), so a null namespace resolver is
// correct on the namespaced GDSN XML. Browser DOMParser never resolves external
// entities and never touches the network — matching the Python parser's
// resolve_entities=False, no_network=True hardening.

export const ELEMENT_NODE = 1;
export const ATTRIBUTE_NODE = 2;
export const TEXT_NODE = 3;

export class XMLParseError extends Error {}

// Build the XPath adapter the mapping engine consumes. Kept as a factory so a
// Node test harness can supply an equivalent adapter (xmldom + xpath) without
// the engine importing any browser globals.
export function createBrowserXPath() {
  const domParser = new DOMParser();

  return {
    parse(text) {
      const doc = domParser.parseFromString(text, 'application/xml');
      // DOMParser reports failures as a <parsererror> element rather than
      // throwing; detect it and surface the same error shape as Python.
      const parserError = doc.getElementsByTagName('parsererror')[0];
      if (parserError) {
        throw new XMLParseError(
          `Invalid XML: ${parserError.textContent.trim()}`
        );
      }
      const root = doc.documentElement;
      if (!root) {
        throw new XMLParseError('Invalid XML: no document element');
      }
      return root;
    },

    // Return XPath results as an ordered array of nodes (elements, attribute
    // nodes, or text nodes), relative to contextNode.
    select(expr, contextNode) {
      const doc = contextNode.ownerDocument || contextNode;
      const result = doc.evaluate(
        expr,
        contextNode,
        null,
        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
        null
      );
      const nodes = [];
      for (let i = 0; i < result.snapshotLength; i += 1) {
        nodes.push(result.snapshotItem(i));
      }
      return nodes;
    },
  };
}

// DOM helpers shared by the mapping engine. These use only properties present
// in both the browser DOM and xmldom, so the engine stays environment-neutral.

export function localName(node) {
  // Both DOMs expose localName; fall back to stripping a prefix from nodeName.
  if (node.localName) return node.localName;
  const name = node.nodeName || '';
  const colon = name.indexOf(':');
  return colon >= 0 ? name.slice(colon + 1) : name;
}

export function isElement(node) {
  return node && node.nodeType === ELEMENT_NODE;
}

// First string value of an XPath result, mirroring converter._xpath_scalar:
// an element result contributes its full text (textContent == "".join(itertext));
// an attribute/text result contributes its node value.
export function nodeStringValue(node) {
  if (node == null) return null;
  if (node.nodeType === ELEMENT_NODE) return node.textContent;
  // Attribute and text nodes: nodeValue holds the string.
  return node.nodeValue;
}

// Element children of a node (skips text/comment nodes).
export function childElements(node) {
  const out = [];
  const children = node.childNodes;
  if (!children) return out;
  for (let i = 0; i < children.length; i += 1) {
    if (children[i].nodeType === ELEMENT_NODE) out.push(children[i]);
  }
  return out;
}

// Ancestor elements from parent up to (and including) the root element, in
// nearest-first order — mirrors lxml Element.iterancestors().
export function ancestorElements(node) {
  const out = [];
  let current = node.parentNode;
  while (current && current.nodeType === ELEMENT_NODE) {
    out.push(current);
    current = current.parentNode;
  }
  return out;
}

// Depth-first iteration over an element and all its descendant elements in
// document order — mirrors lxml Element.iter() restricted to element nodes.
export function iterElements(root) {
  const out = [];
  const walk = (node) => {
    out.push(node);
    const children = node.childNodes;
    if (!children) return;
    for (let i = 0; i < children.length; i += 1) {
      if (children[i].nodeType === ELEMENT_NODE) walk(children[i]);
    }
  };
  walk(root);
  return out;
}

// Whole-subtree text (element.itertext joined), used to decide whether an
// unmapped element carries any content worth reporting.
export function subtreeText(node) {
  return node.textContent || '';
}

// Serialize an element subtree into a plain tree of { id, name, attrs, text,
// children } with a Map from live DOM node -> id. Used by the traceability
// view to render the source XML and highlight the element(s) each mapping row
// came from. Purely additive — does not affect conversion output.
export function serializeXmlTree(root) {
  const nodeToId = new Map();
  let counter = 0;
  const build = (element) => {
    const id = counter;
    counter += 1;
    nodeToId.set(element, id);
    const node = { id, name: localName(element), attrs: [], children: [] };
    const attributes = element.attributes;
    if (attributes) {
      for (let i = 0; i < attributes.length; i += 1) {
        const attr = attributes[i];
        node.attrs.push({ name: attr.name, value: attr.value });
      }
    }
    const kids = childElements(element);
    if (kids.length === 0) {
      const text = (element.textContent || '').trim();
      if (text) node.text = text;
    } else {
      for (const child of kids) node.children.push(build(child));
    }
    return node;
  };
  const tree = build(root);
  return { tree, nodeToId };
}
