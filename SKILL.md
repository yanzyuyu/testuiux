---
name: testuiux
description: >-
  MANDATORY: Execute during or immediately after creating, serving, or modifying ANY frontend UI, web page, HTML template, CSS styling, or responsive layout.
  Autonomous visual UI/UX defect detector and responsive layout verification engine.
  Captures multi-viewport screenshots (mobile 375x812, tablet 768x1024, desktop 1440x900) via Playwright,
  evaluates visual defects with Qwen2.5-VL (element collision, text overlap, truncation, horizontal overflow, broken assets, contrast issues),
  exports structured report.json, and triggers a compact triage model (qwen2.5:1.5b) to deliver a high-priority executive briefing
  directly to the primary coding AI.
---

# testuiux: Autonomous Visual QA & UI/UX Verification Skill

Trigger this skill whenever you write or modify frontend code (HTML, CSS, JSX, TSX, Vue, Svelte, Tailwind, responsive templates) or serve a local development server.

## Installation

```bash
pip install testuiux
playwright install chromium
```

## When to Execute

1. **Post-Frontend Edits:** After changing CSS layout, components, navigation, modals, or footers.
2. **Responsive Verification:** Before declaring completion on any UI task to verify mobile (`375px`), tablet (`768px`), and desktop (`1440px`) layouts.
3. **Pre-Ship QA:** To guarantee zero horizontal scrollbars, zero occluded CTA buttons, and zero broken asset placeholders.

## Execution Command

Run the audit CLI against the target page or local development server:

```bash
testuiux <TARGET_URL_OR_FILE> --format json --notify --output-dir audit_results
```

For dry-run / mock verification without active Ollama instance:
```bash
testuiux <TARGET_URL_OR_FILE> --mode mock --format json --output-dir audit_results
```

## Primary AI Ingestion Flow

1. Read `audit_results/agent_briefing.txt` for immediate executive triage:
   - **Verdict**: PASS / FAIL / ACTION_REQUIRED.
   - **Blocking Issues**: Critical collisions or overflows requiring instant fixes.
2. If blocking issues exist, inspect `audit_results/report.json` for precise element bounding boxes and CSS remedies.
3. Apply the suggested CSS fixes to the codebase.
4. Re-run `testuiux` to verify resolution.
