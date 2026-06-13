# Project Working Rules

These rules apply to future Codex tasks in this repository.

- Always run `python -m pytest` before reporting completion.
- Always run the CLI conversion for the relevant mapping when converter logic
  changes.
- Always push changes unless instructed otherwise.
- After pushing, check GitHub Actions for the latest commit when possible.
- If GitHub CLI is unavailable or unauthenticated, explicitly state that
  GitHub Actions could not be verified directly.
- Never report work as done based only on code changes. Verify the relevant
  behavior first.
- Do not change converter logic when only documentation or UI polish is
  requested.
- Keep Streamlit as a UI layer only. Converter logic must remain in
  `src/gdsn_to_gs1_jsonld`.
- Keep `mapping/mapping_mvp.yaml` stable for v0.1.0 compatibility.
- Add new mappings as versioned files, such as `mapping/mapping_v0_2.yaml`.
