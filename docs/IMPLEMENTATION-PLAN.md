# Merger Comparison Engine implementation plan

**Goal:** A runnable, auditable local research application with a verified real merger and explicit evidence limits.

**Architecture:** Python standard-library calculation engine and loopback HTTP server, structured JSON evidence, and dependency-free HTML/CSS/JavaScript. Optional pypdf handles text PDFs; scanned material requires manual review. No database or remote service is needed.

**Spec:** The user's attached `Pasted text.txt` is controlling; `solution (1).docx` is a concept brief. In particular, unexplained changes are never themselves evidence of genuine improvement.

**Ruling:** Proceed without another design approval because the user expressly asks for complete implementation and reasonable assumptions. This new empty workspace has no application or repository to preserve. The imported MASTER-OPERATING-PROMPT.md could not be located in available likely locations; supplied instructions remain in force.

## Scope and interfaces

- `engine.py`: amount-based ratios, restatement selection, exact bridges, peer sensitivity, conservative verdict gates.
- `ingestion.py`: local document event discovery, extraction candidates, reviewed-observation validation. No uncertain candidate enters calculations.
- `report.py`: verified evidence adapter, report assembly, escaped portable HTML export.
- `app.py`: local read-only report endpoints and ephemeral document-review endpoint.
- `public/`: accessible dashboard consuming `/report.json`; numeric charts have tables.
- `data/case.json`, `data/legal.json`: independently researched primary-source evidence.
- `tests/`: reconstruction, missingness, restatements, denominator interactions, peers, import validation, security and HTTP integration.
- `docs/`: methodology, dictionary, case evidence, legal applicability, verification and extension instructions.

## Execution

- [x] Write failing numerical tests, implement and run the numerical suite.
- [x] Research the BoB/Vijaya/Dena case and applicable law in parallel with the interface.
- [x] Write failing review/import tests, implement candidate discovery and validation.
- [x] Adapt the verified case into every required metric, showing unsupported metrics without fabricated values.
- [x] Integrate dashboard, readable export, setup commands and case extension example.
- [x] Run the full suite and live HTTP/browser checks; review boundary cases; package deliverables.

## Review focus

Missing denominators must not become zero; rounded reported ratios must not fabricate amounts; FY and quarter definitions must not mix; restatements must respect publication cutoffs; uncertainty must not become causal certainty; uploaded HTML must remain text; server must not serve the filesystem or retain uploaded personal documents.

Final scope and unresolved evidence are recorded in VERIFICATION.md; checklist completion does not imply full causal or legal verification.
