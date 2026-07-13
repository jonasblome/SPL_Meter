"""Extract Mermaid diagrams from a Markdown file, render them as PNGs
via https://mermaid.ink, and replace the code blocks with image references.

Usage
-----
Normal mode  – finds ```mermaid blocks, renders them, replaces with ![...](...):
    python render_mermaid_diagrams.py

Rerender mode – re-renders the stored diagram sources without touching the Markdown:
    python render_mermaid_diagrams.py --rerender
"""

import base64
import html
import json
import re
import sys
import urllib.request
from pathlib import Path


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

MARKDOWN_FILE = Path(__file__).resolve().parent.parent / "docs" / "architecture" / "architecture.md"
OUTPUT_DIR = MARKDOWN_FILE.parent / "images"
MERMAID_INK_URL = "https://mermaid.ink/img"
TIMEOUT_SECONDS = 30

# Stored Mermaid sources — updated automatically by process_markdown() and
# kept here so --rerender can re-fetch PNGs without needing the code blocks.
DIAGRAMS = [
    (
        "diagram_001.png",
        """graph TB
    subgraph Hardware["Hardware (Raspberry Pi Zero W)"]
        MIC["ICS43434 I2S-Mikrofon<br/>GPIO 18/19/20/21<br/>Sel → GND"]
    end

    subgraph AudioLayer["Audio-Schicht"]
        ADM["AudioDeviceManager<br/>(src/AudioDeviceManager.py)<br/>─────────────────<br/>PyAudio Stream<br/>I2S 32-bit PCM → 24-bit<br/>Normalisierung auf float<br/>Stereo → Mono<br/>WAV-Datei-Aufnahme"]
        SIM["AudioDeviceSimulator<br/>(src/AudioDeviceSimulator.py)<br/>─────────────────<br/>WAV-Datei als Quelle<br/>Gleiche Schnittstelle<br/>wie AudioDeviceManager"]
        AP["AudioProcessor<br/>(src/AudioProcessor.py)<br/>─────────────────<br/>RMS / Peak / SPL<br/>A-Gewichtung (IEC 61672)<br/>Oktavfilterbank (10 Bänder)<br/>Zeitbewertung Fast / Slow<br/>Leq-Messung"]
        HLP["helpers.py<br/>─────────────<br/>A-Gewichtungs-<br/>tabellen (Oktave &<br/>Terz-Oktave)"]
    end

    subgraph AppLayer["Anwendungs-Schicht"]
        SPLM["SPLMeter<br/>(src/SPLMeter.py)<br/>─────────────────<br/>Komposition aller Module<br/>Auswahl Real / Simulator"]
        MAIN["main.py<br/>─────────────<br/>Einstiegspunkt<br/>--simulate Flag"]
    end

    subgraph UILayer["Präsentations-Schicht"]
        UI["UIHandler<br/>(src/UIHandler.py)<br/>─────────────────<br/>Flask Web-Server :8501<br/>Server-Sent Events (60 Hz)<br/>REST-API"]
        BROWSER["Browser<br/>─────────────<br/>Web-UI<br/>Echtzeit-Anzeige"]
    end

    MIC -->|"I2S"| ADM
    ADM -->|"audio_callback()"| AP
    SIM -->|"_process_chunk()"| AP
    HLP --> AP
    AP -->|"latest_* Werte"| ADM
    AP -->|"latest_* Werte"| SIM
    MAIN --> SPLM
    SPLM -->|simulate=False| ADM
    SPLM -->|simulate=True| SIM
    SPLM --> UI
    ADM -->|"Messwerte"| UI
    SIM -->|"Messwerte"| UI
    UI -->|"SSE /stream"| BROWSER
    BROWSER -->|"POST /start /stop /calibrate ..."| UI
""",
    ),
    (
        "diagram_002.png",
        """flowchart LR
    A["ICS43434\\nMikrofon"] -->|"I2S 32-bit"| B["PyAudio\\nCallback"]
    B -->|">> 8 Bit-Shift\\n÷ 2²³ → float"| C["Mono-Konvertierung\\n(Stereo → Mono)"]
    C --> D["AudioProcessor"]

    D --> E["SPL\\n20·log₁₀(RMS/20µPa)"]
    D --> F["A-Gewichtung\\n10 Oktav-Bänder\\nIEC 61672"]
    D --> G["Zeitbewertung\\nFast τ=125ms\\nSlow τ=1s"]
    D --> H["Leq-Messung\\nenergeti-\\nsches Mittel"]

    E & F & G & H --> I["latest_* Felder\\nin AudioDeviceManager"]
    I -->|"SSE ~60 Hz"| J["Web-UI\\nBrowser"]
""",
    ),
    (
        "diagram_003.png",
        """classDiagram
    class AudioProcessor {
        +sample_rate: int
        +fast_state: float
        +slow_state: float
        +leq_is_running: bool
        +leq_result_db: float
        +compute_rms(audio_data)
        +compute_peak(audio_data)
        +compute_spl_db(audio_data)
        +compute_fast_state(audio_data)
        +compute_slow_state(audio_data)
        +design_a_weighting_filterbank(sample_rate)
        +apply_filterbank(audio_data, filterbank)
        +compute_a_weighting(filtered_signals)
        +start_leq_measurement(duration_s, sample_rate)
        +process_leq_measurement(audio_data)
        +reset_leq_measurement()
    }
""",
    ),
    (
        "diagram_004.png",
        """sequenceDiagram
    participant B as Browser
    participant F as Flask (UIHandler)
    participant D as AudioDeviceManager

    B->>F: POST /start
    F->>D: start_recording() [Thread]
    B->>F: GET /stream (SSE)
    loop ~60 Hz
        F-->>B: data: {spl_db, rms, peak, a_weighted, fast, slow, filterband_spl_db, leq_db}
    end
    B->>F: POST /leq_start
    F->>D: audio_processor.start_leq_measurement()
    B->>F: POST /calibrate {reference_db}
    F->>D: calibrate_microphone(reference_db)
    B->>F: POST /stop
    F->>D: stop_recording()
""",
    ),
]


def encode_for_mermaid_ink(code: str, theme: str = "dark") -> str:
    """Encode Mermaid source for the mermaid.ink /img endpoint."""
    payload = json.dumps(
        {"code": code, "mermaid": {"theme": theme}},
        separators=(",", ":"),
    )
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


def rerender_all(output_dir: Path) -> None:
    """Re-render all diagrams from the stored DIAGRAMS list (dark theme)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, code in DIAGRAMS:
        image_path = output_dir / filename
        print(f"Rendering {filename} -> {image_path}")
        png_data = fetch_png(code)
        image_path.write_bytes(png_data)
    print(f"Done. {len(DIAGRAMS)} diagram(s) written to {output_dir}")


def main():
    if "--rerender" in sys.argv:
        rerender_all(OUTPUT_DIR)
    else:
        process_markdown(MARKDOWN_FILE, OUTPUT_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
