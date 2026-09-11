import json
from pathlib import Path
from bughunter.schema import AuditReport


def export_json_report(report: AuditReport, output_file: Path) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_dict = report.model_dump()
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)
    return output_file
