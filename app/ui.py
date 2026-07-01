from html import escape

import streamlit as st

APP_VERSION = "v0.13.1"


def apply_page_styles() -> None:
    """Apply the shared visual foundation for the Streamlit app."""
    st.markdown(
        """
        <style>
        :root {
            --spacing-xs: 0.375rem;
            --spacing-sm: 0.75rem;
            --spacing-md: 1.25rem;
            --spacing-lg: 2rem;
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.65rem;
            --surface-default: #ffffff;
            --surface-muted: #f5f7fb;
            --surface-accent: #eef5ff;
            --surface-active: #f1f8ff;
            --border-default: #dbe3ee;
            --text-primary: #152238;
            --text-secondary: #53647a;
            --accent-primary: #1769aa;
            --accent-strong: #0f4f86;
            --accent-bright: #4aa3df;
            --accent-rail: #70b7df;
            --state-success: #16794b;
            --state-warning: #9a6700;
            --state-error: #b42318;
        }

        .stApp {
            background: var(--surface-muted);
            color: var(--text-primary);
        }

        /* Streamlit-specific layout hooks; recheck after framework upgrades. */
        [data-testid="stMainBlockContainer"] {
            max-width: 76rem;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        [data-testid="stMainBlockContainer"]
        > div
        > [data-testid="stVerticalBlock"] {
            gap: 1.4rem;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid var(--border-default);
        }

        section[data-testid="stSidebar"] > div {
            background: var(--surface-default);
        }

        .app-hero {
            background: #102b46;
            border: 1px solid #234967;
            border-radius: var(--radius-lg);
            box-shadow: 0 1rem 2.5rem rgba(16, 43, 70, 0.18);
            color: #ffffff;
            overflow: hidden;
            padding: 2.2rem 2.4rem;
            position: relative;
        }

        .app-hero::after {
            background:
                linear-gradient(
                    90deg,
                    rgba(191, 226, 248, 0.18) 1px,
                    transparent 1px
                ),
                linear-gradient(
                    180deg,
                    rgba(191, 226, 248, 0.14) 1px,
                    transparent 1px
                );
            background-size: 2rem 2rem;
            content: "";
            height: 100%;
            opacity: 0.6;
            position: absolute;
            right: 0;
            top: 0;
            width: 38%;
        }

        .app-hero h1 {
            color: #ffffff;
            font-size: 2.55rem;
            letter-spacing: 0;
            line-height: 1.05;
            margin: 0 0 var(--spacing-sm);
            max-width: 48rem;
            position: relative;
            z-index: 1;
        }

        .app-hero .app-eyebrow {
            color: #bfe2f8;
            position: relative;
            z-index: 1;
        }

        .app-hero .app-summary {
            color: rgba(255, 255, 255, 0.88);
            margin-bottom: var(--spacing-md);
            position: relative;
            z-index: 1;
        }

        .app-hero .app-meta {
            margin-bottom: 0;
            position: relative;
            z-index: 1;
        }

        .app-hero .app-chip {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.24);
            color: #ffffff;
        }

        .privacy-note {
            align-items: flex-start;
            background: #eaf5ff;
            border: 1px solid #c7e2f5;
            border-radius: var(--radius-md);
            color: #264a66;
            display: flex;
            gap: var(--spacing-sm);
            padding: 0.9rem 1rem;
        }

        .privacy-note strong {
            color: var(--accent-strong);
        }

        .sidebar-brand {
            background: #f8fbfe;
            border: 1px solid #cfe0f3;
            border-radius: var(--radius-md);
            margin-bottom: var(--spacing-md);
            padding: 1rem;
        }

        .sidebar-brand strong {
            color: var(--accent-strong);
            display: block;
            font-size: 1rem;
            margin-bottom: 0.2rem;
        }

        .sidebar-brand span {
            color: var(--text-secondary);
            font-size: 0.82rem;
        }

        .sidebar-label {
            color: var(--accent-primary);
            font-size: 0.7rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            margin: 0 0 0.45rem;
            text-transform: uppercase;
        }

        /* Streamlit-specific hook for native border=True containers. */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface-default);
            border: 1px solid var(--border-default);
            border-top: 1px solid #c8d6e5;
            border-radius: var(--radius-lg);
            box-shadow: 0 0.45rem 1.1rem rgba(21, 34, 56, 0.055);
        }

        .app-eyebrow,
        .section-kicker {
            color: var(--accent-primary);
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin: 0 0 var(--spacing-xs);
            text-transform: uppercase;
        }

        .app-summary,
        .section-summary {
            color: var(--text-secondary);
            max-width: 52rem;
        }

        .app-summary {
            font-size: 1.05rem;
            line-height: 1.65;
            margin: 0 0 var(--spacing-md);
        }

        .section-heading {
            color: var(--text-primary);
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.3;
            margin: 0;
        }

        .section-summary {
            line-height: 1.55;
            margin: var(--spacing-xs) 0 var(--spacing-md);
        }

        .app-meta {
            display: flex;
            flex-wrap: wrap;
            gap: var(--spacing-sm);
            margin-bottom: var(--spacing-lg);
        }

        .section-title-row {
            align-items: flex-start;
            display: flex;
            gap: 0.9rem;
        }

        .step-number {
            align-items: center;
            background: var(--accent-primary);
            border-radius: 999px;
            color: #ffffff;
            display: inline-flex;
            flex: 0 0 2.3rem;
            font-size: 0.8rem;
            font-weight: 750;
            height: 2.3rem;
            justify-content: center;
            margin-top: 0.1rem;
        }

        .app-chip {
            background: var(--surface-accent);
            border: 1px solid #cfe0f3;
            border-radius: 999px;
            color: var(--accent-strong);
            font-size: 0.78rem;
            font-weight: 650;
            padding: 0.35rem 0.7rem;
        }

        .status-card {
            border: 1px solid;
            border-left-width: 0.35rem;
            border-radius: var(--radius-md);
            height: 100%;
            padding: 1rem 1.1rem;
        }

        .status-card strong {
            display: block;
            font-size: 1rem;
            margin-bottom: 0.2rem;
        }

        .status-success {
            background: #edf9f3;
            border-color: #8bd3ae;
            color: #115c3a;
        }

        .status-warning {
            background: #fff8e6;
            border-color: #e7c66b;
            color: #725000;
        }

        .status-error {
            background: #fff1f0;
            border-color: #efa6a0;
            color: #8d1d15;
        }

        .download-card-title {
            color: var(--text-primary);
            font-size: 0.95rem;
            font-weight: 700;
            margin: 0;
        }

        .download-card-header {
            align-items: center;
            display: flex;
            gap: 0.75rem;
            justify-content: space-between;
        }

        .file-type-badge {
            background: var(--surface-accent);
            border: 1px solid #cfe0f3;
            border-radius: 999px;
            color: var(--accent-strong);
            flex: 0 0 auto;
            font-size: 0.66rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            padding: 0.3rem 0.5rem;
        }

        .download-card-copy {
            color: var(--text-secondary);
            font-size: 0.82rem;
            line-height: 1.45;
            margin: 0.25rem 0 0.75rem;
            min-height: 2.4rem;
        }

        .stButton > button,
        .stDownloadButton > button {
            border: 1px solid #b8c7d9;
            border-radius: var(--radius-md);
            font-weight: 650;
            min-height: 2.75rem;
            transition:
                border-color 120ms ease,
                box-shadow 120ms ease,
                transform 120ms ease;
        }

        .stButton > button[kind="primary"] {
            background: var(--accent-primary);
            border-color: var(--accent-strong);
            box-shadow: 0 0.4rem 1rem rgba(23, 105, 170, 0.2);
        }

        .stDownloadButton > button {
            background: #f7fbff;
            border-color: #bfd4e8;
            color: var(--accent-strong);
        }

        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible {
            box-shadow: 0 0 0 0.2rem rgba(23, 105, 170, 0.22);
            outline: 2px solid var(--accent-primary);
            outline-offset: 2px;
        }

        [data-testid="column"] .stButton > button {
            border-radius: 0 0 var(--radius-md) var(--radius-md);
            margin-top: -0.65rem;
            min-height: 2.45rem;
        }

        /* Premium dashboard composition primitives. */
        .app-hero {
            padding: 1.55rem 1.7rem;
        }

        .hero-grid {
            align-items: center;
            display: grid;
            gap: 1.5rem;
            grid-template-columns: minmax(0, 1.55fr) minmax(17rem, 0.7fr);
            position: relative;
            z-index: 1;
        }

        .hero-copy {
            min-width: 0;
        }

        .app-hero h1 {
            font-size: 2.35rem;
        }

        .workspace-panel {
            backdrop-filter: blur(8px);
            background: rgba(5, 35, 62, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: var(--radius-md);
            padding: 1rem;
        }

        .workspace-label {
            color: #bfe2f8;
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            margin: 0 0 0.85rem;
            text-transform: uppercase;
        }

        .workspace-list {
            display: grid;
            gap: 0.65rem;
        }

        .workspace-item {
            border-left: 2px solid rgba(143, 210, 244, 0.7);
            padding-left: 0.65rem;
        }

        .workspace-item strong {
            color: #ffffff;
            display: block;
            font-size: 0.84rem;
        }

        .workspace-item span {
            color: rgba(255, 255, 255, 0.65);
            display: block;
            font-size: 0.7rem;
            line-height: 1.35;
            margin-top: 0.1rem;
        }

        .traceability-strip {
            background: var(--surface-default);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-md);
            display: grid;
            gap: 0;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            overflow: hidden;
        }

        .trace-node {
            border-right: 1px solid var(--border-default);
            min-height: 6.4rem;
            padding: 1.05rem 1rem 1rem;
            position: relative;
        }

        .trace-node:last-child {
            border-right: 0;
        }

        .trace-node::before {
            background: var(--accent-rail);
            content: "";
            height: 0.18rem;
            left: 1rem;
            position: absolute;
            right: 1rem;
            top: 0.75rem;
        }

        .trace-label {
            color: var(--accent-strong);
            display: block;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.7rem;
            font-weight: 800;
            margin: 0.65rem 0 0.55rem;
        }

        .trace-node strong {
            color: var(--text-primary);
            display: block;
            font-size: 0.94rem;
            margin-bottom: 0.25rem;
        }

        .trace-node p {
            color: var(--text-secondary);
            font-size: 0.82rem;
            line-height: 1.5;
            margin: 0;
        }

        .workflow-entry {
            margin-bottom: 0.95rem;
        }

        .workflow-entry h2 {
            color: var(--text-primary);
            font-size: 1.55rem;
            letter-spacing: 0;
            line-height: 1.2;
            margin: 0 0 0.35rem;
        }

        .workflow-entry p {
            color: var(--text-secondary);
            font-size: 0.96rem;
            line-height: 1.6;
            margin: 0;
            max-width: 58rem;
        }

        .workflow-group-label {
            color: var(--accent-primary);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.07em;
            margin: 1.35rem 0 0.55rem;
            text-transform: uppercase;
        }

        .workflow-mode-card {
            background: var(--surface-default);
            border: 1px solid var(--border-default);
            border-left: 0.35rem solid #b7c8da;
            border-radius: var(--radius-md) var(--radius-md) 0 0;
            min-height: 12.6rem;
            padding: 1rem 1rem 0.95rem;
        }

        .workflow-mode-card.is-active {
            background: var(--surface-active);
            border-color: #8bb7d8;
            border-left-color: var(--accent-primary);
            box-shadow: inset 0 0 0 1px rgba(23, 105, 170, 0.12);
        }

        .workflow-mode-card-header {
            align-items: center;
            display: flex;
            gap: 0.65rem;
            justify-content: space-between;
            margin-bottom: 0.85rem;
        }

        .workflow-mode-mark {
            align-items: center;
            background: var(--surface-accent);
            border: 1px solid #cfe0f3;
            border-radius: var(--radius-sm);
            color: var(--accent-strong);
            display: inline-flex;
            flex: 0 0 auto;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.72rem;
            font-weight: 850;
            height: 2.05rem;
            justify-content: center;
            width: 2.6rem;
        }

        .workflow-mode-state {
            background: #dff0fb;
            border: 1px solid #aad2ea;
            border-radius: 999px;
            color: var(--accent-strong);
            font-size: 0.67rem;
            font-weight: 750;
            padding: 0.22rem 0.48rem;
            text-transform: uppercase;
        }

        .workflow-mode-card.mode-xml {
            border-left-color: #70b7df;
        }

        .workflow-mode-card.mode-voc {
            border-left-color: #7fb394;
        }

        .workflow-mode-card.mode-sdr {
            border-left-color: #d4b75d;
        }

        .workflow-mode-card.mode-ld {
            border-left-color: #8a8fd6;
        }

        .workflow-mode-card.mode-xml .workflow-mode-mark {
            background: #eef8ff;
            border-color: #c8e5f6;
        }

        .workflow-mode-card.mode-voc .workflow-mode-mark {
            background: #f0f8f2;
            border-color: #cde8d4;
        }

        .workflow-mode-card.mode-sdr .workflow-mode-mark {
            background: #fff8e3;
            border-color: #ead996;
        }

        .workflow-mode-card.mode-ld .workflow-mode-mark {
            background: #f3f3ff;
            border-color: #d9dcff;
        }

        .workflow-mode-card.mode-map {
            border-left-color: #7ca9b8;
        }

        .workflow-mode-card.mode-map .workflow-mode-mark {
            background: #f0f6f9;
            border-color: #c5dde7;
        }

        .workflow-mode-card.mode-pp {
            border-left-color: #9b8bb8;
        }

        .workflow-mode-card.mode-pp .workflow-mode-mark {
            background: #f5f3ff;
            border-color: #d6cff0;
        }

        .workflow-mode-card.mode-pb {
            border-left-color: #6f9a8d;
        }

        .workflow-mode-card.mode-pb .workflow-mode-mark {
            background: #eef6f3;
            border-color: #cbe3db;
        }

        .pp-prototype-warning {
            background: #fff8e6;
            border: 1px solid #e7c66b;
            border-radius: var(--radius-md);
            color: #725000;
            font-size: 0.84rem;
            line-height: 1.5;
            margin-bottom: 1rem;
            padding: 0.85rem 1rem;
        }

        .pp-prototype-warning strong {
            color: #5a3c00;
            display: block;
            margin-bottom: 0.2rem;
        }

        .workflow-mode-title {
            color: var(--text-primary);
            display: block;
            font-size: 1.04rem;
            font-weight: 760;
            margin-bottom: 0.35rem;
        }

        .workflow-mode-copy,
        .workflow-mode-outcome {
            color: var(--text-secondary);
            font-size: 0.84rem;
            line-height: 1.5;
            margin: 0;
        }

        .workflow-mode-outcome {
            border-top: 1px solid var(--border-default);
            margin-top: 0.85rem;
            padding-top: 0.75rem;
        }

        .workflow-mode-outcome strong {
            color: var(--accent-strong);
        }

        .coverage-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }

        .coverage-badge {
            background: var(--surface-muted);
            border: 1px solid var(--border-default);
            border-radius: 999px;
            color: var(--text-secondary);
            font-size: 0.7rem;
            line-height: 1;
            padding: 0.42rem 0.58rem;
        }

        .vocabulary-status {
            background: #f8fbfe;
            border: 1px solid #d8e7f2;
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            font-size: 0.75rem;
            line-height: 1.5;
            margin-top: 0.8rem;
            padding: 0.75rem 0.85rem;
        }

        .vocabulary-status strong {
            color: var(--text-primary);
            display: block;
            font-size: 0.8rem;
            margin-bottom: 0.2rem;
        }

        .standards-backlog-status {
            background: #fffaf0;
            border: 1px solid #ead9b8;
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            font-size: 0.75rem;
            line-height: 1.5;
            margin-top: 0.65rem;
            padding: 0.75rem 0.85rem;
        }

        .standards-backlog-status strong {
            color: var(--text-primary);
            display: block;
            font-size: 0.8rem;
            margin-bottom: 0.2rem;
        }

        /* Streamlit-specific hook for the native uploader dropzone. */
        [data-testid="stFileUploaderDropzone"] {
            background: #f8fbfe;
            border: 1.5px dashed #8bb7d8;
            border-radius: var(--radius-md);
            padding: 1.25rem;
        }

        [data-testid="stFileUploaderDropzone"]:focus-within {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 0.2rem rgba(23, 105, 170, 0.16);
        }

        .empty-state {
            align-items: center;
            background: #f8fbfe;
            border: 1px solid #d8e7f2;
            border-radius: var(--radius-md);
            display: flex;
            gap: 0.85rem;
            margin-top: 0.6rem;
            padding: 0.9rem 1rem;
        }

        .empty-state-mark {
            align-items: center;
            background: var(--surface-accent);
            border-radius: var(--radius-sm);
            color: var(--accent-strong);
            display: inline-flex;
            flex: 0 0 2.3rem;
            font-size: 0.72rem;
            font-weight: 800;
            height: 2.3rem;
            justify-content: center;
        }

        .empty-state strong,
        .empty-state span {
            display: block;
        }

        .empty-state strong {
            color: var(--text-primary);
            font-size: 0.88rem;
        }

        .empty-state span {
            color: var(--text-secondary);
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }

        .identity-card {
            background: #f8fbfe;
            border: 1px solid #cfe0f3;
            border-radius: var(--radius-md);
            margin: 0.4rem 0 1rem;
            padding: 1rem 1.1rem;
        }

        .identity-label {
            color: var(--accent-primary);
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
            text-transform: uppercase;
        }

        .identity-value {
            color: var(--text-primary);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.86rem;
            overflow-wrap: anywhere;
        }

        .preview-heading {
            align-items: flex-end;
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            margin-top: 0.3rem;
        }

        .preview-heading strong,
        .preview-heading span {
            display: block;
        }

        .preview-heading strong {
            color: var(--text-primary);
            font-size: 1rem;
        }

        .preview-heading span {
            color: var(--text-secondary);
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }

        .preview-heading .preview-badge {
            background: var(--surface-accent);
            border: 1px solid #cfe0f3;
            border-radius: 999px;
            color: var(--accent-strong);
            flex: 0 0 auto;
            font-size: 0.68rem;
            font-weight: 750;
            margin: 0;
            padding: 0.35rem 0.55rem;
        }

        .result-summary-grid {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin-bottom: 1rem;
        }

        .result-summary-card {
            background: #f8fbff;
            border: 1px solid #d6e3ef;
            border-radius: var(--radius-md);
            min-height: 6.2rem;
            padding: 0.9rem;
        }

        .result-summary-label {
            color: var(--text-secondary);
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .result-summary-value {
            color: var(--text-primary);
            display: block;
            font-size: 1.05rem;
            font-weight: 750;
            margin: 0.55rem 0 0.18rem;
        }

        .result-summary-detail {
            color: var(--text-secondary);
            display: block;
            font-size: 0.74rem;
            line-height: 1.35;
        }

        .review-guide {
            background: #f4f9fe;
            border: 1px solid #c9ddef;
            border-radius: var(--radius-md);
            margin-top: 1rem;
            padding: 1rem 1.1rem;
        }

        .review-guide-title {
            color: var(--accent-strong);
            font-size: 0.9rem;
            font-weight: 750;
            margin-bottom: 0.75rem;
        }

        .review-guide ol {
            display: grid;
            gap: 0.5rem 1.2rem;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            list-style: none;
            margin: 0;
            padding: 0;
        }

        .review-guide li {
            color: var(--text-secondary);
            font-size: 0.74rem;
            line-height: 1.4;
            padding-left: 1.5rem;
            position: relative;
        }

        .review-guide li::before {
            align-items: center;
            background: var(--accent-primary);
            border-radius: 999px;
            color: #ffffff;
            content: attr(data-step);
            display: inline-flex;
            font-size: 0.62rem;
            font-weight: 800;
            height: 1.1rem;
            justify-content: center;
            left: 0;
            position: absolute;
            top: 0;
            width: 1.1rem;
        }

        .convert-progress {
            display: grid;
            gap: 0.5rem;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin: 0.1rem 0 1.15rem;
        }

        .convert-progress-step {
            background: var(--surface-muted);
            border: 1px solid var(--border-default);
            border-top: 3px solid var(--border-default);
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            font-size: 0.76rem;
            padding: 0.55rem 0.6rem;
            text-align: center;
        }

        .convert-progress-step .cp-num {
            display: block;
            font-size: 0.95rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }

        .convert-progress-step.active {
            background: var(--surface-active);
            border-top-color: var(--accent-primary);
            color: var(--text-primary);
            font-weight: 650;
        }

        .convert-progress-step.done {
            background: var(--surface-default);
            color: var(--text-primary);
            font-weight: 650;
        }

        .convert-progress-step.s1.done { border-top-color: #0f9b8e; }
        .convert-progress-step.s2.done { border-top-color: #c98a1b; }
        .convert-progress-step.s3.done { border-top-color: #d2691e; }
        .convert-progress-step.s4.done { border-top-color: #2e9e5b; }

        @media (max-width: 640px) {
            .convert-progress {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (hover: hover) {
            .stButton > button:hover,
            .stDownloadButton > button:hover {
                transform: translateY(-1px);
            }
        }

        @media (max-width: 900px) {
            .hero-grid,
            .traceability-strip,
            .result-summary-grid {
                grid-template-columns: 1fr;
            }

            .trace-node {
                border-bottom: 1px solid var(--border-default);
                border-right: 0;
            }

            .trace-node:last-child {
                border-bottom: 0;
            }

            .review-guide ol {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: var(--spacing-md);
            }

            .app-summary {
                font-size: 0.98rem;
            }

            .app-hero {
                padding: 1.5rem;
            }

            .app-hero h1 {
                font-size: 2rem;
            }

            .section-title-row {
                gap: 0.7rem;
            }

            .download-card-copy {
                min-height: auto;
            }

            .review-guide ol {
                grid-template-columns: 1fr;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            .stButton > button,
            .stDownloadButton > button {
                transition: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header() -> None:
    st.markdown(
        f"""
        <section class="app-hero">
          <div class="hero-grid">
            <div class="hero-copy">
              <p class="app-eyebrow">Standards-traceable conversion workspace</p>
              <h1>GDSN to GS1 JSON-LD Converter</h1>
              <p class="app-summary">
                Turn product XML into machine-readable, reviewable linked data.
              </p>
              <div class="app-meta" aria-label="Application characteristics">
                <span class="app-chip">Converter {APP_VERSION}</span>
                <span class="app-chip">In-memory</span>
                <span class="app-chip">Converter: BMS/XPath traceable</span>
              </div>
            </div>
            <div class="workspace-panel" aria-label="Workspace posture">
              <p class="workspace-label">Workspace posture</p>
              <div class="workspace-list">
                <div class="workspace-item">
                  <strong>Reviewable outputs</strong>
                  <span>JSON-LD, mapping trace, validation, and unmapped fields.</span>
                </div>
                <div class="workspace-item">
                  <strong>Controlled inputs</strong>
                  <span>XML is processed in memory; mappings stay versioned.</span>
                </div>
                <div class="workspace-item">
                  <strong>Governance visible</strong>
                  <span>Open SDRs are surfaced without suppressing warnings.</span>
                </div>
              </div>
            </div>
          </div>
        </section>
        <div class="privacy-note">
          <span aria-hidden="true">&#9679;</span>
          <span>
            <strong>Privacy by design.</strong>
            Uploaded XML is processed in memory and is not intentionally stored
            permanently.
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_overview() -> None:
    st.markdown(
        """
        <div class="traceability-strip" aria-label="Traceability rail">
          <div class="trace-node">
            <span class="trace-label">XML</span>
            <strong>GDSN source</strong>
            <p>Product data enters as single XML or ZIP-contained XML files.</p>
          </div>
          <div class="trace-node">
            <span class="trace-label">BMS/XPath</span>
            <strong>Mapping evidence</strong>
            <p>Versioned profiles preserve source-to-property traceability.</p>
          </div>
          <div class="trace-node">
            <span class="trace-label">JSON-LD</span>
            <strong>Linked data output</strong>
            <p>GS1 Web Vocabulary-aligned product data is generated for review.</p>
          </div>
          <div class="trace-node">
            <span class="trace-label">SDR</span>
            <strong>Governance context</strong>
            <p>Open standards decisions remain visible without changing runtime output.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_entry_intro() -> None:
    st.markdown(
        """
        <div class="workflow-entry">
          <p class="section-kicker">Workflow entry point</p>
          <h2>What do you want to do?</h2>
          <p>
            Choose a task. Workflows are grouped by intent: start by converting
            GDSN XML; explore and review mappings (Web Vocabulary, mapping
            candidates, standards decisions); and prototype linked data and
            Product Passports (JSON-LD prototypes, Product Passport source
            validation, and the Product Passport Builder). Each workflow keeps
            its own evidence, actions, and review surface.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_mode_card(
    title: str,
    description: str,
    outcome: str,
    marker: str,
    selected: bool,
) -> None:
    state_class = " is-active" if selected else ""
    marker_class = f" mode-{marker.lower()}"
    state_html = (
        '<span class="workflow-mode-state">Active</span>' if selected else ""
    )
    st.markdown(
        f"""
        <article class="workflow-mode-card{marker_class}{state_class}">
          <div class="workflow-mode-card-header">
            <span class="workflow-mode-mark">{escape(marker)}</span>
            {state_html}
          </div>
          <strong class="workflow-mode-title">{escape(title)}</strong>
          <p class="workflow-mode-copy">{escape(description)}</p>
          <p class="workflow-mode-outcome">
            <strong>Outcome:</strong> {escape(outcome)}
          </p>
        </article>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(step: int, title: str, summary: str) -> None:
    st.markdown(
        f"""
        <div class="section-title-row">
          <span class="step-number" aria-label="Step {step}">{step}</span>
          <div>
            <p class="section-kicker">Step {step}</p>
            <h2 class="section-heading">{title}</h2>
            <p class="section-summary">{summary}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_upload_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
          <span class="empty-state-mark" aria-hidden="true">XML</span>
          <div>
            <strong>Ready for one product message</strong>
            <span>Accepted format: .xml. Processing starts after Convert.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_vocabulary_status(
    version: str | None,
    last_modified: str | None,
) -> None:
    safe_version = escape(version or "metadata unavailable")
    safe_modified = escape(last_modified or "unknown")
    st.markdown(
        f"""
        <div class="vocabulary-status">
          <strong>Vocabulary status</strong>
          Local snapshot (offline): {safe_version}<br>
          Last modified: {safe_modified}<br>
          Update guidance: <code>docs/webvoc-update-monitor.md</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_standards_backlog_status(
    open_topics: int,
    categories: list[str],
) -> None:
    safe_categories = escape(", ".join(categories) or "metadata unavailable")
    st.markdown(
        f"""
        <div class="standards-backlog-status">
          <strong>Standards review backlog</strong>
          Open topics: {open_topics}<br>
          Categories: {safe_categories}<br>
          Register: <code>docs/standards-decisions/index.md</code><br>
          These are standards/governance decisions, not runtime converter failures.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(
    tone: str,
    title: str,
    detail: str,
) -> None:
    st.markdown(
        f"""
        <div class="status-card status-{tone}" role="status">
          <strong>{title}</strong>
          <span>{detail}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_summary(
    validation_value: str,
    validation_detail: str,
    mapped_rows: int,
    unmapped_rows: int,
) -> None:
    safe_validation_value = escape(validation_value)
    safe_validation_detail = escape(validation_detail)
    st.markdown(
        f"""
        <div class="result-summary-grid" aria-label="Generated output summary">
          <div class="result-summary-card">
            <span class="result-summary-label">JSON-LD generated</span>
            <span class="result-summary-value">Ready</span>
            <span class="result-summary-detail">Full structured product output</span>
          </div>
          <div class="result-summary-card">
            <span class="result-summary-label">Validation result</span>
            <span class="result-summary-value">{safe_validation_value}</span>
            <span class="result-summary-detail">{safe_validation_detail}</span>
          </div>
          <div class="result-summary-card">
            <span class="result-summary-label">Mapping report</span>
            <span class="result-summary-value">{mapped_rows} mapped</span>
            <span class="result-summary-detail">Traceable mapping rows found</span>
          </div>
          <div class="result-summary-card">
            <span class="result-summary-label">Unmapped fields report</span>
            <span class="result-summary-value">{unmapped_rows} entries</span>
            <span class="result-summary-detail">Source elements for review</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_identity_card(product_id: str) -> None:
    safe_product_id = escape(product_id)
    st.markdown(
        f"""
        <div class="identity-card">
          <div class="identity-label">GS1 Digital Link-style product @id</div>
          <div class="identity-value">{safe_product_id}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_preview_heading(
    title: str,
    summary: str,
    badge: str,
) -> None:
    st.markdown(
        f"""
        <div class="preview-heading">
          <div>
            <strong>{title}</strong>
            <span>{summary}</span>
          </div>
          <span class="preview-badge">{badge}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_download_intro(title: str, summary: str, file_type: str) -> None:
    st.markdown(
        f"""
        <div class="download-card-header">
          <p class="download-card-title">{title}</p>
          <span class="file-type-badge">{file_type}</span>
        </div>
        <p class="download-card-copy">{summary}</p>
        """,
        unsafe_allow_html=True,
    )


def render_convert_progress(converted: bool) -> None:
    """Render the four-step guided-conversion progress indicator.

    Before conversion, step 1 (Upload) is the active step; after a successful
    conversion, all four steps are marked done. This is a visual roadmap only —
    it does not change conversion behaviour.
    """
    steps = (
        (1, "Upload"),
        (2, "Mapping"),
        (3, "Validate"),
        (4, "Export"),
    )
    cells = []
    for number, label in steps:
        if converted:
            state = " done"
            mark = "✓"
        elif number == 1:
            state = " active"
            mark = str(number)
        else:
            state = ""
            mark = str(number)
        cells.append(
            f'<div class="convert-progress-step s{number}{state}">'
            f'<span class="cp-num">{mark}</span>{label}</div>'
        )
    st.markdown(
        f'<div class="convert-progress" aria-label="Conversion steps: '
        f'Upload, Mapping, Validate, Export">{"".join(cells)}</div>',
        unsafe_allow_html=True,
    )


def render_review_guidance() -> None:
    st.markdown(
        """
        <div class="review-guide">
          <div class="review-guide-title">What to review next</div>
          <ol>
            <li data-step="1">Check validation status</li>
            <li data-step="2">Confirm product identity</li>
            <li data-step="3">Review mapping report</li>
            <li data-step="4">Check unmapped fields</li>
            <li data-step="5">Download export package</li>
          </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )
