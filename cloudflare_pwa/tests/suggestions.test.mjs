import assert from 'node:assert/strict';
import test from 'node:test';

import { addMappingSuggestions } from '../js/core/suggestions.js';


const baseReport = {
  report_version: '2.0',
  summary: { unmapped_value_occurrences: 1, unmapped_element_groups: 1 },
  unmapped_values: [
    { element: 'consumerStorageInstructions', value: 'Keep cool' },
  ],
  unmapped_elements: [
    { element: 'consumerStorageInstructions', count: 1 },
  ],
};


test('adds an exact upload-specific suggestion without changing evidence', () => {
  const enriched = addMappingSuggestions(baseReport, [
    {
      gdsn_attribute_name: 'consumerStorageInstructions',
      proposed_webvoc_property: 'gs1:consumerStorageInstructions',
      proposed_webvoc_label: 'Consumer Storage Instructions',
      match_percentage: '100',
      suggestion_status: 'strong_candidate',
      review_consensus_status: 'unanimous_accept',
      accept_count: '4',
      auto_emit: 'false',
    },
  ]);

  assert.equal(enriched.mapping_suggestions.length, 1);
  assert.equal(enriched.mapping_suggestions[0].match_percentage, 100);
  assert.equal(enriched.mapping_suggestions[0].auto_emitted, false);
  assert.equal(enriched.mapping_suggestions[0].review_consensus_status, 'unanimous_accept');
  assert.equal(enriched.mapping_suggestions[0].accept_count, 4);
  assert.deepEqual(enriched.unmapped_values, baseReport.unmapped_values);
  assert.equal(enriched.summary.unmapped_value_occurrences, 1);
});


test('keeps 60 percent and rejects anything below the threshold', () => {
  const enriched = addMappingSuggestions(baseReport, [
    {
      gdsn_attribute_name: 'consumerStorageInstructions',
      proposed_webvoc_property: 'gs1:consumerStorageInstructions',
      match_percentage: '60',
      suggestion_status: 'review_candidate',
      auto_emit: 'false',
    },
    {
      gdsn_attribute_name: 'consumerStorageInstructions',
      proposed_webvoc_property: 'gs1:instructions',
      match_percentage: '59.9',
      suggestion_status: 'review_candidate',
      auto_emit: 'false',
    },
  ]);

  assert.equal(enriched.mapping_suggestions.length, 1);
  assert.equal(enriched.mapping_suggestions[0].match_percentage, 60);
});


test('refuses auto-emit rows and ambiguous compound source paths', () => {
  const report = {
    ...baseReport,
    unmapped_elements: [{ element: 'measurementUnitCode', count: 1 }],
  };
  const enriched = addMappingSuggestions(report, [
    {
      gdsn_attribute_name: 'netContent/@measurementUnitCode',
      proposed_webvoc_property: 'gs1:unitCode',
      match_percentage: '90',
      suggestion_status: 'strong_candidate',
      auto_emit: 'false',
    },
    {
      gdsn_attribute_name: 'measurementUnitCode',
      proposed_webvoc_property: 'gs1:unitCode',
      match_percentage: '100',
      suggestion_status: 'strong_candidate',
      auto_emit: 'true',
    },
  ]);

  assert.deepEqual(enriched.mapping_suggestions, []);
});
