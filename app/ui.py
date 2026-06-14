import streamlit as st

APP_VERSION = "v0.5.0"


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
            --radius-sm: 0.45rem;
            --radius-md: 0.75rem;
            --radius-lg: 1rem;
            --surface-default: #ffffff;
            --surface-muted: #f5f7fb;
            --surface-accent: #eef5ff;
            --border-default: #dbe3ee;
            --text-primary: #152238;
            --text-secondary: #53647a;
            --accent-primary: #1769aa;
            --accent-strong: #0f4f86;
            --accent-bright: #4aa3df;
            --state-success: #16794b;
            --state-warning: #9a6700;
            --state-error: #b42318;
        }

        .stApp {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(23, 105, 170, 0.07),
                    transparent 28rem
                ),
                var(--surface-muted);
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
            background:
                linear-gradient(
                    125deg,
                    rgba(15, 79, 134, 0.98),
                    rgba(23, 105, 170, 0.94)
                );
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: var(--radius-lg);
            box-shadow: 0 1rem 2.5rem rgba(15, 79, 134, 0.2);
            color: #ffffff;
            overflow: hidden;
            padding: 2.2rem 2.4rem;
            position: relative;
        }

        .app-hero::after {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            content: "";
            height: 15rem;
            position: absolute;
            right: -5rem;
            top: -7rem;
            width: 15rem;
        }

        .app-hero h1 {
            color: #ffffff;
            font-size: clamp(2rem, 5vw, 3.35rem);
            letter-spacing: -0.035em;
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
            background: linear-gradient(145deg, #eef5ff, #ffffff);
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
            border-top: 4px solid var(--accent-primary);
            border-radius: var(--radius-lg);
            box-shadow: 0 0.65rem 1.6rem rgba(21, 34, 56, 0.08);
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
            margin-bottom: var(--spacing-md);
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
            background: linear-gradient(
                135deg,
                var(--accent-primary),
                var(--accent-strong)
            );
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

        @media (hover: hover) {
            .stButton > button:hover,
            .stDownloadButton > button:hover {
                transform: translateY(-1px);
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

            .section-title-row {
                gap: 0.7rem;
            }

            .download-card-copy {
                min-height: auto;
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
          <p class="app-eyebrow">Standards-traceable conversion workspace</p>
          <h1>GDSN to GS1 JSON-LD Converter</h1>
          <p class="app-summary">
            Transform GDSN-like product XML into machine-readable GS1 Web
            Vocabulary JSON-LD with versioned mappings and reviewable reports.
          </p>
          <div class="app-meta" aria-label="Application characteristics">
            <span class="app-chip">Converter {APP_VERSION}</span>
            <span class="app-chip">In-memory processing</span>
            <span class="app-chip">BMS/XPath traceability</span>
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


def render_download_intro(title: str, summary: str) -> None:
    st.markdown(
        f"""
        <p class="download-card-title">{title}</p>
        <p class="download-card-copy">{summary}</p>
        """,
        unsafe_allow_html=True,
    )
