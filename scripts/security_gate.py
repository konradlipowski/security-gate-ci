import json
import os
import sys
from pathlib import Path

REPORTS_DIR = Path("reports")
GITLEAKS_JSON = REPORTS_DIR / "gitleaks.json"
TRIVY_SARIF = REPORTS_DIR / "trivy.sarif"
SEMGREP_SARIF = REPORTS_DIR / "semgrep.sarif"

def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def count_gitleaks_findings(data) -> int:
    if data is None:
        return 0
    if isinstance(data, list):
        return len(data)
    return 0

def count_sarif_results(sarif) -> int:
    if sarif is None:
        return 0
    try:
        runs = sarif.get("runs", [])
        total = 0
        for r in runs:
            results = r.get("results", [])
            total += len(results)
        return total
    except Exception:
        return 0

def write_summary_md(summary_md: str):
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        Path(p).write_text(summary_md, encoding="utf-8")

def main():
    gitleaks_data = load_json(GITLEAKS_JSON)
    trivy_data = load_json(TRIVY_SARIF)
    semgrep_data = load_json(SEMGREP_SARIF)

    gitleaks_count = count_gitleaks_findings(gitleaks_data)
    trivy_count = count_sarif_results(trivy_data)
    semgrep_count = count_sarif_results(semgrep_data)

    fail_reasons = []
    if gitleaks_count > 0:
        fail_reasons.append(f"Gitleaks: {gitleaks_count} potential secrets found")
    if trivy_count > 0:
        fail_reasons.append(f"Trivy: {trivy_count} HIGH/CRITICAL findings")
    if semgrep_count > 0:
        fail_reasons.append(f"Semgrep: {semgrep_count} findings")

    status = "PASS" if not fail_reasons else "FAIL"

    summary = []
    summary.append(f"# Security Gate: {status}\n")
    summary.append("## Findings summary\n")
    summary.append("| Tool | Findings |\n|---|---:|\n")
    summary.append(f"| Gitleaks | {gitleaks_count} |\n")
    summary.append(f"| Trivy (HIGH,CRITICAL) | {trivy_count} |\n")
    summary.append(f"| Semgrep | {semgrep_count} |\n")

    if fail_reasons:
        summary.append("\n## Fail reasons\n")
        for r in fail_reasons:
            summary.append(f"- {r}\n")

    summary.append("\n## Artifacts\n")
    summary.append("- Download `security-reports` artifact from the workflow run.\n")

    summary_md = "".join(summary)
    write_summary_md(summary_md)

    (REPORTS_DIR / "summary.md").write_text(summary_md, encoding="utf-8")
    (REPORTS_DIR / "summary.json").write_text(
        json.dumps(
            {
                "status": status,
                "gitleaks": gitleaks_count,
                "trivy": trivy_count,
                "semgrep": semgrep_count,
                "fail_reasons": fail_reasons,
            },
            indent=2
        ),
        encoding="utf-8"
    )

    if status == "FAIL":
        print("Security Gate FAIL")
        for r in fail_reasons:
            print("-", r)
        sys.exit(1)

    print("Security Gate PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()
