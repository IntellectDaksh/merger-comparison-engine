# Merger Comparison Engine

A research application answering whether a bank merger changed the economics or the appearance of performance. Includes the real **Bank of Baroda / Vijaya Bank / Dena Bank** amalgamation effective 1 April 2019, primary-source evidence, reproducible arithmetic, peer sensitivity and a dated legal applicability matrix.

## Run

Python 3.10 or newer. No installation or network access is required for the dashboard, calculations, text review or exports.

```powershell
cd path\to\merger-engine
python app.py
```

Open **http://127.0.0.1:8840**. If `python` is unavailable on Windows, use `py -3 app.py`, or run `start.ps1` in PowerShell. Stop with Ctrl+C. A different local port is available through `--port 8841`.

The local server accepts only local access. It has no accounts, cloud storage, telemetry or investment-recommendation features. Do not expose the local server through a public tunnel. The Vercel site serves a read-only snapshot from `public/` and does not accept document uploads. Commercial use or personalized investment advice requires separate legal and security review.

## Use

1. Read the executive finding and distinguish reported facts, calculated estimates and interpretations.
2. Select a metric to inspect the combined baseline, waterfall and exact arithmetic. Unquantified effects stay inside the unexplained residual.
3. Inspect peer exclusions, the quarterly path, original observations and source links.
4. Export a self-contained readable HTML report or complete report JSON. Browser print can save the HTML as PDF.
5. In the local version, use Document Review to upload a permitted PDF/TXT/CSV/JSON excerpt or paste text. Extraction creates **unverified candidates**, never approved observations. Files are not retained.

Optional PDF extraction uses `pypdf`; install it in your own environment only if needed: `python -m pip install pypdf`. Scanned, encrypted, ambiguous or oversized PDFs require manual transcription/review. Text extracted from a PDF is not automatically trusted. No automatic crawling or third-party API keys are needed.

## Reproduce and extend

```powershell
python -m unittest discover -s tests -v
python report.py --output real-case-report.html
python ingestion.py permitted-excerpt.txt
python ingestion.py reviewed-observations.json --validate
python app.py --case reviewed-case.json
```

Read [the methodology](docs/METHODOLOGY.md), [data dictionary](docs/DATA-DICTIONARY.md) and [extension guide](docs/EXTENDING.md) before adding a case. Data and calculation specifications are separate: comparisons reference observation IDs, allowing additional supported banks and applicable NBFC metrics without adding calculation code. A new entity requires manual source and accounting-basis review. This is a curated working case, not an exhaustive exchange-wide merger scanner.

## Deliverables

- `data/case.json`: reported observations, entity resolution, sources, chronology and comparison specifications.
- `data/legal.json` and `docs/LEGAL-APPLICABILITY.md`: 26-row primary-source legal matrix as of 16 October 2026, with historical/current/future distinctions and unresolved questions.
- `real-case-report.html`: readable standalone export.
- `public/`: deployable, read-only dashboard and dated report snapshot.
- `docs/CASE-EVIDENCE.md`: case source and reconciliation notes.
- `docs/VERIFICATION.md`: tests run and remaining limitations.

The fictional Bank X/Y example exists only in unit tests. The real case is historical: a 2026 research date does not imply its financial observations are current results. No unsupported figure is estimated merely to fill the interface.
