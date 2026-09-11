import httpx
from bughunter.schema import AuditReport

SUMMARY_SYSTEM_PROMPT = """You are a QA Triage Officer.
Given a raw JSON visual audit report containing UI defects, generate a concise, high-priority executive briefing for the Lead AI Developer.
Format:
- Verdict: PASS / FAIL / ACTION_REQUIRED
- Impact Summary: 1-2 bullet points highlighting critical UI breakages that block user experience.
- Priority Fixes: Numbered list with viewport, defect type, and specific CSS remedies.
Keep it strictly under 120 words. No greetings or pleasantries."""


def build_fallback_briefing(report: AuditReport) -> str:
    crit_issues = []
    warn_issues = []
    for vp in report.viewports:
        for iss in vp.issues:
            entry = f"[{vp.viewport_name.upper()}] {iss.type.value}: {iss.description} -> Fix: {iss.suggested_fix}"
            if iss.severity.value == "CRITICAL":
                crit_issues.append(entry)
            else:
                warn_issues.append(entry)

    verdict = "FAIL" if report.critical_count > 0 else ("WARN" if report.warning_count > 0 else "PASS")

    lines = [
        f"VERDICT: {verdict}",
        f"TOTAL DEFECTS: {report.total_issues} ({report.critical_count} Critical, {report.warning_count} Warning)",
    ]

    if crit_issues:
        lines.append("\nBLOCKING ISSUES:")
        for idx, item in enumerate(crit_issues[:3], 1):
            lines.append(f"{idx}. {item}")

    if warn_issues and len(crit_issues) < 3:
        lines.append("\nWARNINGS:")
        for idx, item in enumerate(warn_issues[:2], 1):
            lines.append(f"- {item}")

    return "\n".join(lines)


async def generate_agent_briefing(
    report: AuditReport,
    api_base: str = "http://localhost:11434/v1",
    model: str = "qwen2.5:1.5b",
    api_key: str = "ollama",
    use_small_model: bool = True,
) -> str:
    if not use_small_model:
        return build_fallback_briefing(report)

    serialized_issues = [
        {
            "viewport": vp.viewport_name,
            "type": iss.type.value,
            "severity": iss.severity.value,
            "description": iss.description,
            "suggested_fix": iss.suggested_fix,
        }
        for vp in report.viewports
        for iss in vp.issues
    ]

    prompt = f"Audit Report Data for {report.target_url}:\n{serialized_issues}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{api_base}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return build_fallback_briefing(report)
