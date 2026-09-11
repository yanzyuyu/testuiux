import base64
import json
import re
from pathlib import Path
import httpx
from bughunter.schema import BoundingBox, IssueType, SeverityLevel, VisualIssue

SYSTEM_PROMPT = """You are an expert Frontend QA Engineer. Analyze this webpage screenshot and detect any visual bugs.
Look specifically for:
1. TEXT_OVERLAP: Text colliding or rendering directly over other text, images, or controls.
2. ELEMENT_COLLISION: Modals, fixed footers, or floating action buttons occluding underlying buttons or content.
3. HORIZONTAL_OVERFLOW: Elements overflowing beyond the viewport edge.
4. TEXT_TRUNCATION: Text awkwardly cut off or overflowing containers without ellipsis.
5. BROKEN_ASSET: Broken image placeholders, missing icons, stuck loaders.
6. CONTRAST_LOW: Text unreadable due to insufficient contrast against the background.

For each issue, return a JSON object with:
- type: TEXT_OVERLAP | ELEMENT_COLLISION | HORIZONTAL_OVERFLOW | TEXT_TRUNCATION | BROKEN_ASSET | CONTRAST_LOW
- severity: CRITICAL | WARNING | INFO
- description: Concise explanation of the visual defect
- suggested_fix: CSS or HTML rule to resolve it
- box_2d: [ymin, xmin, ymax, xmax] normalized to 0-1000

Output MUST be a valid JSON array of objects only. If no bugs exist, return []."""


def encode_image_base64(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def parse_llm_json(content: str) -> list[dict]:
    clean_str = content.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_str)
    if match:
        clean_str = match.group(1).strip()
    try:
        parsed = json.loads(clean_str)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "issues" in parsed and isinstance(parsed["issues"], list):
            return parsed["issues"]
        return []
    except json.JSONDecodeError:
        return []


def to_visual_issues(items: list[dict]) -> list[VisualIssue]:
    results: list[VisualIssue] = []
    for item in items:
        try:
            itype = IssueType(item.get("type", "TEXT_OVERLAP").upper())
        except ValueError:
            itype = IssueType.TEXT_OVERLAP

        try:
            sev = SeverityLevel(item.get("severity", "WARNING").upper())
        except ValueError:
            sev = SeverityLevel.WARNING

        box_raw = item.get("box_2d", [0, 0, 100, 100])
        if not (isinstance(box_raw, list) and len(box_raw) == 4):
            continue

        ymin, xmin, ymax, xmax = [max(0, min(1000, int(v))) for v in box_raw]
        if ymax <= ymin or xmax <= xmin:
            continue

        results.append(
            VisualIssue(
                type=itype,
                severity=sev,
                description=item.get("description", "Visual defect detected"),
                suggested_fix=item.get("suggested_fix", "Check CSS layout rules"),
                box=BoundingBox(ymin=ymin, xmin=xmin, ymax=ymax, xmax=xmax),
            )
        )
    return results


async def detect_via_api(
    image_path: Path,
    api_base: str = "http://localhost:11434/v1",
    model: str = "qwen2.5-vl:3b",
    api_key: str = "ollama",
) -> list[VisualIssue]:
    b64 = encode_image_base64(image_path)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": SYSTEM_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ],
        "temperature": 0.1,
    }

    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{api_base}/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        raw_issues = parse_llm_json(raw_text)
        return to_visual_issues(raw_issues)


def detect_mock(image_path: Path, viewport_name: str) -> list[VisualIssue]:
    issues: list[VisualIssue] = []
    if viewport_name == "mobile":
        issues.append(
            VisualIssue(
                type=IssueType.ELEMENT_COLLISION,
                severity=SeverityLevel.CRITICAL,
                description="Fixed bottom banner occludes the primary checkout CTA button.",
                suggested_fix="Increase main container padding-bottom: 80px or reduce banner height on mobile viewports.",
                box=BoundingBox(ymin=740, xmin=45, ymax=850, xmax=955),
            )
        )
        issues.append(
            VisualIssue(
                type=IssueType.TEXT_TRUNCATION,
                severity=SeverityLevel.WARNING,
                description="Product title overflows card boundaries and gets clipped abruptly.",
                suggested_fix="Apply text-overflow: ellipsis; overflow: hidden; white-space: nowrap; to title container.",
                box=BoundingBox(ymin=240, xmin=50, ymax=310, xmax=950),
            )
        )
        issues.append(
            VisualIssue(
                type=IssueType.HORIZONTAL_OVERFLOW,
                severity=SeverityLevel.CRITICAL,
                description="Pricing table width exceeds screen viewport creating unwanted horizontal scrolling.",
                suggested_fix="Set max-width: 100%; overflow-x: auto; or switch to stacked flex layout.",
                box=BoundingBox(ymin=420, xmin=30, ymax=650, xmax=1000),
            )
        )
    elif viewport_name == "desktop":
        issues.append(
            VisualIssue(
                type=IssueType.CONTRAST_LOW,
                severity=SeverityLevel.WARNING,
                description="Subheading text color #b0b0b0 has insufficient contrast ratio against #ffffff background.",
                suggested_fix="Change text color to #4a5568 or darker to meet WCAG AA 4.5:1 ratio requirement.",
                box=BoundingBox(ymin=150, xmin=120, ymax=195, xmax=880),
            )
        )
    return issues


async def detect_visual_issues(
    image_path: Path,
    viewport_name: str,
    mode: str = "mock",
    api_base: str = "http://localhost:11434/v1",
    model: str = "qwen2.5-vl:3b",
    api_key: str = "ollama",
) -> list[VisualIssue]:
    if mode == "mock":
        return detect_mock(image_path, viewport_name)
    return await detect_via_api(image_path, api_base=api_base, model=model, api_key=api_key)
