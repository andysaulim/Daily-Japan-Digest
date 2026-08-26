"""
Render a Japan Daily Brief to PDF (full-color, print-ready).

Usage:
  python make_pdf.py index.html                  # an already-rendered email HTML
  python make_pdf.py digest.json                 # a digest JSON (rendered first)
  python make_pdf.py index.html brief.pdf        # explicit output path

The email HTML is a 680px table layout built for inbox width; for print we keep
the design intact but force background graphics on so the navy panels and
Hinomaru accents survive, and let content flow across pages. Uses the
pre-installed Chromium via Playwright.
"""
import glob
import json
import os
import sys
from pathlib import Path

# Print tweak injected before </head>: force backgrounds to print, drop the
# card shadow, and let everything flow across page breaks. Kept minimal — the
# email design is otherwise unchanged.
_PRINT_CSS = """
<style>
  @media print {
    html, body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; background:#fff !important; }
    .wrapper { box-shadow: none !important; }
    a { text-decoration: none; }
    /* Let EVERYTHING flow across page breaks. Avoiding breaks on cards/rows
       pushes anything that doesn't fit to the next page, leaving big empty
       gaps — worse than a card occasionally splitting. */
    * { page-break-inside: auto !important; }
  }
  @page { size: Letter; margin: 9mm 10mm; }
</style>
"""


def html_from_input(path: Path) -> str:
    """Return print-ready HTML from either a rendered .html or a digest .json."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        digest = json.loads(path.read_text(encoding="utf-8"))
        from render import render_html
        html = render_html(digest)
    else:
        html = path.read_text(encoding="utf-8")
    if "</head>" in html:
        html = html.replace("</head>", _PRINT_CSS + "</head>", 1)
    else:
        html = _PRINT_CSS + html
    return html


def _chromium_executable() -> str | None:
    """Best-effort path to the pre-installed Chromium. Returns None to let
    Playwright resolve it itself (via PLAYWRIGHT_BROWSERS_PATH)."""
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    for pat in (f"{base}/chromium-*/chrome-linux/chrome",
                f"{base}/chromium/chrome-linux/chrome"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


def html_to_pdf(html: str, out_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    out_path = Path(out_path)
    with sync_playwright() as p:
        launch = {"args": ["--no-sandbox", "--disable-gpu"]}
        exe = _chromium_executable()
        if exe:
            launch["executable_path"] = exe
        browser = p.chromium.launch(**launch)
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(
            path=str(out_path),
            format="Letter",
            print_background=True,
            margin={"top": "9mm", "bottom": "9mm", "left": "10mm", "right": "10mm"},
        )
        browser.close()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python make_pdf.py <index.html | digest.json> [out.pdf]")
        return 1
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"input not found: {src}")
        return 1
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".pdf")
    html_to_pdf(html_from_input(src), out)
    print(f"✅  PDF written: {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
