import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from bughunter.schema import ViewportResult

VIEWPORT_CONFIGS = {
    "mobile": {
        "width": 375,
        "height": 812,
        "is_mobile": True,
        "device_scale_factor": 2,
    },
    "tablet": {
        "width": 768,
        "height": 1024,
        "is_mobile": True,
        "device_scale_factor": 2,
    },
    "desktop": {
        "width": 1440,
        "height": 900,
        "is_mobile": False,
        "device_scale_factor": 1,
    },
}


def normalize_target_url(target: str) -> str:
    if target.startswith(("http://", "https://", "file://")):
        return target
    local_path = Path(target).resolve()
    if local_path.exists():
        return local_path.as_uri()
    return f"https://{target}"


async def capture_single_viewport(
    browser,
    target_url: str,
    viewport_name: str,
    config: dict,
    output_dir: Path,
    full_page: bool = True,
) -> ViewportResult:
    context = await browser.new_context(
        viewport={"width": config["width"], "height": config["height"]},
        is_mobile=config.get("is_mobile", False),
        device_scale_factor=config.get("device_scale_factor", 1),
    )
    page = await context.new_page()

    try:
        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        await asyncio.sleep(0.5)

        screenshot_filename = f"screenshot_{viewport_name}.png"
        screenshot_path = output_dir / screenshot_filename

        await page.screenshot(
            path=str(screenshot_path),
            full_page=full_page,
        )

        return ViewportResult(
            viewport_name=viewport_name,
            width=config["width"],
            height=config["height"],
            screenshot_path=str(screenshot_path),
        )
    finally:
        await context.close()


async def capture_viewports(
    target_url: str,
    output_dir: Path,
    selected_viewports: list[str] | None = None,
    full_page: bool = True,
) -> list[ViewportResult]:
    normalized_url = normalize_target_url(target_url)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not selected_viewports:
        selected_viewports = list(VIEWPORT_CONFIGS.keys())

    results: list[ViewportResult] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for vp_name in selected_viewports:
                if vp_name not in VIEWPORT_CONFIGS:
                    continue
                cfg = VIEWPORT_CONFIGS[vp_name]
                res = await capture_single_viewport(
                    browser=browser,
                    target_url=normalized_url,
                    viewport_name=vp_name,
                    config=cfg,
                    output_dir=output_dir,
                    full_page=full_page,
                )
                results.append(res)
        finally:
            await browser.close()

    return results
