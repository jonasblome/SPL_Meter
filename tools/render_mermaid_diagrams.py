"""Extract Mermaid diagrams from a Markdown file, render them as PNGs
via https://mermaid.ink, and replace the code blocks with image references."""

import base64
import html
import json
import re
import urllib.request
from pathlib import Path


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

MARKDOWN_FILE = Path(__file__).resolve().parent.parent / "docs" / "architecture" / "architecture.md"
OUTPUT_DIR = MARKDOWN_FILE.parent / "images"
MERMAID_INK_URL = "https://mermaid.ink/img"
TIMEOUT_SECONDS = 30


def encode_for_mermaid_ink(code: str) -> str:
    """Encode Mermaid source for the mermaid.ink /img endpoint."""
    payload = json.dumps({"code": code}, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")
    # Strip any trailing '=' padding; mermaid.ink expects unpadded base64url.
    return encoded.rstrip("=")


def fetch_png(code: str) -> bytes:
    """Fetch a PNG rendering of the given Mermaid code from mermaid.ink."""
    encoded = encode_for_mermaid_ink(code)
    url = f"{MERMAID_INK_URL}/{encoded}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/png",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def process_markdown(md_path: Path, output_dir: Path) -> None:
    """Replace all ```mermaid blocks in the Markdown file with PNG images."""
    output_dir.mkdir(parents=True, exist_ok=True)
    text = md_path.read_text(encoding="utf-8")

    mermaid_pattern = re.compile(
        r"```mermaid\n(.*?)```",
        re.DOTALL,
    )

    replacements = []
    for index, match in enumerate(mermaid_pattern.finditer(text), start=1):
        raw_code = match.group(1)
        # Code in Markdown may contain HTML entities (e.g. &amp;); decode them.
        code = html.unescape(raw_code)

        filename = f"diagram_{index:03d}.png"
        image_path = output_dir / filename

        print(f"Rendering diagram {index} -> {image_path}")
        png_data = fetch_png(code)
        image_path.write_bytes(png_data)

        # Relative path from the Markdown file to the image.
        rel_path = image_path.relative_to(md_path.parent).as_posix()
        alt_text = f"Architecture diagram {index}"
        replacement = f"![{alt_text}]({rel_path})\n"
        replacements.append((match.start(), match.end(), replacement))

    if not replacements:
        print("No Mermaid diagrams found.")
        return

    # Apply replacements from the end so indices stay valid.
    new_text = text
    for start, end, replacement in reversed(replacements):
        new_text = new_text[:start] + replacement + new_text[end:]

    md_path.write_text(new_text, encoding="utf-8")
    print(f"Updated {md_path}")


def main():
    process_markdown(MARKDOWN_FILE, OUTPUT_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
