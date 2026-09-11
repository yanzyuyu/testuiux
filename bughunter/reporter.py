import base64
from pathlib import Path
from bughunter.schema import AuditReport, SeverityLevel


def file_to_b64(path_str: str) -> str:
    p = Path(path_str)
    if not p.exists():
        return ""
    with open(p, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"


def generate_html_report(report: AuditReport, output_file: Path) -> Path:
    severity_styles = {
        SeverityLevel.CRITICAL: "background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171;",
        SeverityLevel.WARNING: "background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d;",
        SeverityLevel.INFO: "background-color: #dbeafe; color: #1e40af; border: 1px solid #93c5fd;",
    }

    viewports_html = []
    for vp in report.viewports:
        annotated_b64 = file_to_b64(vp.annotated_path) if vp.annotated_path else ""
        original_b64 = file_to_b64(vp.screenshot_path) if vp.screenshot_path else ""

        issues_html = []
        for idx, iss in enumerate(vp.issues, start=1):
            badge_style = severity_styles.get(iss.severity, severity_styles[SeverityLevel.INFO])
            issues_html.append(
                f"""
            <div class="issue-card">
                <div class="issue-header">
                    <span class="badge" style="{badge_style}">#{idx} {iss.severity.value}</span>
                    <span class="issue-type">{iss.type.value}</span>
                </div>
                <div class="issue-desc">{iss.description}</div>
                <div class="fix-box">
                    <div class="fix-label">Suggested Fix</div>
                    <code>{iss.suggested_fix}</code>
                </div>
            </div>
            """
            )

        issues_rendered = "".join(issues_html) if issues_html else "<p class='no-issues'>No visual issues detected for this viewport.</p>"

        viewports_html.append(
            f"""
        <section class="viewport-section" id="vp-{vp.viewport_name}">
            <div class="viewport-header">
                <h2>{vp.viewport_name.upper()} VIEWPORT</h2>
                <span class="meta-tag">{vp.width}px x {vp.height}px ({len(vp.issues)} issues)</span>
            </div>
            <div class="comparison-grid">
                <div class="image-box">
                    <h3>Annotated Defects</h3>
                    <div class="img-wrapper">
                        <img src="{annotated_b64}" alt="Annotated Screenshot" />
                    </div>
                </div>
                <div class="image-box">
                    <h3>Original Capture</h3>
                    <div class="img-wrapper">
                        <img src="{original_b64}" alt="Original Screenshot" />
                    </div>
                </div>
            </div>
            <div class="issues-list">
                <h3>Detected Issues & Recommendations</h3>
                <div class="cards-grid">
                    {issues_rendered}
                </div>
            </div>
        </section>
        """
        )

    all_viewports = "".join(viewports_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Bug Hunter Audit Report</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --primary: #38bdf8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            padding: 24px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
        }}
        .hero-title {{
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .target-url {{
            font-size: 14px;
            color: var(--primary);
            margin-top: 6px;
            font-family: monospace;
            word-break: break-all;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }}
        .stat-card {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }}
        .stat-val {{
            font-size: 32px;
            font-weight: 700;
        }}
        .stat-label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .val-total {{ color: var(--primary); }}
        .val-crit {{ color: var(--danger); }}
        .val-warn {{ color: var(--warning); }}
        .viewport-section {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 32px;
        }}
        .viewport-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        .viewport-header h2 {{
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}
        .meta-tag {{
            font-size: 12px;
            font-family: monospace;
            background-color: var(--bg);
            padding: 4px 10px;
            border-radius: 4px;
            color: var(--text-muted);
            border: 1px solid var(--border);
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        @media (max-width: 900px) {{
            .comparison-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .image-box h3 {{
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 8px;
            font-weight: 500;
        }}
        .img-wrapper {{
            background-color: #000;
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: auto;
            max-height: 600px;
            display: flex;
            align-items: flex-start;
            justify-content: center;
        }}
        .img-wrapper img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .issues-list h3 {{
            font-size: 16px;
            margin-bottom: 16px;
            color: var(--text-main);
        }}
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 16px;
        }}
        .issue-card {{
            background-color: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }}
        .issue-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }}
        .badge {{
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        .issue-type {{
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            font-family: monospace;
        }}
        .issue-desc {{
            font-size: 14px;
            color: var(--text-main);
            margin-bottom: 12px;
        }}
        .fix-box {{
            background-color: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 6px;
            padding: 10px;
        }}
        .fix-label {{
            font-size: 10px;
            text-transform: uppercase;
            color: var(--primary);
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .fix-box code {{
            font-family: "SFMono-Regular", Consolas, Menlo, monospace;
            font-size: 12px;
            color: #e2e8f0;
            display: block;
            word-break: break-word;
        }}
        .no-issues {{
            color: var(--success);
            font-size: 14px;
            padding: 12px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="hero-title">Visual Bug Hunter Audit Report</div>
            <div class="target-url">Audit Target: {report.target_url}</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Defects</div>
                    <div class="stat-val val-total">{report.total_issues}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Critical Issues</div>
                    <div class="stat-val val-crit">{report.critical_count}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Warnings</div>
                    <div class="stat-val val-warn">{report.warning_count}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Timestamp</div>
                    <div style="font-size: 14px; margin-top: 10px; color: var(--text-muted);">{report.timestamp}</div>
                </div>
            </div>
        </header>
        <main>
            {all_viewports}
        </main>
    </div>
</body>
</html>"""

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_file
