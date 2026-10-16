# Adding a supported case

1. Obtain permitted issuer/exchange/regulatory documents and record rights. The application does not bypass access controls or automate restricted retrieval.
2. Review extracted candidates in the dashboard or run `python ingestion.py excerpt.txt`. Map legal entity identifiers, announcement, each approval, effective date and first combined period. Reject transactions that are only portfolio purchases or capital raises from the merger case type.
3. Create a JSON package with `observations`, `sources`, and `checks`. Every observation needs id/entity/period/metric/value/unit/basis/sourceId/locator plus `reviewed: true`. Source metadata needs id, HTTP(S) URL or uploaded-file SHA-256, publishedDate, retrievedAt and extractionMethod. The four `checks` keys `unit`, `period`, `subtotal`, and `source_reconciliation` must each be true after actual human review.
4. Run `python ingestion.py reviewed-observations.json --validate`. An error blocks adoption. Validation checks metadata and confirmations; it cannot prove a human's confirmation truthful or reconstruct a scanned source.
5. Copy the reviewed observations and sources into a case following `data/case.json`. Define comparisons by observation IDs. Use a numerator/denominator operand for a reconstructed value, or `{"reported":["observation-id"]}` for one unmodified issuer ratio. The latter is labelled reported, not independently reconstructed. Add peers, quarterly paths, unresolved eliminations and accounting differences explicitly.
6. Use the same reporting basis inside each operand. The engine normalizes INR units but blocks mismatched dates or accounting bases. To compare a bank to an NBFC, document harmonisation first; omit inapplicable bank-specific metrics rather than guessing equivalents.
7. Run `python app.py --case reviewed-case.json`, inspect every calculation and export. The report loader rejects unreviewed, unsourced and duplicate observations, validates reported units and applies the evidence-availability cutoff. The CLI file remains a trusted analyst configuration; human confirmation is not independent verification. Automatic causal verdict approval is disabled in this release, regardless of configuration flags.

## Minimal operand example

```json
{
  "id": "gross_npa_ratio",
  "acquirer": {"numerator": ["a-gnpa"], "denominator": ["a-gross-advances"]},
  "baseline": {"numerator": ["a-gnpa", "b-gnpa"], "denominator": ["a-gross-advances", "b-gross-advances"]},
  "post": {"numerator": ["combined-gnpa"], "denominator": ["combined-gross-advances"]},
  "notes": ["Disclose the status of intercompany eliminations here."],
  "evidence_gates": {"comparable": false, "independent_evidence": false, "peer_robust": false, "persistent": false, "transition": false}
}
```

These are schema identifiers, not financial observations or a real case. The fictional Bank X/Y numerical data is used only in tests.

## Supported boundary

Reusable amount ratios, issuer-reported metrics, local document classification, source review, peer median/sensitivity and portable exports are implemented. Automatic entity resolution across all exchange issuers, licensed scheduled feeds, OCR, trained table extraction, synthetic controls, inferred accounting adjustments, comprehensive NBFC-specific models and public multi-user operation are not implemented. New cases remain visibly incomplete until their evidence supports them.
