"""Accessibility & About page (feature #19).

Documents and demonstrates the accessibility options and lets the user try
text-to-speech. The controls also appear in the sidebar of every page.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_FRONTEND = Path(__file__).resolve().parents[1]
if str(_FRONTEND) not in sys.path:
    sys.path.insert(0, str(_FRONTEND))

import streamlit as st

from _accessibility import accessibility_controls, apply_accessibility, speak

st.set_page_config(page_title="GrowthAI · Accessibility", page_icon="♿", layout="wide")
options = accessibility_controls()
apply_accessibility(options)

st.title("♿ Accessibility")
st.caption("GrowthAI is built to be usable by everyone (feature #19).")

st.markdown(
    """
    ### Available options (see the **Accessibility** panel in the sidebar)

    | Option | What it does |
    |---|---|
    | 🔠 **Large fonts** | Increases text size across the whole app for low-vision users |
    | 🎨 **Color-blind mode** | Switches status colors to the Okabe–Ito color-blind-safe palette |
    | 🔊 **Read results aloud** | Uses your browser's built-in speech synthesis (fully offline) |
    | 🌙 **Dark mode** | The app ships dark-first; use Streamlit's theme menu for light mode |

    All options work with **zero external services** and no data leaves your device.
    """
)

st.subheader("🔊 Try text-to-speech")
sample = st.text_area(
    "Text to read",
    "Your child's BMI is in the healthy range for their age. Keep up balanced meals, "
    "at least sixty minutes of activity a day, and good sleep.",
)
if st.button("▶️ Read aloud"):
    speak(sample, enabled=True)
    st.success("Speaking… (ensure your device volume is on).")

st.divider()
st.caption("Speech synthesis uses the W3C Web Speech API available in modern browsers.")
