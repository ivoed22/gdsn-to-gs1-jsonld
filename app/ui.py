import streamlit as st


def apply_page_styles() -> None:
    """Apply the small, shared visual foundation for the Streamlit app."""
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

        [data-testid="stMainBlockContainer"] {
            max-width: 76rem;
            padding-top: var(--spacing-lg);
            padding-bottom: 3rem;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid var(--border-default);
        }

        section[data-testid="stSidebar"] > div {
            background: var(--surface-default);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.94);
            border-color: var(--border-default);
            border-radius: var(--radius-lg);
            box-shadow: 0 0.5rem 1.5rem rgba(21, 34, 56, 0.055);
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
            font-size: 1.3rem;
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

        .app-chip {
            background: var(--surface-accent);
            border: 1px solid #cfe0f3;
            border-radius: 999px;
            color: var(--accent-strong);
            font-size: 0.78rem;
            font-weight: 650;
            padding: 0.35rem 0.7rem;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: var(--radius-md);
            min-height: 2.75rem;
            transition:
                border-color 120ms ease,
                box-shadow 120ms ease,
                transform 120ms ease;
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
        """
        <p class="app-eyebrow">Standards-traceable conversion workspace</p>
        """,
        unsafe_allow_html=True,
    )
    st.title("GDSN to GS1 JSON-LD Converter")
    st.markdown(
        """
        <p class="app-summary">
          Transform GDSN-like product XML into machine-readable GS1 Web
          Vocabulary JSON-LD with versioned mappings and reviewable reports.
        </p>
        <div class="app-meta" aria-label="Application characteristics">
          <span class="app-chip">Converter v0.5.0</span>
          <span class="app-chip">In-memory processing</span>
          <span class="app-chip">BMS/XPath traceability</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(kicker: str, title: str, summary: str) -> None:
    st.markdown(
        f"""
        <p class="section-kicker">{kicker}</p>
        <h2 class="section-heading">{title}</h2>
        <p class="section-summary">{summary}</p>
        """,
        unsafe_allow_html=True,
    )
