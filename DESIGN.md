# Design System

This is the practical UI reference for the Streamlit app. It intentionally uses
a small token set and native Streamlit components.

## Design goals

- Professional GS1 and standards-tool character.
- Clear workflow and report hierarchy.
- Calm, compact, accessible presentation.
- Small, reviewable changes with no business-logic coupling.

## Layout rules

- Use wide mode with a centered main content area.
- Organize the page as header, input workflow, result summary, report details,
  and downloads.
- Keep one primary action per section.
- Prefer containers and columns that stack cleanly.

## Spacing scale

| Token | Value | Use |
| --- | --- | --- |
| `spacing-xs` | `0.375rem` | Inline labels and compact metadata |
| `spacing-sm` | `0.75rem` | Related controls |
| `spacing-md` | `1.25rem` | Card padding and section gaps |
| `spacing-lg` | `2rem` | Major page sections |

## Border radius tokens

| Token | Value |
| --- | --- |
| `radius-sm` | `0.45rem` |
| `radius-md` | `0.75rem` |
| `radius-lg` | `1rem` |

## Typography rules

- Use Streamlit's system font stack.
- Page titles should be concise and visually dominant.
- Section titles should describe the task or report, not the component type.
- Supporting text uses `text-secondary` and short line lengths.
- Use monospace only for identifiers, paths, code, and structured output.

## Color tokens

| Token | Value |
| --- | --- |
| `surface-default` | `#ffffff` |
| `surface-muted` | `#f5f7fb` |
| `surface-accent` | `#eef5ff` |
| `border-default` | `#dbe3ee` |
| `text-primary` | `#152238` |
| `text-secondary` | `#53647a` |
| `accent-primary` | `#1769aa` |
| `accent-strong` | `#0f4f86` |
| `state-success` | `#16794b` |
| `state-warning` | `#9a6700` |
| `state-error` | `#b42318` |

## Surface and card rules

- Use a quiet border and subtle shadow, never heavy elevation.
- Cards group one task or one report family.
- Do not nest multiple styled cards.
- Keep code and data frames on native surfaces for readability.

## Button rules

- Primary buttons represent the next workflow action.
- Secondary and download buttons use consistent full-width alignment in their
  layout cell.
- Destructive-looking styling is reserved for destructive actions; reset is a
  neutral secondary action.
- Hover, active, disabled, and visible focus states must remain distinct.

## Form and input rules

- Keep labels visible.
- Place concise help text directly before or after the related input.
- Do not use placeholders as the only instruction.
- Group profile selection separately from file upload.

## Status state rules

- Use native success, warning, error, and info components.
- State messages begin with the outcome and include a useful count or next
  action where available.
- Never communicate state through color alone.

## Report and download section rules

- Order reports from outcome to detail: validation, product identity, JSON-LD,
  mapping trace, downloads.
- Give previews clear titles and one-line descriptions.
- Present downloads in a balanced grid and retain explicit file-format labels.

## Empty, loading, error, and success state rules

- Empty: explain the single next action.
- Loading: use a native spinner around work that can take noticeable time.
- Error: preserve the actionable exception message without exposing internals.
- Success: confirm completion and validation status.

## Accessibility checklist

- [ ] Visible keyboard focus on every interactive control.
- [ ] Sufficient foreground, background, and border contrast.
- [ ] Visible labels for uploader and profile selector.
- [ ] Status meaning available in text.
- [ ] Logical heading order.
- [ ] Reduced-motion preference respected.
- [ ] No functionality dependent on hover.

## Responsive checklist

- [ ] Columns stack without losing reading order.
- [ ] Controls remain full-width and usable on small screens.
- [ ] Main padding reduces on narrow viewports.
- [ ] Code and table content can scroll inside their native components.
- [ ] No fixed heights are required for core workflow content.
