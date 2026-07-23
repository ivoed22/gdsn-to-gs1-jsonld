// Port of src/gdsn_to_gs1_jsonld/readiness.py — per-product DPP readiness
// (traceability & structural signals only). Track D is out of scope for this
// PWA, so the codelist dimension always reports not_evaluated (matching a
// conversion run without a codelist registry).

export const READINESS_LEVELS = [
  'structurally_ready',
  'attention_points',
  'review_required',
];

export const DPP_RELEVANCE_NOT_ASSESSED = 'not_yet_assessed_pending_crosswalk';

export const SCOPE_NOTE =
  'Traceability & structural readiness signals only — not official GS1 ' +
  'validation, no production compliance claim, and no EU DPP conformity ' +
  'assessment.';

function structuralValidationDimension(validationReport) {
  const errors = validationReport.errors || [];
  const warnings = validationReport.warnings || [];
  let status;
  if (!validationReport.valid) {
    status = 'errors';
  } else if (warnings.length) {
    status = 'passed_with_warnings';
  } else {
    status = 'passed';
  }
  return {
    status,
    error_count: errors.length,
    warning_count: warnings.length,
    detail: `${errors.length} error(s), ${warnings.length} warning(s) from the converter's structural validation.`,
  };
}

function mappingCoverageDimension(mappingReportRows, unmappedFields) {
  const total = mappingReportRows.length;
  const mapped = mappingReportRows.filter((row) => row.found).length;
  const unmappedElements = (unmappedFields.unmapped_elements || []).length;
  const status =
    mapped === total && unmappedElements === 0
      ? 'full_profile_coverage'
      : 'partial_profile_coverage';
  return {
    status,
    mapped_count: mapped,
    profile_row_count: total,
    unmapped_source_element_count: unmappedElements,
    detail: `${mapped}/${total} profile rows found in the source; ${unmappedElements} populated source element(s) outside the profile.`,
  };
}

function codelistConformanceDimension() {
  // Track D not implemented in this PWA — always "not evaluated".
  return {
    status: 'not_evaluated',
    counts: {},
    detail:
      'Codelist registry not loaded for this run, or no codelist-backed ' +
      'fields were present.',
  };
}

function dppRelevanceDimension() {
  return {
    status: DPP_RELEVANCE_NOT_ASSESSED,
    detail:
      "Which properties matter for a Digital Product Passport is the " +
      "GS1-first DPP Crosswalk's job (v0.36.0+, not built). Reporting " +
      'anything else here would fabricate a judgment.',
  };
}

function overallLevel(dimensions) {
  if (dimensions.structural_validation.status === 'errors') {
    return 'review_required';
  }
  if (
    dimensions.structural_validation.status === 'passed_with_warnings' ||
    dimensions.mapping_coverage.status === 'partial_profile_coverage' ||
    dimensions.codelist_conformance.status === 'issues_found'
  ) {
    return 'attention_points';
  }
  return 'structurally_ready';
}

export function assessReadiness({
  validation_report: validationReport,
  mapping_report_rows: mappingReportRows,
  unmapped_fields: unmappedFields,
}) {
  const dimensions = {
    structural_validation: structuralValidationDimension(validationReport),
    mapping_coverage: mappingCoverageDimension(mappingReportRows, unmappedFields),
    codelist_conformance: codelistConformanceDimension(),
    dpp_relevance: dppRelevanceDimension(),
  };
  return {
    readiness_level: overallLevel(dimensions),
    dimensions,
    scope_note: SCOPE_NOTE,
  };
}
