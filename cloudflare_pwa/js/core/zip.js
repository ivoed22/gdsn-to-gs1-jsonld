// Thin wrappers over the vendored fflate library (window.fflate) for the bulk
// workflow: read a .zip of XML files, and package conversion outputs into a
// .zip for download. Browser-only.

function fflate() {
  const lib = globalThis.fflate;
  if (!lib) throw new Error('ZIP support unavailable (vendor/fflate.min.js failed to load).');
  return lib;
}

// Build a ZIP (Uint8Array) from a { filename: string|Uint8Array } map.
export function zipFiles(files) {
  const lib = fflate();
  const entries = {};
  for (const [name, content] of Object.entries(files)) {
    entries[name] = typeof content === 'string' ? lib.strToU8(content) : content;
  }
  return lib.zipSync(entries, { level: 6 });
}

// Unpack a ZIP (Uint8Array) into text entries, filtered by extension.
// Returns [{ name, text }] for matching, non-directory entries.
export function unzipTextEntries(bytes, extensions = ['.xml']) {
  const lib = fflate();
  const unpacked = lib.unzipSync(bytes);
  const out = [];
  for (const [name, data] of Object.entries(unpacked)) {
    if (name.endsWith('/')) continue; // directory
    const lower = name.toLowerCase();
    if (extensions.length && !extensions.some((ext) => lower.endsWith(ext))) continue;
    // Skip macOS resource-fork noise.
    if (name.includes('__MACOSX/') || name.split('/').pop().startsWith('.')) continue;
    out.push({ name, text: lib.strFromU8(data) });
  }
  return out;
}
