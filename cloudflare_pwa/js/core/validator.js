// Port of src/gdsn_to_gs1_jsonld/validator.py.

export function validateProduct(product, mapping, mappingReportRows) {
  const errors = [];
  const warnings = [];
  const rowsById = {};
  for (const row of mappingReportRows) rowsById[row.id] = row;

  for (const field of mapping.fields) {
    const row = rowsById[field.id];
    if (field.required && !row.found) {
      if (field.canonical_field === 'gtin') {
        errors.push(
          "Required field 'gtin' was not found. Cannot construct product @id."
        );
      } else {
        errors.push(`Required field '${field.id}' was not found.`);
      }
    } else if (!field.required && !row.found) {
      warnings.push(`Optional field '${field.id}' was not found.`);
    } else if (row.status === 'transform_error' || row.status === 'validation_error') {
      const message = `Field '${field.id}': ${row.message}`;
      if (field.required) {
        errors.push(message);
      } else {
        warnings.push(message);
      }
    }
  }

  if (product.net_content_value == null || product.net_content_unit == null) {
    if (product.net_content_value != null || product.net_content_unit != null) {
      warnings.push(
        'Net content is incomplete; both value and unit are required for JSON-LD.'
      );
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}
