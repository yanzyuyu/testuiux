# testuiux

Autonomous visual UI/UX defect detector and responsive layout verification engine powered by Playwright and Qwen2.5-VL. Captures multi-viewport screenshots, recognizes layout bugs, generates structured `report.json`, and triggers a lightweight triage model (SLM) to produce an executive briefing directly consumable by primary coding agents.

[![PyPI version](https://img.shields.io/pypi/v/testuiux.svg)](https://pypi.org/project/testuiux/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features

- **Zero Manual Setup**: Fully autonomous model lifecycle. Automatically detects local Ollama instances, boots the daemon in the background if closed, and pulls models on-demand.
- **Multi-Viewport Automated Capture**: Uses Playwright to render mobile (`375x812`), tablet (`768x1024`), and desktop (`1440x900`) viewports.
- **Vision-Language QA Inspection**: Evaluates screenshots with Qwen2.5-VL to spot element collisions, text overlap, truncation, unconstrained horizontal overflows, broken assets, and unreadable color contrast.
- **Visual Defect Highlighting**: Uses Pillow to render color-coded bounding boxes and severity badges.
- **Structured JSON Reporting**: Automatically exports `report.json` with coordinate boundaries, severity ratings, and CSS remedies.
- **Dual-Model Autonomous Triage**: Feeds raw audit data into a compact language model (`qwen2.5:1.5b`) to synthesize an executive briefing (`agent_briefing.txt`) for primary AI coding assistants.
- **Antigravity Skill Native**: Registered as a persistent skill (`testuiux`) invoked automatically whenever frontend UI changes are implemented.

## Requirements

- Python 3.10+
- Playwright Chromium (`playwright install chromium`)
- Ollama (optional, auto-detected if installed)

## Installation

Install directly from PyPI:

```bash
pip install testuiux
playwright install chromium
```

## Usage

### 1. Autonomous Run (Zero Configuration)

Point `testuiux` to any URL or local HTML file. The tool automatically detects runtime environment and produces JSON audit data with agent briefings:

```bash
testuiux http://localhost:3000
```

Or on local HTML files:

```bash
testuiux demo/buggy_site.html
```

### 2. Export All Formats (JSON + Side-by-Side HTML Report)

```bash
testuiux http://localhost:3000 --format all --output-dir ./audit_results
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
