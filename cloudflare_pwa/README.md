# Cloudflare offline PWA

This directory is the static-assets application served at
`gdsntojsonldwebvoc.ivoladenius.com`. Cloudflare deploys it through the root
`wrangler.jsonc` file.

The PWA is a browser-native counterpart of the Python reference converter. The
current executable mapping is `data/mappings/mapping_v0_4.json`. Archived
profiles remain selectable only for comparison.

`data/mapping_suggestions_v0_1.json` is advisory evidence, not an executable
mapping. The upload-specific UI displays exact source-name matches scoring 60%
or higher, while `js/core/suggestions.js` structurally prevents automatic
emission. The generated JSON-LD therefore remains governed by the selected
mapping profile.
