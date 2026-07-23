import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';


test('conversion results use the requested visual order and hide passport continuation', async () => {
  const component = await readFile(new URL('../js/components/convert.js', import.meta.url), 'utf8');
  const css = await readFile(new URL('../css/styles.css', import.meta.url), 'utf8');

  assert.equal(component.includes('Continue to Product Passport'), false);
  assert.match(component, /61 strong consensus · 21\.2%/);
  assert.match(component, /24 acceptance consensus · 8\.3%/);
  assert.match(component, /113 human review · 39\.2%/);
  assert.match(component, /46 conflicted · 16\.0%/);
  assert.match(css, /\.result-section--downloads\s*\{\s*order:\s*2/);
  assert.match(css, /\.result-section--output\s*\{\s*order:\s*3/);
  assert.match(css, /\.result-section--checks\s*\{\s*order:\s*4/);
  assert.match(css, /\.result-section--suggestions\s*\{\s*order:\s*5/);
});


test('unmapped source table allocates its largest column to the path', async () => {
  const component = await readFile(new URL('../js/components/convert.js', import.meta.url), 'utf8');
  const css = await readFile(new URL('../css/styles.css', import.meta.url), 'utf8');

  assert.match(component, /table table--unmapped/);
  assert.match(css, /\.table--unmapped \.col--path\s*\{\s*width:\s*42%/);
  assert.match(css, /\.table--unmapped \.col--count\s*\{\s*width:\s*7%/);
});
