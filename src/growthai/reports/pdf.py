"""HTML/PDF rendering utilities.

Preserves the original Jinja2 + WeasyPrint pipeline but makes PDF generation
*graceful*: WeasyPrint needs native GTK libraries (often missing on Windows),
so if it is unavailable we still emit a fully-styled HTML report and say so,
rather than crashing. Charts and the QR code are embedded as base64 data URIs
so the output is a single portable file.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from growthai.logging_conf import get_logger

logger = get_logger("reports.pdf")

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_html(template_name: str, context: dict) -> str:
    """Render a Jinja2 template to an HTML string."""
    return _env.get_template(template_name).render(**context)


def fig_to_data_uri(fig, scale: float = 2.0) -> str | None:
    """Convert a Plotly figure to a base64 PNG data URI (needs kaleido)."""
    try:
        png = fig.to_image(format="png", scale=scale)
        b64 = base64.b64encode(png).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as exc:  # noqa: BLE001 - kaleido/chrome not present
        logger.warning("Chart export skipped (%s)", exc)
        return None


def qr_data_uri(payload: str) -> str | None:
    """Generate a QR code as a base64 PNG data URI (feature #6)."""
    try:
        import qrcode

        img = qrcode.make(payload)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("QR generation skipped (%s)", exc)
        return None


def html_to_pdf(html: str, output_path: Path) -> bool:
    """Write ``html`` to a PDF. Returns True on success, False if unavailable."""
    try:
        from weasyprint import HTML

        HTML(string=html).write_pdf(str(output_path))
        logger.info("PDF written: %s", output_path)
        return True
    except Exception as exc:  # noqa: BLE001 - GTK/WeasyPrint missing
        logger.warning("PDF generation unavailable (%s); HTML fallback used", exc)
        return False
