# Career Forge — AI Resume & Job Match Studio (`career-forge`)

**Built for the Anna AI OS Founding Builder Challenge 2026**

Career Forge is a complete, Schema-3 Anna App bundling:

1. **Interactive Studio UI (`bundle/`)** — A responsive dark/light Web UI connected to Anna via `AnnaAppRuntime` (`/static/anna-apps/_sdk/latest/index.js`).
2. **Python Executa Backend (`executas/career-engine-python/`)** — A zero-external-dependency JSON-RPC 2.0 over stdio Python plugin (`career_engine_plugin.py`) that performs deterministic ATS skill/keyword gap analysis, XYZ bullet rewriting, tailored cover letter & cold DM generation, STAR interview prep, and scan history persistence.
3. **Multi-platform binary distribution** — PyInstaller one-file binaries for `darwin-arm64`, `darwin-x86_64`, `linux-x86_64` (the Cloud Agent binary) and `windows-x86_64`, built by GitHub Actions and uploaded with `anna-app apps publish`.

---

## Project Layout

```text
career-forge/
├── app.json                                  # Store listing metadata + bundled_executas map + screenshots
├── manifest.json                             # Schema 3 AppManifest (UI, storage, host_api ACL)
├── assets/
│   ├── logo.png                              # 256x256 store logo
│   └── shot-1..4.png                         # REAL in-app screenshots (scan / XYZ / cover / interview)
├── bundle/
│   ├── index.html                            # App UI entry point
│   ├── style.css                             # Dark/Light responsive studio styles
│   ├── app.js                                # ESM controller using AnnaAppRuntime SDK
│   ├── anna-tool-ids.js                      # Maps bundled handle -> tool_id (auto-generated on publish)
│   └── icon.svg                              # App vector icon
├── executas/
│   └── career-engine-python/
│       ├── executa.json                      # Executa descriptor (distribution.active: "binary")
│       ├── pyproject.toml                    # uv / setuptools entrypoint config
│       ├── career_engine_plugin.py           # JSON-RPC 2.0 stdio plugin
│       └── dist/                             # <-- downloaded archives (git-ignored, never committed)
├── scripts/
│   ├── download-binaries.ps1                 # Fetch the 4 release archives into dist/ (Windows)
│   └── download-binaries.sh                  # Same for macOS / Linux
├── .github/workflows/
│   └── build-executa-binaries.yml            # 4-platform PyInstaller build -> GitHub Release
└── tests/
    └── test_plugin.py                        # Automated JSON-RPC contract tests
```

---

## Step-by-Step Commands to Run, Validate & Publish on Anna

### Step 1: Prerequisites

```bash
# Astral uv (runs Python Executas locally)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Anna App CLI (requires Node 22+)
npm i -g @anna-ai/cli

anna-app doctor
anna-app login --host https://anna.partners
```

### Step 2: Test the plugin + validate the app

```bash
cd career-forge
python3 -m unittest tests/test_plugin.py
anna-app validate --strict
```

### Step 3: Local dev

```bash
anna-app dev            # needs a PAT on disk (run `anna-app login` first)
anna-app dev --no-llm   # fully offline
```

Open `http://localhost:5180`.

### Step 4 (REQUIRED for review): build the 4 platform binaries

The Agent installs a **real binary** per platform. If `distribution.active` is
`local`, the store page labels the tool **LOCAL** and the app hangs on
*"Preparing tools for this app…"* on the Cloud Agent — so the binaries must exist.

1. Push this project to a GitHub repo.
2. **Actions → `Build Career Engine Executa Binaries` → Run workflow**, with
   `version` = the `version` in `executas/career-engine-python/executa.json` (e.g. `1.0.1`).
3. Wait for all four jobs. **Confirm the `linux-x86_64` job is green** — that is
   the binary the Cloud Agent runs (built inside `manylinux_2_28`, so it only
   needs glibc ≥ 2.28).
4. A release `career-engine-v1.0.1` appears with the 4 archives + `.sha256` files.

### Step 5: Download the archives into `dist/`

```powershell
# Windows (PowerShell) — from the project root
pwsh .\scripts\download-binaries.ps1 -Version 1.0.1 -Repo <owner>/<repo>
```

```bash
# macOS / Linux
bash scripts/download-binaries.sh 1.0.1 <owner>/<repo>
```

You should now have exactly:

```text
executas/career-engine-python/dist/
├── career-engine-1.0.1-darwin-arm64.tar.gz
├── career-engine-1.0.1-darwin-x86_64.tar.gz
├── career-engine-1.0.1-linux-x86_64.tar.gz
└── career-engine-1.0.1-windows-x86_64.zip
```

### Step 6: Publish + submit for review

```bash
anna-app apps publish        # uploads UI bundle + 4 binaries, cuts v1.0.1
anna-app apps status career-forge
anna-app apps submit-review  # -> PENDING_REVIEW
```

### Step 7: Test on a Cloud Agent (do this before submitting)

Anna reviewed on a **Cloud Agent (Linux)**. After publishing, install your own
app on a Cloud Agent and walk the full flow: open the app → run an ATS scan →
XYZ rewrites → cover letter → interview prep. Only submit once that works.

### Step 8: Release

```bash
anna-app apps release 1.0.1
```

---

## Notes

- `executa.json` keeps **both** profiles: `local` (for `anna-app dev`, which
  runs the plugin straight from Python) and `binary` (used for publishing).
  Only `distribution.active` decides what gets published — keep it `"binary"`.
- Binaries are **never** committed: `executas/*/dist/` is git-ignored; they are
  built in CI, hosted on a GitHub Release, downloaded locally, then pushed to
  the Anna CDN by `anna-app apps publish`.
- The store screenshots in `assets/` are genuine captures of the running app
  (real scan results, real Executa output), not mock-ups.
