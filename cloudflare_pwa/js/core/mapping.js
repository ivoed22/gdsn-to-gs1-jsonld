// Port of src/gdsn_to_gs1_jsonld/converter.py — the mapping-driven extraction
// orchestrator. Uses live DOM node references as the "selected" set (identical
// in effect to the Python lxml getpath string set, but exact and robust).

import { applyTransform, DecimalValue } from './transforms.js';
import { LanguageValue, setNestedValue, serializeDeep } from './model.js';
import {
  isElement,
  localName,
  nodeStringValue,
  childElements,
  ancestorElements,
  iterElements,
  subtreeText,
  serializeXmlTree,
} from './xml.js';
import { addMappingSuggestions } from './suggestions.js';
import { buildJsonld } from './jsonld.js';
import { validateProduct } from './validator.js';

// converter.UNMAPPED_IGNORE — container element names excluded from the
// unmapped-fields report.
const UNMAPPED_IGNORE = new Set([
  'catalogueItemNotificationMessage',
  'transaction',
  'transactionIdentification',
  'catalogueItem',
  'tradeItem',
  'tradeItemInformation',
  'tradeItemDescriptionInformation',
  'tradeItemMeasurements',
  'marketingInformation',
  'brandNameInformation',
  'informationProviderOfTradeItem',
  'contentOwner',
  'referencedFileInformation',
  'quantityContained',
  'nutrientDetail',
  'allergen',
]);

// Canonical model defaults (canonical_model.CanonicalProduct field defaults),
// so the JSON-LD builder can reference any field regardless of mapping profile.
function emptyCanonicalProduct() {
  return {
    gtin: null,
    product_name: [],
    product_description: [],
    brand_name: null,
    gpc_category_code: null,
    net_content_value: null,
    net_content_unit: null,
    product_image_url: [],
    product_page_url: null,
    ingredient_statement: [],
    allergens: [],
    nutrients: [],
    certifications: [],
    referenced_documents: [],
  };
}

function transformValue(rawValue, field) {
  let value = rawValue;
  for (const transform of field.transform || []) {
    value = applyTransform(String(value), transform);
  }
  return value;
}

// converter._xpath_scalar.
function xpathScalar(adapter, element, valueXpath) {
  const nodes = adapter.select(valueXpath, element);
  if (!nodes.length) return null;
  return nodeStringValue(nodes[0]);
}

// converter._extract_field. Returns { value, row, selectedElements }.
function extractField(adapter, root, field, defaultLanguage) {
  const elements = adapter.select(field.xpath, root);
  const selectedElements = elements.filter(isElement);
  const extracted = [];
  const errors = [];

  for (const element of elements) {
    if (!isElement(element)) {
      errors.push('Field xpath must select XML elements.');
      continue;
    }
    const rawValue = xpathScalar(adapter, element, field.value_xpath || 'text()');
    if (rawValue == null || !rawValue.trim()) continue;
    let transformed;
    try {
      transformed = transformValue(rawValue, field);
    } catch (exc) {
      errors.push(exc.message);
      continue;
    }
    if (field.datatype === 'language_string') {
      const language = field.language_xpath
        ? xpathScalar(adapter, element, field.language_xpath)
        : null;
      extracted.push(
        new LanguageValue(
          String(transformed),
          language || field.fallback_language || defaultLanguage
        )
      );
    } else {
      extracted.push(transformed);
    }
  }

  const found = extracted.length > 0;
  let status;
  let message;
  if (errors.length) {
    const isValidation = (field.transform || []).some(
      (name) => name === 'validate_gtin' || name === 'validate_url'
    );
    status = isValidation ? 'validation_error' : 'transform_error';
    message = errors.join('; ');
  } else if (found) {
    status = 'mapped';
    message = 'Value mapped successfully.';
  } else if (field.required) {
    status = 'missing_required';
    message = 'Required value was not found.';
  } else {
    status = 'missing_optional';
    message = 'Optional value was not found.';
  }

  const value = field.multiple ? extracted : extracted.length ? extracted[0] : null;
  const displayValues = extracted.map((item) => serializeDeep(item));
  const row = {
    id: field.id,
    description: field.description,
    xpath: field.xpath,
    canonical_field: field.canonical_field,
    jsonld_property: field.jsonld_property,
    required: !!field.required,
    found,
    value: field.multiple ? displayValues : displayValues.length ? displayValues[0] : null,
    status,
    message,
  };
  return { value, row, selectedElements };
}

// converter._extract_object_mapping. Returns { objects, row, selectedNodes }.
function extractObjectMapping(adapter, root, objectMapping, defaultLanguage) {
  const parents = adapter.select(objectMapping.parent_xpath, root).filter(isElement);
  const selectedNodes = new Set();
  const objects = [];
  const messages = [];

  for (const parent of parents) {
    selectedNodes.add(parent);
    if (parent.parentNode && isElement(parent.parentNode)) {
      selectedNodes.add(parent.parentNode);
    }
    const objectData = {};
    for (const field of objectMapping.fields) {
      const fieldElements = adapter.select(field.xpath, parent).filter(isElement);
      const values = [];
      for (const element of fieldElements) {
        selectedNodes.add(element);
        let ancestor = element.parentNode;
        while (ancestor && ancestor !== parent) {
          if (isElement(ancestor)) selectedNodes.add(ancestor);
          ancestor = ancestor.parentNode;
        }
        const rawValue = xpathScalar(adapter, element, field.value_xpath || 'text()');
        if (rawValue == null || !rawValue.trim()) continue;
        let transformed;
        try {
          transformed = transformValue(rawValue, field);
        } catch (exc) {
          messages.push(`${field.id}: ${exc.message}`);
          continue;
        }
        if (field.datatype === 'language_string') {
          const language = field.language_xpath
            ? xpathScalar(adapter, element, field.language_xpath)
            : null;
          values.push(
            new LanguageValue(
              String(transformed),
              language || field.fallback_language || defaultLanguage
            )
          );
        } else {
          values.push(transformed);
        }
      }
      if (field.required && values.length === 0) {
        messages.push(`${field.id}: required value was not found`);
      }
      if (field.canonical_field && values.length > 0) {
        setNestedValue(
          objectData,
          field.canonical_field,
          field.multiple ? values : values[0]
        );
      }
    }
    if (Object.keys(objectData).length > 0) objects.push(objectData);
  }

  const found = objects.length > 0;
  // Parent elements are the source nodes shown in the traceability view.
  const traceNodes = parents.slice();
  let status;
  let message;
  if (messages.length) {
    status = 'validation_error';
    message = messages.join('; ');
  } else if (found) {
    status = 'mapped';
    message = `Mapped ${objects.length} object(s).`;
  } else {
    status = 'missing_optional';
    message = 'Optional object mapping was not found.';
  }

  const row = {
    id: objectMapping.id,
    description: objectMapping.description,
    xpath: objectMapping.parent_xpath,
    canonical_field: objectMapping.canonical_field,
    jsonld_property: objectMapping.jsonld_property,
    required: objectMapping.fields.some((field) => field.required),
    found,
    value: objects.map((objectData) => serializeDeep(objectData)),
    status,
    message,
  };
  return { objects, row, selectedNodes, traceNodes };
}

// converter._find_unmapped.
function findUnmapped(root, selectedNodes, adapter) {
  const counts = new Map();
  const occurrences = [];
  for (const element of iterElements(root)) {
    if (selectedNodes.has(element)) continue;
    const ln = localName(element);
    if (UNMAPPED_IGNORE.has(ln)) continue;
    if (!subtreeText(element).trim()) continue;

    const parent =
      element.parentNode && isElement(element.parentNode) ? element.parentNode : null;
    const parentName = parent ? localName(parent) : null;
    const ancestorNames = ancestorElements(element).map(localName);
    const path = `/${ancestorNames.slice().reverse().join('/')}/${ln}`;

    const context = {};
    const langNodes = adapter.select(
      'ancestor-or-self::*[@languageCode][1]/@languageCode',
      element
    );
    if (langNodes.length) context.languageCode = String(nodeStringValue(langNodes[0]));

    if (parentName === 'referencedFileInformation' && parent) {
      const contextFields = new Set([
        'referencedFileTypeCode',
        'uniformResourceIdentifier',
        'fileName',
        'fileFormatName',
      ]);
      for (const sibling of childElements(parent)) {
        const siblingName = localName(sibling);
        if (contextFields.has(siblingName)) {
          const siblingValue = subtreeText(sibling).trim();
          if (siblingValue) context[siblingName] = siblingValue;
        }
      }
    }

    const discriminatorContainers = {
      nutrientDetail: 'nutrientTypeCode',
      allergen: 'allergenTypeCode',
      certification: 'certificationIdentification',
    };
    for (const [containerName, discriminatorName] of Object.entries(
      discriminatorContainers
    )) {
      const containers = adapter.select(
        `ancestor-or-self::*[local-name()='${containerName}'][1]`,
        element
      );
      if (!containers.length) continue;
      const discriminatorValues = adapter.select(
        `./*[local-name()='${discriminatorName}']/text()`,
        containers[0]
      );
      if (discriminatorValues.length) {
        const discriminatorValue = String(
          nodeStringValue(discriminatorValues[0])
        ).trim();
        if (discriminatorValue) context[discriminatorName] = discriminatorValue;
      }
    }

    const contextItems = Object.keys(context)
      .sort()
      .map((key) => [key, context[key]]);
    const mapKey = JSON.stringify([ln, parentName, path, contextItems]);
    const existing = counts.get(mapKey);
    if (existing) {
      existing.count += 1;
    } else {
      counts.set(mapKey, { element: ln, parent: parentName, path, contextItems, count: 1 });
    }

    const attributes = {};
    if (element.attributes) {
      for (let i = 0; i < element.attributes.length; i += 1) {
        const attribute = element.attributes[i];
        attributes[localName(attribute)] = attribute.value;
      }
    }
    const occurrence = {
      element: ln,
      parent: parentName,
      path,
      semantic_path: path,
      value: subtreeText(element).trim(),
    };
    if (Object.keys(attributes).length) occurrence.attributes = attributes;
    if (contextItems.length) occurrence.context = Object.fromEntries(contextItems);
    occurrences.push(occurrence);
  }

  const entries = [...counts.values()].sort((a, b) => {
    if (a.element !== b.element) return a.element < b.element ? -1 : 1;
    if (a.path !== b.path) return a.path < b.path ? -1 : 1;
    const ac = JSON.stringify(a.contextItems);
    const bc = JSON.stringify(b.contextItems);
    return ac < bc ? -1 : ac > bc ? 1 : 0;
  });

  return {
    report_version: '2.0',
    policy:
      'Populated source values not emitted by the active mapping profile. Values are preserved as source evidence; no GS1 terms are inferred.',
    summary: {
      unmapped_value_occurrences: occurrences.length,
      unmapped_element_groups: entries.length,
    },
    unmapped_values: occurrences,
    unmapped_elements: entries.map((entry) => {
      const obj = {
        element: entry.element,
        parent: entry.parent,
        path: entry.path,
        count: entry.count,
      };
      if (entry.contextItems.length) {
        obj.context = Object.fromEntries(entry.contextItems);
      }
      return obj;
    }),
  };
}

// converter._supporting_paths_for_combined_properties (parent nodes shared by
// two or more fields of the same JSON-LD property).
function supportingPaths(selectedElementsByProperty) {
  const out = new Set();
  for (const elementsByField of Object.values(selectedElementsByProperty)) {
    if (Object.keys(elementsByField).length < 2) continue;
    const fieldsByParent = new Map();
    for (const [fieldId, elements] of Object.entries(elementsByField)) {
      for (const element of elements) {
        const parent = element.parentNode;
        if (!parent || !isElement(parent)) continue;
        if (!fieldsByParent.has(parent)) fieldsByParent.set(parent, new Set());
        fieldsByParent.get(parent).add(fieldId);
      }
    }
    for (const [parent, fieldIds] of fieldsByParent) {
      if (fieldIds.size >= 2) out.add(parent);
    }
  }
  return out;
}

// converter.convert_xml_to_jsonld (without file writing / Track-D codelists).
export function convertXmlToJsonld(adapter, xmlText, mapping, suggestionCatalog = []) {
  const root = adapter.parse(xmlText);
  const defaultLanguage =
    (mapping.settings && mapping.settings.default_language) || 'en';
  const productValues = {};
  const mappingRows = [];
  const selectedNodes = new Set();
  const selectedElementsByProperty = {};
  const rowSourceNodes = {}; // row id -> [source DOM nodes] (for traceability)

  for (const field of mapping.fields) {
    const { value, row, selectedElements } = extractField(
      adapter,
      root,
      field,
      defaultLanguage
    );
    productValues[field.canonical_field] = value;
    mappingRows.push(row);
    rowSourceNodes[field.id] = selectedElements;
    for (const element of selectedElements) selectedNodes.add(element);
    if (row.found) {
      for (const element of selectedElements) {
        const parent = element.parentNode;
        if (parent && isElement(parent) && localName(parent) === localName(element)) {
          selectedNodes.add(parent);
        }
      }
      if (!selectedElementsByProperty[field.jsonld_property]) {
        selectedElementsByProperty[field.jsonld_property] = {};
      }
      selectedElementsByProperty[field.jsonld_property][field.id] = selectedElements;
    }
  }

  for (const objectMapping of mapping.object_mappings || []) {
    const { objects, row, selectedNodes: objectNodes, traceNodes } = extractObjectMapping(
      adapter,
      root,
      objectMapping,
      defaultLanguage
    );
    productValues[objectMapping.canonical_field] = objects;
    mappingRows.push(row);
    rowSourceNodes[objectMapping.id] = traceNodes;
    for (const node of objectNodes) selectedNodes.add(node);
  }

  for (const node of supportingPaths(selectedElementsByProperty)) {
    selectedNodes.add(node);
  }

  const product = emptyCanonicalProduct();
  for (const [key, value] of Object.entries(productValues)) product[key] = value;

  const validationReport = validateProduct(product, mapping, mappingRows);
  const jsonldData = buildJsonld(product, mapping);
  const unmappedFields = addMappingSuggestions(
    findUnmapped(root, selectedNodes, adapter),
    suggestionCatalog
  );

  // Additive traceability data — does not affect jsonld_data (golden-stable).
  const { tree, nodeToId } = serializeXmlTree(root);
  const rowSourceIds = {};
  for (const [rowId, nodes] of Object.entries(rowSourceNodes)) {
    const ids = [];
    for (const node of nodes) {
      const id = nodeToId.get(node);
      if (id !== undefined && !ids.includes(id)) ids.push(id);
    }
    if (ids.length) rowSourceIds[rowId] = ids;
  }

  return {
    jsonld_data: jsonldData,
    canonical_product: product,
    mapping_report_rows: mappingRows,
    validation_report: validationReport,
    unmapped_fields: unmappedFields,
    trace: { tree, row_source_ids: rowSourceIds },
  };
}

export { DecimalValue };
