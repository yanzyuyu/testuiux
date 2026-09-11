from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from bughunter.schema import SeverityLevel, VisualIssue

SEVERITY_COLORS = {
    SeverityLevel.CRITICAL: {"border": (220, 38, 38, 255), "fill": (220, 38, 38, 40)},
    SeverityLevel.WARNING: {"border": (217, 119, 6, 255), "fill": (217, 119, 6, 40)},
    SeverityLevel.INFO: {"border": (37, 99, 235, 255), "fill": (37, 99, 235, 30)},
}


def get_default_font(size: int = 14):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()


def annotate_image(
    screenshot_path: Path,
    issues: list[VisualIssue],
    output_path: Path,
) -> Path:
    base_img = Image.open(screenshot_path).convert("RGBA")
    overlay = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    img_w, img_h = base_img.size
    font = get_default_font(14)
    badge_font = get_default_font(12)

    for idx, issue in enumerate(issues, start=1):
        x1 = int((issue.box.xmin / 1000.0) * img_w)
        y1 = int((issue.box.ymin / 1000.0) * img_h)
        x2 = int((issue.box.xmax / 1000.0) * img_w)
        y2 = int((issue.box.ymax / 1000.0) * img_h)

        x1 = max(0, min(img_w - 1, x1))
        y1 = max(0, min(img_h - 1, y1))
        x2 = max(x1 + 10, min(img_w, x2))
        y2 = max(y1 + 10, min(img_h, y2))

        scheme = SEVERITY_COLORS.get(issue.severity, SEVERITY_COLORS[SeverityLevel.INFO])

        draw.rectangle([x1, y1, x2, y2], fill=scheme["fill"], outline=scheme["border"], width=3)

        badge_text = f"#{idx} [{issue.severity.value}] {issue.type.value}"
        text_bbox = draw.textbbox((x1, y1), badge_text, font=badge_font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        badge_y1 = max(0, y1 - text_h - 8)
        badge_y2 = badge_y1 + text_h + 8
        badge_x2 = min(img_w, x1 + text_w + 12)

        draw.rectangle([x1, badge_y1, badge_x2, badge_y2], fill=scheme["border"])
        draw.text((x1 + 6, badge_y1 + 4), badge_text, fill=(255, 255, 255, 255), font=badge_font)

    combined = Image.alpha_composite(base_img, overlay).convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(output_path, "PNG")
    return output_path
