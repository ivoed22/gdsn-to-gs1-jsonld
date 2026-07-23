// Upload-specific, review-only GDSN -> Web Vocabulary mapping suggestions.
// Scores are discovery evidence only. This module never changes JSON-LD.

export const MINIMUM_SUGGESTION_PERCENTAGE = 60;
export const STRONG_SUGGESTION_PERCENTAGE = 90;

function sourceLocalName(attributeName) {
  const value = String(attributeName || '').trim().replaceAll('\\', '/');
  // A terminal name is ambiguous when the catalog row represents a nested
  // source path. Do not guess until parent-aware matching is implemented.
  if (!value || value.includes('/') || value.startsWith('@')) return '';
  return value;
}

function optionalNumber(value) {
  if (value == null || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function addMappingSuggestions(unmappedReport, catalog) {
  const index = new Map();
  for (const row of catalog || []) {
    const percentage = Number(row.match_percentage || 0);
    if (percentage < MINIMUM_SUGGESTION_PERCENTAGE) continue;
    // Fail closed: catalog suggestions must never enable emission.
    if (String(row.auto_emit || '').toLowerCase() !== 'false') continue;
    const local = sourceLocalName(row.gdsn_attribute_name).toLowerCase();
    if (!local) continue;
    if (!index.has(local)) index.set(local, []);
    index.get(local).push({ ...row, match_percentage: percentage });
  }

  const elements = new Set(
    (unmappedReport.unmapped_elements || [])
      .map((item) => String(item.element || '').trim())
      .filter(Boolean)
  );
  const suggestions = [];
  for (const element of [...elements].sort((a, b) => a.localeCompare(b))) {
    const candidates = [...(index.get(element.toLowerCase()) || [])].sort(
      (a, b) => b.match_percentage - a.match_percentage ||
        String(a.gdsn_attribute_name).localeCompare(String(b.gdsn_attribute_name)) ||
        String(a.proposed_webvoc_property).localeCompare(String(b.proposed_webvoc_property))
    );
    const seen = new Set();
    for (const candidate of candidates) {
      const marker = `${candidate.gdsn_attribute_name}\u0000${candidate.proposed_webvoc_property}`;
      if (seen.has(marker)) continue;
      seen.add(marker);
      suggestions.push({
        source_element: element,
        gdsn_attribute_name: candidate.gdsn_attribute_name,
        proposed_webvoc_property: candidate.proposed_webvoc_property,
        proposed_webvoc_label: candidate.proposed_webvoc_label || '',
        proposed_webvoc_range: candidate.proposed_webvoc_range || '',
        match_percentage: candidate.match_percentage,
        suggestion_status: candidate.suggestion_status,
        match_reasons: candidate.match_reasons || '',
        second_candidate: candidate.second_candidate || '',
        second_percentage: optionalNumber(candidate.second_percentage),
        third_candidate: candidate.third_candidate || '',
        third_percentage: optionalNumber(candidate.third_percentage),
        source_versions: candidate.source_versions || '',
        review_consensus_status: candidate.review_consensus_status || 'insufficient_review',
        reviewer_count: optionalNumber(candidate.reviewer_count),
        accept_count: optionalNumber(candidate.accept_count),
        needs_human_review_count: optionalNumber(candidate.needs_human_review_count),
        reject_count: optionalNumber(candidate.reject_count),
        no_equivalent_count: optionalNumber(candidate.no_equivalent_count),
        mean_reviewer_confidence: optionalNumber(candidate.mean_reviewer_confidence),
        reviewer_decisions: candidate.reviewer_decisions || '',
        recommended_action: candidate.recommended_action || '',
        auto_emitted: false,
        review_required: true,
      });
    }
  }

  return {
    report_version: '2.1',
    policy:
      'Populated source values not emitted by the active mapping profile. ' +
      'Possible 60%+ matches are review-only suggestions and are never emitted as JSON-LD.',
    ...unmappedReport,
    mapping_suggestion_policy: {
      minimum_match_percentage: MINIMUM_SUGGESTION_PERCENTAGE,
      strong_candidate_percentage: STRONG_SUGGESTION_PERCENTAGE,
      auto_emit: false,
      warning:
        'Similarity is not semantic approval. Verify definition, domain, range, cardinality, nesting and codelists.',
    },
    mapping_suggestions: suggestions,
    summary: {
      ...(unmappedReport.summary || {}),
      unmapped_element_groups: (unmappedReport.unmapped_elements || []).length,
      mapping_suggestion_count: suggestions.length,
      mapping_suggestion_source_elements: new Set(
        suggestions.map((item) => item.source_element)
      ).size,
    },
  };
}

export function addReviewCandidatesToJsonld(jsonldData, unmappedReport) {
  const valuesByElement = new Map();
  for (const occurrence of unmappedReport.unmapped_values || []) {
    const element = String(occurrence.element || '').trim();
    const value = String(occurrence.value || '').trim();
    if (!element || !value) continue;
    if (!valuesByElement.has(element)) valuesByElement.set(element, []);
    if (!valuesByElement.get(element).includes(value)) valuesByElement.get(element).push(value);
  }

  const nodes = [];
  const seen = new Set();
  for (const suggestion of unmappedReport.mapping_suggestions || []) {
    const element = String(suggestion.source_element || '').trim();
    const target = String(suggestion.proposed_webvoc_property || '').trim();
    for (const value of valuesByElement.get(element) || []) {
      const marker = `${element}\u0000${target}\u0000${value}`;
      if (seen.has(marker)) continue;
      seen.add(marker);
      nodes.push({
        '@type': 'schema:PropertyValue',
        'schema:name': element,
        'schema:value': value,
        'schema:propertyID': target,
        'schema:description':
          `Review candidate only; not an asserted GS1 mapping. Heuristic match ${Number(suggestion.match_percentage).toFixed(1)}%; ` +
          `AI consensus ${suggestion.review_consensus_status || 'human_review'}.`,
      });
    }
  }
  if (!nodes.length) return jsonldData;
  const existing = jsonldData['schema:additionalProperty'];
  return {
    ...jsonldData,
    'schema:additionalProperty': [
      ...(existing == null ? [] : Array.isArray(existing) ? existing : [existing]),
      ...nodes,
    ],
  };
}
