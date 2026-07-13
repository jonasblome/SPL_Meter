"""Render a Python source file as 16:9 code images in VS Code Dark+ colors."""

import sys
from pathlib import Path

# Use Pygments from the project virtual environment (system Python has Pillow).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spl_meter_env" / "Lib" / "site-packages"))

from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.token import Token


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

SOURCE_FILE = Path(__file__).resolve().parent.parent / "src" / "AudioDeviceManager.py"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "presentation" / "code_images"

WIDTH = 1920
ASPECT_W = 16
ASPECT_H = 9
SLICE_HEIGHT = int(WIDTH * ASPECT_H / ASPECT_W)  # 1080

FONT_SIZE = 18
LINE_HEIGHT = 28
MARGIN_TOP = 40
MARGIN_BOTTOM = 40
MARGIN_LEFT = 30
LINE_NUMBER_WIDTH = 60
TEXT_X = MARGIN_LEFT + LINE_NUMBER_WIDTH
TEXT_RIGHT_MARGIN = 40

# Approximate VS Code Dark+ theme colors.
BG_COLOR = "#1E1E1E"
FG_COLOR = "#D4D4D4"
LINE_NUMBER_COLOR = "#858585"
LINE_NUMBER_BG = "#1E1E1E"

THEME = {
    Token.Comment: "#6A9955",
    Token.Comment.Single: "#6A9955",
    Token.Comment.Multiline: "#6A9955",
    Token.Comment.Special: "#6A9955",
    Token.Keyword: "#569CD6",
    Token.Keyword.Constant: "#569CD6",
    Token.Keyword.Declaration: "#569CD6",
    Token.Keyword.Namespace: "#569CD6",
    Token.Keyword.Pseudo: "#569CD6",
    Token.Keyword.Reserved: "#569CD6",
    Token.Keyword.Type: "#4EC9B0",
    Token.Name.Class: "#4EC9B0",
    Token.Name.Decorator: "#4EC9B0",
    Token.Name.Entity: "#4EC9B0",
    Token.Name.Exception: "#4EC9B0",
    Token.Name.Function: "#DCDCAA",
    Token.Name.Function.Magic: "#DCDCAA",
    Token.Name.Builtin: "#DCDCAA",
    Token.Name.Builtin.Pseudo: "#DCDCAA",
    Token.Name.Attribute: "#9CDCFE",
    Token.Name.Namespace: "#9CDCFE",
    Token.Name.Other: "#9CDCFE",
    Token.Name.Tag: "#569CD6",
    Token.Name.Variable: "#9CDCFE",
    Token.Name.Variable.Class: "#9CDCFE",
    Token.Name.Variable.Global: "#9CDCFE",
    Token.Name.Variable.Instance: "#9CDCFE",
    Token.Name.Variable.Magic: "#9CDCFE",
    Token.Literal.String: "#CE9178",
    Token.Literal.String.Affix: "#CE9178",
    Token.Literal.String.Backtick: "#CE9178",
    Token.Literal.String.Char: "#CE9178",
    Token.Literal.String.Delimiter: "#CE9178",
    Token.Literal.String.Doc: "#6A9955",
    Token.Literal.String.Double: "#CE9178",
    Token.Literal.String.Escape: "#D7BA7D",
    Token.Literal.String.Heredoc: "#CE9178",
    Token.Literal.String.Interpol: "#CE9178",
    Token.Literal.String.Other: "#CE9178",
    Token.Literal.String.Regex: "#CE9178",
    Token.Literal.String.Single: "#CE9178",
    Token.Literal.String.Symbol: "#CE9178",
    Token.Literal.Number: "#B5CEA8",
    Token.Literal.Number.Bin: "#B5CEA8",
    Token.Literal.Number.Float: "#B5CEA8",
    Token.Literal.Number.Hex: "#B5CEA8",
    Token.Literal.Number.Integer: "#B5CEA8",
    Token.Literal.Number.Oct: "#B5CEA8",
    Token.Operator: "#D4D4D4",
    Token.Operator.Word: "#569CD6",
    Token.Punctuation: "#D4D4D4",
    Token.Text: "#D4D4D4",
    Token.Text.Whitespace: "#D4D4D4",
    Token.Generic: "#D4D4D4",
    Token.Error: "#F44747",
}


def get_color(token_type):
    """Find the best matching theme color for a Pygments token type."""
    while token_type is not Token and token_type not in THEME:
        token_type = token_type.parent
    return THEME.get(token_type, FG_COLOR)


def load_font(size):
    """Try to load a monospace font; fall back to Pillow's default."""
    candidates = [
        "consola.ttf",
        "Consolas.ttf",
        "consolai.ttf",
        "cour.ttf",
        "Cour.ttf",
        "Courier New.ttf",
        "lucon.ttf",
        "DejaVuSansMono.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def split_tokens_by_line(tokens):
    """Yield (line_number, [(token_type, text), ...]) for each source line."""
    line_no = 1
    current_line = []
    for token_type, value in tokens:
        parts = value.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                yield line_no, current_line
                line_no += 1
                current_line = []
            if part or (i == len(parts) - 1 and not value.endswith("\n")):
                current_line.append((token_type, part))
    if current_line:
        yield line_no, current_line


def render_code_image(source_path, width=WIDTH):
    """Render the whole file as one vertically scrollable image."""
    code = source_path.read_text(encoding="utf-8")
    # Expand tabs so column alignment matches the editor.
    code = code.replace("\t", "    ")

    lexer = PythonLexer()
    tokens = list(lexer.get_tokens(code))

    font = load_font(FONT_SIZE)
    bold_font = load_font(FONT_SIZE)  # bold not always available; regular is fine

    # Measure character width using a typical character.
    char_width = font.getlength("M")
    text_max_width = width - TEXT_X - TEXT_RIGHT_MARGIN
    max_chars_per_line = max(1, int(text_max_width // char_width))

    lines = list(split_tokens_by_line(tokens))
    total_height = MARGIN_TOP + len(lines) * LINE_HEIGHT + MARGIN_BOTTOM

    img = Image.new("RGB", (width, total_height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = MARGIN_TOP
    for line_no, line_tokens in lines:
        # Line number sidebar
        draw.rectangle(
            [(MARGIN_LEFT, y), (MARGIN_LEFT + LINE_NUMBER_WIDTH, y + LINE_HEIGHT)],
            fill=LINE_NUMBER_BG,
        )
        draw.text(
            (MARGIN_LEFT + LINE_NUMBER_WIDTH - 10, y),
            str(line_no),
            fill=LINE_NUMBER_COLOR,
            font=font,
            anchor="rt",
        )

        # Code tokens
        x = TEXT_X
        for token_type, text in line_tokens:
            color = get_color(token_type)
            # Soft-wrap if a token is extremely long (unlikely here).
            if len(text) > max_chars_per_line:
                chunks = [text[i : i + max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
            else:
                chunks = [text]
            for chunk in chunks:
                draw.text((x, y), chunk, fill=color, font=font)
                x += font.getlength(chunk)
        y += LINE_HEIGHT

    return img


def slice_into_16_9(full_image, output_dir):
    """Cut the rendered image into 16:9 slices and save them."""
    output_dir.mkdir(parents=True, exist_ok=True)
    width, total_height = full_image.size
    slice_height = SLICE_HEIGHT

    slices = []
    for top in range(0, total_height, slice_height):
        bottom = min(top + slice_height, total_height)
        box = (0, top, width, bottom)
        crop = full_image.crop(box)
        # Pad the last slice to exactly 16:9.
        if crop.height < slice_height:
            padded = Image.new("RGB", (width, slice_height), BG_COLOR)
            padded.paste(crop, (0, 0))
            crop = padded
        slices.append(crop)

    for idx, img in enumerate(slices, start=1):
        out_path = output_dir / f"AudioDeviceManager_{idx:02d}.png"
        img.save(out_path, "PNG")
        print(f"Saved {out_path} ({img.width}x{img.height})")

    return slices


def main():
    print(f"Rendering {SOURCE_FILE} ...")
    full_image = render_code_image(SOURCE_FILE)
    print(f"Full rendered image: {full_image.width}x{full_image.height}")
    slices = slice_into_16_9(full_image, OUTPUT_DIR)
    print(f"Created {len(slices)} 16:9 image(s) in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
