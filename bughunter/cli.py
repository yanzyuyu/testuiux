import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from bughunter.schema import AuditReport
from bughunter.crawler import capture_viewports
from bughunter.detector import detect_visual_issues
from bughunter.annotator import annotate_image
from bughunter.reporter import generate_html_report
from bughunter.json_reporter import export_json_report
from bughunter.summarizer import generate_agent_briefing

console = Console()


async def run_audit(
    target: str,
    viewports: list[str],
    mode: str,
    api_base: str,
    model: str,
    api_key: str,
    output_dir: Path,
    small_model: str,
    notify: bool,
    format_type: str,
) -> tuple[AuditReport, str]:
    console.print(
        Panel(
            f"[bold cyan]Target:[/bold cyan] {target}\n"
            f"[bold cyan]Mode:[/bold cyan] {mode}\n"
            f"[bold cyan]Vision Model:[/bold cyan] {model if mode == 'api' else 'mock/heuristic'}\n"
            f"[bold cyan]Triage Model:[/bold cyan] {small_model if notify else 'disabled'}\n"
            f"[bold cyan]Format:[/bold cyan] {format_type}",
            title="Visual Bug Hunter",
        )
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    with console.status("[bold green]Capturing responsive viewports with Playwright..."):
        viewport_results = await capture_viewports(
            target_url=target,
            output_dir=output_dir,
            selected_viewports=viewports,
            full_page=True,
        )

    for vp in viewport_results:
        with console.status(f"[bold yellow]Analyzing visual issues for {vp.viewport_name} viewport..."):
            issues = await detect_visual_issues(
                image_path=Path(vp.screenshot_path),
                viewport_name=vp.viewport_name,
                mode=mode,
                api_base=api_base,
                model=model,
                api_key=api_key,
            )
            vp.issues = issues

            annotated_filename = f"annotated_{vp.viewport_name}.png"
            annotated_path = output_dir / annotated_filename
            annotate_image(
                screenshot_path=Path(vp.screenshot_path),
                issues=issues,
                output_path=annotated_path,
            )
            vp.annotated_path = str(annotated_path)

    report = AuditReport(
        target_url=target,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        viewports=viewport_results,
    )

    json_path = output_dir / "report.json"
    export_json_report(report, json_path)

    if format_type in ("html", "all"):
        report_html_path = output_dir / "report.html"
        generate_html_report(report, report_html_path)

    briefing = ""
    if notify:
        with console.status(f"[bold magenta]Generating agent briefing with small model ({small_model})..."):
            briefing = await generate_agent_briefing(
                report=report,
                api_base=api_base,
                model=small_model,
                api_key=api_key,
                use_small_model=(mode == "api"),
            )
            briefing_file = output_dir / "agent_briefing.txt"
            with open(briefing_file, "w", encoding="utf-8") as f:
                f.write(briefing)

    return report, briefing


def main():
    parser = argparse.ArgumentParser(description="Autonomous Visual Bug Hunter with Qwen2.5-VL")
    parser.add_argument("target", help="Target URL (e.g. http://localhost:3000) or local HTML file")
    parser.add_argument(
        "--viewports",
        default="mobile,desktop",
        help="Comma-separated viewports: mobile,tablet,desktop (default: mobile,desktop)",
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "api"],
        default="mock",
        help="Detection mode: mock (heuristic demo) or api (Qwen2.5-VL via Ollama/OpenAI)",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:11434/v1",
        help="Base URL for model endpoints (default: http://localhost:11434/v1)",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-vl:3b",
        help="Vision model name (default: qwen2.5-vl:3b)",
    )
    parser.add_argument(
        "--small-model",
        default="qwen2.5:1.5b",
        help="Small triage model for agent notification briefing (default: qwen2.5:1.5b)",
    )
    parser.add_argument(
        "--api-key",
        default="ollama",
        help="API Key for model endpoints",
    )
    parser.add_argument(
        "--output-dir",
        default="./audit_results",
        help="Directory to save artifacts (default: ./audit_results)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "all"],
        default="json",
        help="Report output format: json, html, or all (default: json)",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        default=True,
        help="Automatically trigger small model triage briefing for main AI agent",
    )
    parser.add_argument(
        "--no-notify",
        dest="notify",
        action="store_false",
        help="Disable triage briefing",
    )

    args = parser.parse_args()
    selected_viewports = [v.strip() for v in args.viewports.split(",") if v.strip()]
    out_dir = Path(args.output_dir).resolve()

    report, briefing = asyncio.run(
        run_audit(
            target=args.target,
            viewports=selected_viewports,
            mode=args.mode,
            api_base=args.api_base,
            model=args.model,
            api_key=args.api_key,
            output_dir=out_dir,
            small_model=args.small_model,
            notify=args.notify,
            format_type=args.format,
        )
    )

    table = Table(title="Visual QA Audit Summary")
    table.add_column("Viewport", style="cyan")
    table.add_column("Dimensions", style="dim")
    table.add_column("Defects Found", justify="right")
    table.add_column("Critical", justify="right", style="red")
    table.add_column("Warning", justify="right", style="yellow")

    for vp in report.viewports:
        crits = sum(1 for i in vp.issues if i.severity.value == "CRITICAL")
        warns = sum(1 for i in vp.issues if i.severity.value == "WARNING")
        table.add_row(
            vp.viewport_name,
            f"{vp.width}x{vp.height}",
            str(len(vp.issues)),
            str(crits),
            str(warns),
        )

    console.print(table)
    console.print(f"[bold green]JSON Report saved:[/bold green] {out_dir / 'report.json'}")

    if briefing:
        console.print(Panel(briefing, title="[bold magenta]AI Agent Executive Briefing (Small Model)[/bold magenta]", border_style="magenta"))


if __name__ == "__main__":
    main()
