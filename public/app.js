"use strict";

const finite = value => typeof value === "number" && Number.isFinite(value);
const list = value => Array.isArray(value) ? value : value == null ? [] : [value];
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const describe = value => value == null ? "Not available" : typeof value === "object" ? JSON.stringify(value) : String(value);
const safeUrl = value => { try { const url = new URL(String(value)); return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password ? url.href : null; } catch { return null; } };
const formatNumber = (value, signed = false) => finite(value) ? new Intl.NumberFormat("en-IN", {maximumFractionDigits:4, signDisplay:signed ? "exceptZero" : "auto"}).format(value) : "Not available";
const formatLevel = (value, unit = "") => finite(value) ? `${formatNumber(value)}${unit === "%" || unit === "percent" ? "%" : unit ? ` ${unit}` : ""}` : "Not available";
const changeUnit = metric => ["%", "percent", "percentage"].includes(metric.unit) ? "pp" : metric.unit || "";
const formatChange = (value, metric) => finite(value) ? `${formatNumber(value, true)} ${changeUnit(metric)}`.trim() : "Not available";
const factValue = value => finite(value) ? value : value && finite(value.value) ? value.value : null;
const paragraphs = value => list(value).map(item => `<p>${escapeHtml(describe(item))}</p>`).join("") || '<p class="muted">Not documented in the available evidence.</p>';
const bullets = value => `<ul class="compact-list">${list(value).map(item => `<li>${escapeHtml(describe(item))}</li>`).join("")}</ul>`;
const link = (url, label) => safeUrl(url) ? `<a href="${escapeHtml(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}<span class="sr-only"> (opens in new tab)</span></a>` : escapeHtml(label);

function bridgeSteps(metric) {
  const components = [["Acquirer before",metric.acquirer,"level"],["Mechanical / mix",metric.mechanical,"change"],["Accounting / presentation",metric.accounting,"change"],["One-offs / relief",metric.one_off,"change"],["Sector movement",metric.sector,"change"],["Unexplained + unquantified",metric.residual,"residual"],["After · basis noted",metric.post,"level"]];
  if ([metric.acquirer,metric.mechanical,metric.residual,metric.post].some(value => !finite(value))) return null;
  let cumulative = metric.acquirer;
  return components.map(([label,value,kind], index) => {
    if (!finite(value)) return {label,value:null,kind,start:null,end:null};
    const start = kind === "level" ? 0 : cumulative;
    const end = kind === "level" ? value : cumulative + value;
    if (index > 0 && kind !== "level") cumulative = end;
    return {label,value,kind,start,end};
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {finite, safeUrl, escapeHtml, formatNumber, bridgeSteps};
  if (require.main === module && process.argv.includes("--self-test")) {
    const assert = require("node:assert/strict");
    const rows = bridgeSteps({acquirer:2,mechanical:-.3,accounting:.1,one_off:0,sector:-.2,residual:.4,post:2});
    assert.ok(Math.abs(rows.at(-2).end - 2) < 1e-12);
    assert.equal(bridgeSteps({acquirer:2}), null);
    const unknown = bridgeSteps({acquirer:2,mechanical:-.3,accounting:null,one_off:null,sector:-.2,residual:.5,post:2});
    assert.equal(unknown[2].value, null);
    assert.equal(unknown.at(-2).end, 2);
    assert.equal(formatNumber(null), "Not available");
    assert.equal(safeUrl("javascript:alert(1)"), null);
    assert.equal(escapeHtml('<script>"&'), "&lt;script&gt;&quot;&amp;");
    console.log("PASS: bridge arithmetic, missing data, URL validation and HTML escaping");
  }
}

if (typeof document !== "undefined") {
  const $ = id => document.getElementById(id);
  let report = null;
  let observationPage = 0;
  let pdfFile = null;
  let draftChanged = false;
  const localReview = ["127.0.0.1", "localhost"].includes(location.hostname);
  if (localReview) {
    $("review").hidden = false;
    document.querySelector('a[href="#review"]').hidden = false;
  }

  function sourceLinks(references) {
    const sources = list(report?.case?.sources);
    return `<div class="source-links">${list(references).map(reference => {
      const source = typeof reference === "object" ? reference : sources.find(item => item.id === reference);
      return source ? (safeUrl(source.url) ? link(source.url, source.id || source.title || "Source") : `<span>${escapeHtml(source.id || source.title || "Source unavailable")}</span>`) : `<span>${escapeHtml(reference)}</span>`;
    }).join("")}</div>`;
  }

  function renderClaims(claims) {
    return list(claims).map(claim => {
      if (typeof claim !== "object" || claim === null) return `<p>${escapeHtml(describe(claim))}</p>`;
      return `<div class="management-claim">${claim.claim ? `<p><strong>${escapeHtml(claim.claim)}</strong></p>` : ""}${claim.announcedTarget ? `<p><strong>Announced target.</strong> ${escapeHtml(claim.announcedTarget)}</p>${sourceLinks(claim.sourceId)}` : ""}${claim.outcome ? `<p><strong>Observed outcome.</strong> ${escapeHtml(claim.outcome)} ${escapeHtml(claim.outcomeLocator || "")}</p>${sourceLinks(claim.outcomeSourceId)}` : ""}${claim.caution ? `<p><strong>Attribution limit.</strong> ${escapeHtml(claim.caution)}</p>` : ""}</div>`;
    }).join("") || '<p>No quantified synergy target or matched outcome was verified in the reviewed evidence.</p>';
  }

  function renderMetrics() {
    const metrics = list(report.analysis?.metrics);
    if (!metrics.length) {
      $("metrics-table").innerHTML = '<p class="empty">No validated financial metrics are available for this case.</p>';
      $("metric-select").disabled = true;
      $("metric-detail").innerHTML = '<p class="empty">Add reconciled, reviewed figures to enable a metric comparison.</p>';
      $("peer-detail").innerHTML = '<p class="empty">No validated peer comparison is available.</p>';
      return;
    }
    $("metrics-table").innerHTML = `<table class="metric-table"><caption class="sr-only">Acquirer on original basis, combined baseline on its stated basis, post-merger figures and calculated residual</caption><thead><tr><th scope="col">Metric</th><th scope="col" class="numeric">Acquirer before<br><span class="muted">Original basis</span></th><th scope="col" class="numeric">Combined before<br><span class="muted">Issuer aggregate / calculation</span></th><th scope="col" class="numeric">After · basis noted</th><th scope="col" class="numeric">Unexplained<br>change</th><th scope="col">Finding</th></tr></thead><tbody>${metrics.map(metric => `<tr data-metric-row="${escapeHtml(metric.id)}"><th scope="row" class="metric-name"><button class="metric-button" type="button" data-metric="${escapeHtml(metric.id)}">${escapeHtml(metric.label)}</button><span class="metric-unit">${escapeHtml(metric.category || metric.unit || "Definition required")}</span></th><td class="numeric">${escapeHtml(formatLevel(factValue(metric.acquirer),metric.unit))}</td><td class="numeric">${escapeHtml(formatLevel(factValue(metric.baseline),metric.unit))}</td><td class="numeric">${escapeHtml(formatLevel(factValue(metric.post),metric.unit))}</td><td class="numeric">${escapeHtml(formatChange(metric.residual,metric))}</td><td><span class="verdict-label">${escapeHtml(metric.verdict || "Too early to tell")}</span></td></tr>`).join("")}</tbody></table>`;
    $("metric-select").innerHTML = metrics.map(metric => `<option value="${escapeHtml(metric.id)}">${escapeHtml(metric.label)}</option>`).join("");
    $("metrics-table").querySelectorAll("[data-metric]").forEach(button => button.addEventListener("click", () => {
      selectMetric(button.dataset.metric, true);
      $("decomposition").scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth"});
      $("metric-select").focus({preventScroll:true});
    }));
    const requested = new URL(location.href).searchParams.get("metric");
    selectMetric(metrics.some(item => item.id === requested) ? requested : metrics[0].id);
  }

  function renderBridge(metric) {
    const steps = bridgeSteps(metric);
    const components = [["Mechanical / mix",metric.mechanical],["Accounting / presentation",metric.accounting],["One-offs / regulatory relief",metric.one_off],["Sector movement",metric.sector],["Unexplained residual",metric.residual]];
    let chart = '<p class="empty">A waterfall is unavailable because a comparable baseline or post-merger figure is missing. Missing values are not assumed to be zero.</p>';
    if (steps) {
      const minimum = Math.min(0,...steps.flatMap(item => [item.start,item.end]).filter(finite));
      const maximum = Math.max(0,...steps.flatMap(item => [item.start,item.end]).filter(finite));
      const span = maximum - minimum || 1;
      chart = `<figure class="waterfall"><figcaption>${escapeHtml(metric.label)} · levels and contributions (${escapeHtml(metric.unit || "units")}; changes ${escapeHtml(changeUnit(metric))})</figcaption><div aria-hidden="true">${steps.map(item => `<div class="bridge-row"><span>${escapeHtml(item.label)}</span><div class="bridge-track">${finite(item.value) ? `<span class="bridge-bar ${item.value < 0 ? "negative" : ""} ${item.kind === "residual" ? "residual" : ""}" style="left:${100 * (Math.min(item.start,item.end) - minimum)/span}%;width:${100 * Math.abs(item.end-item.start)/span}%"></span>` : '<span class="bridge-unknown">Unquantified</span>'}</div><span class="bridge-value">${finite(item.value) ? escapeHtml(formatNumber(item.value,item.kind !== "level")) : "In residual"}</span></div>`).join("")}</div><p class="bridge-caption">Floating bars show quantified contributions. Unquantified effects remain inside the hatched residual, which is not a measure of merger synergy. Missing effects have no bar and are not assumed to be zero.</p></figure>`;
    }
    const arithmetic = metric.arithmetic || (steps ? `${formatNumber(metric.acquirer)} ${components.filter(([,value]) => finite(value)).map(([label,value]) => `${value >= 0 ? "+" : "−"} ${formatNumber(Math.abs(value))} (${label})`).join(" ")} = ${formatNumber(metric.post)}` : "No fully reconciled arithmetic is available.");
    return `<div class="bridge-layout">${chart}<div class="calculation-panel"><h4>Inspect the arithmetic</h4><div class="arithmetic">${escapeHtml(describe(arithmetic).replace(/ \| /g,"\n\n"))}</div><p>Reconciliation difference: <strong>${finite(metric.reconciliation_error) ? escapeHtml(formatChange(metric.reconciliation_error,metric)) : "Not available"}</strong></p><p>Mechanical effect = combined baseline − acquirer before. Other components bridge that baseline to the post-merger figure on the stated basis.</p></div></div><details><summary>Waterfall values and component definitions</summary><div class="table-scroll"><table><caption class="sr-only">Text alternative to the waterfall</caption><thead><tr><th scope="col">Component</th><th scope="col" class="numeric">Contribution</th></tr></thead><tbody>${components.map(([label,value]) => `<tr><th scope="row">${escapeHtml(label)}</th><td class="numeric">${escapeHtml(finite(value) ? formatChange(value,metric) : "Unquantified; remains in residual")}</td></tr>`).join("")}</tbody></table></div>${bullets(metric.notes)}</details>`;
  }

  function renderHistory(metric) {
    const bridge = metric.ratio_bridge;
    const path = list(metric.path);
    let html = "";
    if (bridge) html += `<details><summary>Numerator, denominator and interaction</summary><p>The symmetric allocation splits the interaction equally between numerator and denominator effects. This is a second explanation of the same baseline-to-post change; do not add it to the waterfall above.</p><div class="table-scroll"><table><thead><tr><th scope="col">Arithmetic effect</th><th scope="col" class="numeric">Change</th></tr></thead><tbody>${[["Numerator",bridge.numerator_effect],["Denominator",bridge.denominator_effect],["Total",bridge.total],["Reconciliation difference",bridge.reconciliation_error]].map(([label,value]) => `<tr><th scope="row">${label}</th><td class="numeric">${escapeHtml(formatChange(value,metric))}</td></tr>`).join("")}</tbody></table></div></details>`;
    if (path.length) html += `<details><summary>Available reporting history (${path.length} periods)</summary><div class="table-scroll"><table><thead><tr><th scope="col">Period</th><th scope="col" class="numeric">Value</th><th scope="col">Evidence type</th><th scope="col">Source</th></tr></thead><tbody>${path.map(point => `<tr><th scope="row">${escapeHtml(point.period)}</th><td class="numeric">${escapeHtml(formatLevel(point.value,metric.unit))}</td><td>${escapeHtml(point.kind || "Not specified")}</td><td>${sourceLinks(point.sources)}</td></tr>`).join("")}</tbody></table></div></details>`;
    return html;
  }

  function selectMetric(id, updateUrl = false) {
    const metric = list(report.analysis?.metrics).find(item => item.id === id);
    if (!metric) return;
    $("metric-select").value = id;
    document.querySelectorAll("[data-metric-row]").forEach(row => row.classList.toggle("selected-row", row.dataset.metricRow === id));
    document.querySelectorAll("[data-metric]").forEach(button => button.setAttribute("aria-pressed",String(button.dataset.metric === id)));
    if (updateUrl) {const url = new URL(location.href);url.searchParams.set("metric",id);history.pushState({},"",url);}
    let uncertainty;
    if (metric.uncertainty && typeof metric.uncertainty === "object") {
      uncertainty = `${finite(metric.uncertainty.low) && finite(metric.uncertainty.high) ? `Range: ${formatChange(metric.uncertainty.low,metric)} to ${formatChange(metric.uncertainty.high,metric)}. ` : ""}${metric.uncertainty.note || describe(metric.uncertainty)}`;
    } else uncertainty = metric.uncertainty || "No defensible uncertainty interval is available. Precision in the arithmetic does not remove uncertainty in attribution.";
    $("metric-detail").innerHTML = `<div class="metric-summary"><div><h3>${escapeHtml(metric.label)}</h3><p>${escapeHtml(metric.reason || metric.definition || "Comparable evidence remains incomplete.")}</p></div><div class="metric-verdict"><strong>${escapeHtml(metric.verdict || "Too early to tell")}</strong><span>${escapeHtml(metric.evidence_strength || "Weak")} evidence · ${escapeHtml(metric.status || "review the limitations")}</span></div></div><dl class="definition-list"><div><dt>Definition</dt><dd>${escapeHtml(metric.definition || "See operand arithmetic and comparability notes; a complete definition is not supplied.")}</dd></div><div><dt>Reporting periods</dt><dd>Before: ${escapeHtml(describe(metric.pre_period))} · After: ${escapeHtml(describe(metric.post_period))}</dd></div><div><dt>Issuer-reported after</dt><dd>${escapeHtml(formatLevel(factValue(metric.reported_post),metric.unit))}${metric.reported_post_note ? ` · ${escapeHtml(metric.reported_post_note)}` : ""}</dd></div></dl><dl class="stat-strip"><div><dt>Acquirer before · ${escapeHtml(metric.operands?.acquirer?.kind || "original basis")}</dt><dd>${escapeHtml(formatLevel(factValue(metric.acquirer),metric.unit))}</dd></div><div><dt>Combined before · baseline</dt><dd>${escapeHtml(formatLevel(factValue(metric.baseline),metric.unit))}</dd></div><div><dt>After · basis noted · ${escapeHtml(metric.operands?.post?.kind || "review basis")}</dt><dd>${escapeHtml(formatLevel(factValue(metric.post),metric.unit))}</dd></div><div><dt>Observed change</dt><dd>${escapeHtml(formatChange(metric.observed_change,metric))}</dd></div></dl>${renderBridge(metric)}<div class="uncertainty"><strong>Uncertainty & comparability</strong><p>${escapeHtml(uncertainty)}</p></div>${renderHistory(metric)}${sourceLinks(metric.sources)}`;
    renderPeers(metric);
  }

  function renderPeers(metric) {
    const peer = metric.peer || {};
    const rows = list(peer.rows);
    const sensitivity = list(peer.sensitivity);
    const peerTable = rows.length ? `<div class="table-scroll"><table><caption class="sr-only">Peer comparison for ${escapeHtml(metric.label)}</caption><thead><tr><th scope="col">Peer</th><th scope="col" class="numeric">Before</th><th scope="col" class="numeric">After</th><th scope="col" class="numeric">Change</th></tr></thead><tbody>${rows.map(row => `<tr><th scope="row">${escapeHtml(row.name || row.entity)}</th><td class="numeric">${escapeHtml(formatLevel(row.pre,metric.unit))}</td><td class="numeric">${escapeHtml(formatLevel(row.post,metric.unit))}</td><td class="numeric">${escapeHtml(formatChange(row.change,metric))}</td></tr>`).join("")}<tr><th scope="row">Peer median change</th><td></td><td></td><td class="numeric">${escapeHtml(formatChange(peer.median_change ?? metric.sector,metric))}</td></tr></tbody></table></div>` : '<p class="empty">No validated peer panel is available for this metric. A causal merger effect cannot be established from the observed change alone.</p>';
    const sensitivityTable = sensitivity.length ? `<div class="table-scroll"><table><caption class="sr-only">Peer sensitivity estimates for ${escapeHtml(metric.label)}</caption><thead><tr><th scope="col">Specification</th><th scope="col" class="numeric">Sector</th><th scope="col" class="numeric">Residual</th></tr></thead><tbody>${sensitivity.map(row => `<tr><th scope="row">${escapeHtml(row.label || row.name)}</th><td class="numeric">${escapeHtml(formatChange(row.sector,metric))}</td><td class="numeric">${escapeHtml(formatChange(row.residual,metric))}</td></tr>`).join("")}</tbody></table></div>` : '<p class="empty">Peer sensitivity is not available. Any positive residual therefore fails the robust-improvement test.</p>';
    $("peer-detail").innerHTML = `<p class="section-description">${escapeHtml(metric.label)} · ${escapeHtml(peer.method || "Peer comparison unavailable")}</p><div class="peer-grid"><div><h3>Peer movement</h3>${peerTable}</div><div><h3>Sensitivity to peer choice</h3>${sensitivityTable}</div></div><p class="peer-note"><strong>Pre-trend fit.</strong> ${escapeHtml(peer.pretrend_note || "No validated pre-trend fit is available; parallel trends have not been established.")}</p>${peer.selection_note ? `<p class="peer-note"><strong>Selection.</strong> ${escapeHtml(peer.selection_note)}</p>` : ""}${peer.coincident_events ? `<p class="peer-note"><strong>Coincident events.</strong> ${escapeHtml(describe(peer.coincident_events))}</p>` : ""}${sourceLinks([...new Set([...list(peer.sources),...rows.flatMap(row => list(row.sources))])])}`;
  }

  function renderObservations(page = 0, updateUrl = false) {
    const rows = list(report?.case?.observations);
    const pages = Math.max(1,Math.ceil(rows.length/25));
    observationPage = Math.max(0,Math.min(pages-1,Math.trunc(Number(page)) || 0));
    const visible = rows.slice(observationPage*25,(observationPage+1)*25);
    $("observations-table").innerHTML = visible.length ? `<table class="observation-table"><thead><tr><th scope="col">Observation / entity</th><th scope="col">Period / basis</th><th scope="col">Metric</th><th scope="col" class="numeric">Reported value</th><th scope="col">Source / locator</th><th scope="col">Restatement / review</th></tr></thead><tbody>${visible.map(row => `<tr><th scope="row">${escapeHtml(row.id)}<br><span class="muted">${escapeHtml(row.entity)}</span></th><td>${escapeHtml(row.period)}<br><span class="muted">${escapeHtml(row.basis)}</span></td><td>${escapeHtml(row.metric)}</td><td class="numeric">${escapeHtml(formatLevel(row.value,row.unit))}</td><td>${sourceLinks(row.sourceId)}<span class="muted">${escapeHtml(row.locator)}</span></td><td>${escapeHtml(row.restatement || row.restated || row.revision ? describe(row.restatement || row.restated || row.revision) : "No restatement identified in this record")}<br><span class="muted">${row.reviewed === true ? "Reviewed" : "Review not confirmed"}</span></td></tr>`).join("")}</tbody></table>` : '<p class="empty">No original observations are available.</p>';
    $("observations-status").textContent = rows.length ? `Page ${observationPage+1} of ${pages} · ${rows.length} observations` : "No observations";
    $("observations-previous").disabled=observationPage===0;
    $("observations-next").disabled=observationPage>=pages-1;
    if (updateUrl) {const url = new URL(location.href);url.searchParams.set("observations_page",String(observationPage+1));history.pushState({},"",url);}
  }

  function renderReport(data) {
    report = data;
    const study = data.case || {};
    const analysis = data.analysis || {};
    const overall = analysis.overall || {};
    document.title = `${study.title || "Merger case"} | Merger Comparison Engine`;
    $("case-title").textContent = study.title || "Merger comparison";
    $("case-id").textContent = study.id ? ` / ${study.id}` : "";
    $("case-subtitle").textContent = study.subtitle || "Reconstruct the baseline. Inspect the change. Test the explanation.";
    $("as-of").textContent = `Evidence reviewed ${study.as_of || "date not specified"}`;
    $("verdict").textContent = overall.verdict || "Too early to tell";
    $("summary").textContent = overall.summary || "The available evidence does not support a reliable overall attribution.";
    $("evidence-strength").textContent = overall.evidence_strength || "Weak";
    $("finding-reasons").innerHTML = list(overall.reasons).map(reason => `<li>${escapeHtml(describe(reason))}</li>`).join("");
    $("timeline-list").innerHTML = list(study.timeline).map(event => `<li><span class="date">${escapeHtml(event.date || "Date not verified")}</span><h3>${escapeHtml(event.label || event.event || event.title)}</h3><p>${escapeHtml(event.detail || event.description || "")}</p>${event.url ? link(event.url,"Primary source ↗") : sourceLinks(event.sources || event.source_id)}</li>`).join("") || '<li><h3>Timeline not verified</h3><p>Do not infer effective dates from an announcement alone.</p></li>';
    $("entity-map").innerHTML = list(study.entities).map(entity => `<div class="entity-row"><strong>${escapeHtml(entity.name || entity.entity)}</strong><div><p>${escapeHtml([entity.role?.replaceAll("_"," "),entity.type,entity.identifiers ? Object.entries(entity.identifiers).map(([key,value]) => `${key.toUpperCase()}: ${value}`).join("; ") : null,entity.status,entity.identifierStatus,entity.note].filter(Boolean).join(" · "))}</p>${entity.swap ? `<p>Share exchange: ${escapeHtml(entity.swap.newBobShares)} Bank of Baroda shares for ${escapeHtml(entity.swap.oldShares)} predecessor shares.</p>` : ""}${sourceLinks(entity.sourceId || entity.identifierSourceId)}</div></div>`).join("");
    $("transaction-note").textContent = study.transaction_note || study.event?.transactionBoundary || study.transaction_type || "";
    const reconstruction = study.reconstruction || {};
    $("reconstruction-detail").innerHTML = `${reconstruction.mode === "issuer_aggregated_amounts" ? '<div class="notice"><strong>Issuer-aggregated baseline.</strong> The included ratios use disclosed combined amounts. A fully independent predecessor reconstruction and intercompany elimination bridge remain incomplete.</div>' : ""}${list(reconstruction.unresolved).length || list(reconstruction.verifiedSummations).length ? `<details><summary>Baseline construction and unresolved adjustments</summary>${list(reconstruction.verifiedSummations).map(item => `<p><strong>${escapeHtml(item.metric.replaceAll("_"," "))}:</strong> ${list(item.amounts).map(value => escapeHtml(formatNumber(value))).join(" + ")} = ${escapeHtml(formatNumber(item.sum))} INR crore.</p>${sourceLinks(item.sourceId)}`).join("")}${bullets(reconstruction.unresolved)}</details>` : ""}`;
    $("comparability-detail").innerHTML = list(study.comparability).map(item => `<div class="comparison-note"><h3>${escapeHtml((item.category || "Comparability").replaceAll("_"," "))}</h3><p>${escapeHtml(item.note || describe(item))}</p>${sourceLinks(item.sourceIds || item.sourceId)}</div>`).join("") || '<p>No report-wide comparability notes are available. Review the limits attached to each metric.</p>';
    renderMetrics();
    const challenge = analysis.challenge || study.challenge || {};
    $("challenge-detail").innerHTML = `<div><h3>The strongest counterargument</h3>${paragraphs(study.interpretation?.counterargument || challenge.counterargument)}${sourceLinks(challenge.counterargumentSources)}</div><div><h3>What would falsify this finding?</h3>${paragraphs(study.interpretation?.falsification || challenge.falsification)}${sourceLinks(challenge.falsificationSources)}</div><div><h3>Targets versus outcomes</h3>${renderClaims(study.managementClaims || challenge.synergies)}</div>`;
    const methodology = analysis.methodology || {};
    $("methodology").innerHTML = `${paragraphs(methodology.summary)}${bullets(methodology.rules || analysis.decision_rules)}${bullets(methodology.limitations)}`;
    const limitations = list(study.limitations);
    $("limitations").innerHTML = `<h3>What the evidence cannot establish</h3>${limitations.length ? bullets(limitations) : '<p>Review each metric’s comparability and missing-data notes before interpreting the result.</p>'}`;
    const sources = list(study.sources);
    $("source-count").textContent = `${sources.length} source records`;
    $("sources-list").innerHTML = sources.map((source,index) => `<div class="source-item" id="source-${escapeHtml(source.id || index)}"><span class="source-id">${escapeHtml(source.id || String(index+1).padStart(2,"0"))}</span><div><h3>${escapeHtml(source.title || source.name || "Source document")}</h3><p>${escapeHtml(source.publisher || source.entity || "")}</p><p class="source-meta">${[`Published: ${source.publication_date || source.publishedDate || "Unknown"}`,source.publicationDateStatus && `Date status: ${source.publicationDateStatus}`,source.period && `Period: ${describe(source.period)}`,source.page && `Page / table: ${describe(source.page)}`,source.units && `Unit: ${describe(source.units)}`,source.extraction_method && `Method: ${source.extraction_method}`,source.retrievedAt && `Retrieved: ${source.retrievedAt}`].filter(Boolean).map(item => `<span>${escapeHtml(item)}</span>`).join("")}</p>${source.note || source.notes ? `<p>${escapeHtml(source.note || source.notes)}</p>` : ""}</div>${safeUrl(source.url) ? link(source.url,"Open source ↗") : '<span class="meta">Local / unavailable</span>'}</div>`).join("") || '<p class="empty">No source records have been provided.</p>';
    renderObservations(Number(new URL(location.href).searchParams.get("observations_page") || 1)-1);
    const legal = data.legal || {};
    $("legal-note").textContent = legal.note || "Applicability depends on the entity, transaction structure and relevant date. This research does not constitute public-launch clearance; flagged matters require qualified legal review.";
    $("legal-matrix").innerHTML = list(legal.rows).length ? `<table class="legal-table"><thead><tr><th scope="col">Rule / jurisdiction</th><th scope="col">Entity & transaction</th><th scope="col">Exact provision</th><th scope="col">Effective date</th><th scope="col">Required action</th><th scope="col">Legal review</th><th scope="col">Official evidence</th></tr></thead><tbody>${legal.rows.map(row => `<tr><th scope="row">${escapeHtml(row.rule || row.title)}<br><span class="muted">${escapeHtml(row.jurisdiction || "India")}</span></th><td>${escapeHtml(row.entity_transaction_type || [row.entities,row.transaction_type].filter(Boolean).map(describe).join(" · "))}</td><td>${escapeHtml(row.provision || "Verification required")}</td><td>${escapeHtml(row.effective_date || "Verification required")}</td><td class="legal-action">${escapeHtml(row.action || row.required_action || "Review applicability")}</td><td>${row.legal_review_needed === false ? "No flag recorded" : "Required"}</td><td>${list(row.url || row.evidence_urls).map((url,index) => link(url,`Source ${index+1} ↗`)).join("<br>") || "Not available"}</td></tr>`).join("")}</tbody></table>` : '<p class="empty">No legal applicability matrix is available. Public launch is not cleared.</p>';
    $("report").hidden = false;
  }

  async function loadReport() {
    $("load-state").hidden = false;
    $("load-error").hidden = true;
    try {
      const response = await fetch("/report.json", {headers:{Accept:"application/json"}});
      if (!response.ok) throw new Error(`The report returned ${response.status}. Reload the page and try again.`);
      const data = await response.json();
      if (!data.case || !data.analysis) throw new Error("The response is missing the case or analysis. Check the data validation output.");
      renderReport(data);
    } catch (error) {
      $("load-error-message").textContent = error.message || "Connection failed. Reload the page and try again.";
      $("load-error").hidden = false;
    } finally {$("load-state").hidden = true;}
  }

  function clearErrors() { for (const id of ["review-text","source-url"]) $(id).removeAttribute("aria-invalid");$("text-error").textContent="";$("url-error").textContent=""; }
  function inputError(id, message) {$(id).setAttribute("aria-invalid","true");$(id === "review-text" ? "text-error" : "url-error").textContent = message;$(id).focus();}

  $("document-file").addEventListener("change", async event => {
    pdfFile = null;
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {$("review-status").textContent="This file is over 5 MB. Use a smaller excerpt or document.";event.target.value="";return;}
    const extension = file.name.split(".").pop().toLowerCase();
    if (!["txt","csv","json","pdf"].includes(extension)) {$("review-status").textContent="Choose a TXT, CSV, JSON or PDF file.";event.target.value="";return;}
    try {
      if (extension === "pdf") {
        const bytes = new Uint8Array(await file.arrayBuffer());
        let binary = "";
        for (let offset=0;offset<bytes.length;offset+=32768) binary += String.fromCharCode(...bytes.subarray(offset,offset+32768));
        pdfFile = {file_name:file.name,file_base64:btoa(binary)};
        $("review-status").textContent=`${file.name} is ready for extraction and review. The PDF will be used as the source text.`;
      } else {
        const text = await file.text();
        if (text.length > 200000) throw new Error("This text is over 200,000 characters. Upload a smaller excerpt.");
        $("review-text").value=text;
        $("review-status").textContent=`${file.name} loaded. Inspect the excerpt before extraction.`;
      }
      draftChanged = true;
    } catch (error) {$("review-status").textContent=`File could not be read: ${error.message}`;event.target.value="";}
  });

  $("review-form").addEventListener("input", () => {draftChanged=true;});
  $("review-text").addEventListener("keydown", event => {if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {event.preventDefault();$("review-form").requestSubmit();}});
  $("review-form").addEventListener("submit", async event => {
    event.preventDefault();clearErrors();
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    for (const key of Object.keys(payload)) payload[key]=String(payload[key]).trim();
    if (!payload.text && !pdfFile) {inputError("review-text","Paste an excerpt or select a supported document to review.");return;}
    if (payload.source_url && !safeUrl(payload.source_url)) {inputError("source-url","Enter a full http:// or https:// source URL, or leave this field empty.");return;}
    if (pdfFile) Object.assign(payload,pdfFile);
    $("review-submit").disabled=true;$("review-submit").querySelector(".working").hidden=false;
    $("review-status").textContent="Extracting candidates and running validation checks…";
    try {
      const response = await fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(payload)});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Review failed (${response.status}).`);
      $("review-result").innerHTML = `<div class="notice"><h3>Review required · not added to the report</h3><p>${escapeHtml(result.message || "Check every candidate against the source, including units, dates, subtotals and entity mapping. Extraction alone is not verification.")}</p></div><h3>Validation results</h3><pre>${escapeHtml(JSON.stringify(result.validation || {status:"No validation details returned"},null,2))}</pre><details open><summary>Extracted candidates (${list(result.numbers).length} numeric records; ${list(result.event_candidates).length} event candidates)</summary><pre>${escapeHtml(JSON.stringify({events:result.event_candidates || [],numbers:result.numbers || [],...result.warnings ? {warnings:result.warnings} : {}},null,2))}</pre></details>`;
      $("review-result").hidden=false;$("review-result").focus();
      $("review-status").textContent="Extraction complete. Candidates remain unverified; the case report is unchanged.";
      draftChanged=false;
    } catch(error) {$("review-status").textContent=`${error.message} Your input is still here; correct it or try again.`;}
    finally {$("review-submit").disabled=false;$("review-submit").querySelector(".working").hidden=true;}
  });

  $("retry").addEventListener("click",loadReport);
  $("metric-select").addEventListener("change",event => selectMetric(event.target.value,true));
  $("observations-previous").addEventListener("click",() => renderObservations(observationPage-1,true));
  $("observations-next").addEventListener("click",() => renderObservations(observationPage+1,true));
  addEventListener("popstate",() => {if (report) {selectMetric(new URL(location.href).searchParams.get("metric") || report.analysis.metrics[0]?.id);renderObservations(Number(new URL(location.href).searchParams.get("observations_page") || 1)-1);}});
  addEventListener("beforeunload",event => {if(draftChanged){event.preventDefault();event.returnValue="";}});
  loadReport();
}
