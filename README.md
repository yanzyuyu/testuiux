# testuiux

Autonomous visual UI/UX defect detector and responsive layout verification engine powered by Playwright and Qwen2.5-VL. Captures multi-viewport screenshots, recognizes layout bugs, generates structured `report.json`, and triggers a lightweight triage model (SLM) to produce an executive briefing directly consumable by primary coding agents.

## Features

- **Multi-Viewport Automated Capture**: Uses Playwright to render mobile (`375x812`), tablet (`768x1024`), and desktop (`1440x900`) viewports.
- **Vision-Language QA Inspection**: Evaluates screenshots with Qwen2.5-VL to spot element collisions, text overlap, truncation, unconstrained horizontal overflows, broken assets, and unreadable color contrast.
- **Visual Defect Highlighting**: Uses Pillow to render color-coded bounding boxes and severity badges.
- **Structured JSON Reporting**: Automatically exports `report.json` with coordinate boundaries, severity ratings, and CSS remedies.
- **Dual-Model Autonomous Triage**: Feeds raw audit data into a compact language model (`qwen2.5:1.5b`) to synthesize an executive briefing (`agent_briefing.txt`) for primary AI coding assistants.
- **Antigravity Skill Native**: Registered as a persistent skill (`testuiux`) invoked automatically whenever frontend UI changes are implemented.

## Requirements

- Python 3.10+
- Playwright Chromium (`playwright install chromium`)
- Ollama with `qwen2.5-vl:3b` and `qwen2.5:1.5b` (or `--mode mock` for dry-run verification)

## Installation

```bash
git clone https://github.com/yanzyuyu/testuiux.git
cd testuiux
pip install -r requirements.txt
playwright install chromium
```

## Usage

### 1. Test Run on Bundled Demo Fixture

Execute a verification run against `demo/buggy_site.html`:

```bash
python -m bughunter.cli demo/buggy_site.html --mode mock --format json
```

### 2. Live Scan with Local AI Models (Ollama)

Ensure local Ollama models are running:

```bash
ollama run qwen2.5-vl:3b
ollama run qwen2.5:1.5b
```

Run audit against development or staging server:

```bash
python -m bughunter.cli http://localhost:3000 --mode api --format json --notify
```

### 3. Generate All Artifacts (JSON + HTML Report)

```bash
python -m bughunter.cli http://localhost:3000 --mode api --format all --output-dir ./audit_results
```

## Generated Artifacts

```
audit_results/
├── report.json             # Structured machine-readable defects data
├── agent_briefing.txt      # Executive briefing for primary AI agent
├── report.html             # Standalone side-by-side comparison report
├── screenshot_mobile.png   # Clean capture
└── annotated_mobile.png    # Highlighted defects capture
```

## Defect Categories

| Issue Type | Description |
| :--- | :--- |
| `ELEMENT_COLLISION` | Fixed footers, modals, or floating buttons occluding interactive UI |
| `HORIZONTAL_OVERFLOW` | Containers exceeding screen boundaries causing horizontal scroll |
| `TEXT_OVERLAP` | Colliding labels or texts rendering over other visual components |
| `TEXT_TRUNCATION` | Prematurely clipped strings lacking proper CSS ellipsis rules |
| `BROKEN_ASSET` | Failed image requests and unrendered placeholder graphics |
| `CONTRAST_LOW` | Text violating accessibility contrast standards against background |

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
