# Security Gate CI (Trivy + Gitleaks + Semgrep)

A lightweight, portfolio-ready **Security Gate** for GitHub repositories.  
It runs **secret scanning (Gitleaks)**, **vulnerability scanning (Trivy)**, and **SAST (Semgrep)** on every `push` and `pull_request`, generates **reports**, and fails the pipeline if the policy is violated.

---

## Badges

![CI](https://img.shields.io/badge/GitHub%20Actions-Security%20Gate-blue)
![Security](https://img.shields.io/badge/Security-Trivy%20%7C%20Gitleaks%20%7C%20Semgrep-purple)
![Reports](https://img.shields.io/badge/Reports-Artifact%20%2B%20Summary-informational)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

---

## Features

- **Gitleaks**: detects accidental secret leaks (API keys, tokens, private keys).
- **Trivy (fs scan)**: finds HIGH/CRITICAL vulnerabilities in dependencies and (depending on repo content) risky configs.
- **Semgrep (OWASP Top 10 ruleset)**: static analysis for common risky patterns in code.
- **Security Gate policy**: one decision step (`scripts/security_gate.py`) that outputs **PASS/FAIL**.
- **Reports**:
  - `reports/gitleaks.json`
  - `reports/trivy.sarif`
  - `reports/semgrep.sarif`
  - `reports/summary.md` + `reports/summary.json`
- **Artifacts**: downloadable `security-reports` artifact in the workflow run.
- Optional: SARIF upload to GitHub Security tab (enabled if available for the repo).

---

## Policy (MVP)

The pipeline FAILS if:

- Gitleaks finds **≥ 1** potential secret  
- Trivy finds **≥ 1** HIGH/CRITICAL issue (workflow filters to `HIGH,CRITICAL`)  
- Semgrep finds **≥ 1** finding  

Adjust policy in: `scripts/security_gate.py`

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── security-gate.yml
├── scripts/
│   └── security_gate.py
├── src/
│   └── app.js
├── gitleaks.toml
├── .semgrepignore
├── .gitignore
└── README.md
```

---

## Installation

No local installation is required to run the CI pipeline (GitHub Actions runs it for you).  
Optional: run the scanners locally to debug findings.

### Optional local tools (Linux/macOS)

- Docker (for running Gitleaks container)
- Python 3.11+ (for Semgrep CLI + gate script)
- Trivy binary (optional, if you want to run Trivy locally)

---

## Run Locally (Optional)

Clone the project:

```bash
git clone https://github.com/konradlipowski/security-gate-ci.git
cd security-gate-ci
```

Create `reports/` folder:

```bash
mkdir -p reports
```

### Semgrep (local)

```bash
python3 -m pip install --upgrade pip
pip install semgrep

semgrep scan \
  --config p/owasp-top-ten \
  --sarif-output reports/semgrep.sarif \
  --metrics=off \
  --quiet || true
```

### Gitleaks (local via Docker)

```bash
docker pull zricethezav/gitleaks:latest

docker run --rm \
  -v "$PWD:/repo" \
  -w /repo \
  zricethezav/gitleaks:latest \
  git \
  --config gitleaks.toml \
  --report-format json \
  --report-path reports/gitleaks.json \
  --redact 100 \
  --exit-code 0
```

### Trivy (local, if installed)

```bash
trivy fs \
  --severity HIGH,CRITICAL \
  --ignore-unfixed \
  --format sarif \
  --output reports/trivy.sarif \
  .
```

### Run the Security Gate script (local)

This step evaluates already-generated reports and produces summary files.

```bash
python3 scripts/security_gate.py
```

Output files:

- `reports/summary.md`
- `reports/summary.json`

---

## CI / Deployment

This repo uses GitHub Actions as the “deployment” mechanism for security scanning.

On every `push` to `main` and every `pull_request`, the workflow:

1. Runs **Gitleaks**
2. Runs **Trivy**
3. Runs **Semgrep**
4. Runs **Security Gate** (PASS/FAIL decision)
5. Uploads `reports/` as artifact `security-reports`

Workflow file: `.github/workflows/security-gate.yml`

---

## Branch Protection (Recommended)

To enforce the gate (block merges when FAIL):

1. Go to **Settings → Branches → Add branch protection rule**
2. Select branch `main`
3. Enable:
   - **Require a pull request before merging**
   - **Require status checks to pass before merging**
4. Select the status check:
   - `Security Gate / security-gate`

---

## Usage / Demo (FAIL → PASS)

Create a branch that introduces a **fake** secret to show the gate working:

```bash
git checkout -b demo/fail-gate
mkdir -p demo
echo 'AWS_SECRET_KEY=THIS_IS_NOT_A_REAL_SECRET_1234567890' > demo/leak.txt
git add demo/leak.txt
git commit -m "Demo: fake secret to show gate blocking"
git push -u origin demo/fail-gate
```

Open a PR to `main`:

- The workflow should FAIL due to **Gitleaks**.

Then remove the file and push again:

```bash
rm demo/leak.txt
git add -A
git commit -m "Fix: remove fake secret"
git push
```

The workflow should PASS.

---

## Reports

After each workflow run:

1. Open the run in **Actions**
2. Download artifact: **security-reports**
3. Files included:

- `reports/gitleaks.json` (secret findings)
- `reports/trivy.sarif` (HIGH/CRITICAL findings)
- `reports/semgrep.sarif` (SAST findings)
- `reports/summary.md` (human-friendly)
- `reports/summary.json` (machine-friendly)

---

## Screenshots

1. FAIL run (PR with fake secret)
2. PASS run (after fix)

```md
![FAIL run](docs/screenshots/fail.png)
![PASS run](docs/screenshots/pass.png)
```

---

## Troubleshooting

### No results in “Security” tab
SARIF upload to GitHub Code Scanning may be unavailable depending on repo visibility/plan/settings.  
Even if upload is not available, the workflow still produces SARIF files and artifacts.

### Gitleaks finds false positives
Use allowlists in `gitleaks.toml` or add specific paths/patterns to ignore.

### Semgrep too noisy
Switch ruleset to something narrower or stricter, e.g.:

- `p/security-audit` (often broader)
- custom rules (best for “v2”)

---

## Appendix

### Why these tools?
- **Gitleaks** prevents the most common and damaging mistake — committing secrets.
- **Trivy** quickly flags critical dependency issues (CVE exposure).
- **Semgrep** catches risky coding patterns early, before runtime.

### Next steps (v2 upgrades)
- Add Trivy config scan (Terraform/K8s) if present
- Implement severity filtering for Semgrep (fail only on high confidence)
- Publish an HTML report via GitHub Pages
- Add baseline suppression for known accepted risks

---

## License

MIT
