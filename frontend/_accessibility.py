"""Shared accessibility utilities for the Streamlit app (feature #19).

Provides a reusable sidebar control block and CSS/JS injectors for:
* large-font mode,
* color-blind-safe palette,
* text-to-speech (browser SpeechSynthesis, fully offline).

Kept in one module so every page stays consistent (DRY).
"""

from __future__ import annotations

import html as _html

import streamlit as st
import streamlit.components.v1 as components

# Okabe-Ito color-blind-safe palette (widely recommended for accessibility).
COLORBLIND_SAFE = {
    "teal": "#0072B2", "green": "#009E73", "amber": "#E69F00", "red": "#D55E00", "navy": "#000000",
}


def accessibility_controls() -> dict[str, bool]:
    """Render the sidebar accessibility panel; return the chosen options."""
    with st.sidebar.expander("♿ Accessibility", expanded=False):
        large_font = st.checkbox("Large fonts", value=False, key="a11y_large")
        colorblind = st.checkbox("Color-blind mode", value=False, key="a11y_cb")
        tts = st.checkbox("Read results aloud", value=False, key="a11y_tts")
    return {"large_font": large_font, "colorblind": colorblind, "tts": tts}


def apply_accessibility(options: dict[str, bool]) -> None:
    """Inject CSS for the active accessibility options."""
    css = ""
    if options.get("large_font"):
        css += """
        html, body, .stApp, p, li, label, span, div[data-testid="stMarkdownContainer"] {
            font-size: 1.22rem !important; line-height: 1.7 !important;
        }
        h1 { font-size: 2.6rem !important; } h2 { font-size: 2.0rem !important; }
        """
    if options.get("colorblind"):
        css += """
        :root { --gai-teal:#0072B2; --gai-green:#009E73; --gai-amber:#E69F00; --gai-red:#D55E00; }
        .low,.normal { background:#009E73 !important; }
        .medium,.overweight,.underweight { background:#E69F00 !important; }
        .high,.obesity { background:#D55E00 !important; }
        """
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def speak(text: str, enabled: bool) -> None:
    """Speak ``text`` via the browser's offline speech synthesis."""
    if not enabled or not text:
        return
    safe = _html.escape(text).replace("`", "'")
    components.html(
        f"""
        <script>
          const u = new SpeechSynthesisUtterance(`{safe}`);
          u.rate = 0.98; u.pitch = 1.0;
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(u);
        </script>
        """,
        height=0,
    )
