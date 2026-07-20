// investigation_ui.js
// Shared UI logic used by BOTH the demo case page and the custom investigation
// page, so we never duplicate the same rendering code twice:
//   - runInvestigationFlow(...) drives the "Investigation Pipeline" animation
//     and timing around a single analysis request.
//   - renderInvestigationResults(...) turns the backend's JSON report into
//     the on-page "Investigation Report" section.
//   - scrollToEvidence(...) implements "View Source Evidence" (Part 6).
//
// This file defines plain global functions (no build step / bundler), so
// app.js and new_investigation.js can call them directly.

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// "Print / Save Report" (Part 11): plain browser printing, no PDF library.
// The button lives inside the shared _results_section.html partial, present
// on every page that includes it, so it's wired up once here.
document.addEventListener("DOMContentLoaded", () => {
    const printButton = document.getElementById("print-report-btn");
    if (printButton) {
        printButton.addEventListener("click", () => window.print());
    }
});

async function postJSON(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
        const error = new Error("Request to " + url + " failed with status " + response.status);
        error.status = response.status;
        throw error;
    }
    return response.json();
}

// Steps through the 4 pipeline cards (Pending -> Processing -> Complete) over
// roughly `totalDurationMs`. This is a purely visual sequence - it does not
// mean separate AI agents are running; it just paces the single local
// analysis call so the "Investigation Pipeline" is easy to follow.
async function animatePipelineSteps(totalDurationMs) {
    const steps = document.querySelectorAll(".pipeline-step");
    if (steps.length === 0) {
        return;
    }
    const perStep = totalDurationMs / steps.length;

    steps.forEach((step) => {
        step.classList.remove("active");
        setStepStatus(step, "pipeline_status_pending");
    });

    for (const step of steps) {
        step.classList.add("active");
        setStepStatus(step, "pipeline_status_processing");
        await sleep(perStep);
        setStepStatus(step, "pipeline_status_complete");
    }
}

function setStepStatus(stepElement, i18nKey) {
    const statusEl = stepElement.querySelector(".pipeline-step-status");
    if (statusEl) {
        statusEl.textContent = t(i18nKey);
    }
}

// Runs one full "click button -> animate pipeline -> call backend -> render
// results" flow. Shared by the demo page and the custom investigation page;
// only `requestFn` (what to fetch) differs between them.
async function runInvestigationFlow({ button, statusText, requestFn }) {
    const startTime = performance.now();
    button.disabled = true;
    statusText.textContent = t("analysis_running");

    const resultsSection = document.getElementById("investigation-results");
    if (resultsSection) {
        resultsSection.classList.add("hidden");
    }

    try {
        const [result] = await Promise.all([
            requestFn(),
            animatePipelineSteps(2400), // keeps the visual sequence natural, ~2.4s
        ]);

        renderInvestigationResults(result);

        const elapsedSeconds = ((performance.now() - startTime) / 1000).toFixed(2);
        statusText.textContent = t("analysis_complete", { seconds: elapsedSeconds });
    } catch (error) {
        statusText.textContent = t("analysis_error");
        console.error(error);
    } finally {
        button.disabled = false;
    }
}

// ---------------------------------------------------------------------------
// Rendering the investigation report
// ---------------------------------------------------------------------------

function renderInvestigationResults(result) {
    // Remembered so the report can be re-rendered (with translated labels)
    // if the user switches interface language after analysis completes.
    window.lastInvestigationResult = result;

    setText("result-executive-summary", result.executive_summary);
    renderCaseInformation(result.case_information);
    renderRiskLevel(result.risk_level);
    renderInvolvedParties(result.involved_parties);
    renderVerifiedFacts(result.verified_facts);
    renderContextualStatements(result.contextual_statements);
    renderTimeline(result.timeline);
    renderContradictions(result.contradictions);
    renderEvidenceAssessment(result.evidence_assessment);
    renderList("result-follow-up-questions", result.follow_up_questions, "none_found");
    renderList("result-next-steps", result.recommended_next_steps, "none_found");
    setText("result-disclaimer", result.disclaimer);

    setText("print-case-title", result.case_title);
    setText("print-analysis-date", new Date().toLocaleString());

    const resultsSection = document.getElementById("investigation-results");
    resultsSection.classList.remove("hidden");
}

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value || "";
    }
}

function renderList(elementId, items, emptyKey) {
    const list = document.getElementById(elementId);
    list.innerHTML = "";
    if (!items || items.length === 0) {
        const item = document.createElement("li");
        item.textContent = t(emptyKey);
        list.appendChild(item);
        return;
    }
    items.forEach((text) => {
        const item = document.createElement("li");
        item.textContent = text;
        list.appendChild(item);
    });
}

function renderCaseInformation(info) {
    const box = document.getElementById("result-case-information");
    box.innerHTML = "";
    box.appendChild(buildLabeledLine(t("case_id_label"), info.case_id));
    box.appendChild(buildLabeledLine(t("case_type_label"), info.case_type || t("none_found")));
    box.appendChild(buildLabeledLine(t("evidence_count_label"), String(info.evidence_count)));
}

function renderRiskLevel(riskLevel) {
    const badge = document.getElementById("result-risk-level");
    const key = riskLevel === "High" ? "risk_high" : riskLevel === "Medium" ? "risk_medium" : "risk_low";
    const colorClass = riskLevel === "High" ? "text-red-400" : riskLevel === "Medium" ? "text-amber-400" : "text-teal-400";
    badge.textContent = t(key);
    badge.className = "font-semibold text-base " + colorClass;
}

function renderInvolvedParties(parties) {
    const box = document.getElementById("result-involved-parties");
    box.innerHTML = "";
    box.appendChild(buildLabeledLine(t("people_label"), formatList(parties.people)));
    box.appendChild(buildLabeledLine(t("organizations_label"), formatList(parties.organizations)));
}

function renderVerifiedFacts(facts) {
    const box = document.getElementById("result-verified-facts");
    box.innerHTML = "";
    box.appendChild(buildLabeledLine(t("dates_label"), formatList(facts.dates)));
    box.appendChild(buildLabeledLine(t("emails_label"), formatList(facts.emails)));

    const statementsHeading = document.createElement("p");
    statementsHeading.className = "text-slate-500 mt-2";
    statementsHeading.textContent = t("key_statements_label") + ":";
    box.appendChild(statementsHeading);

    if (facts.key_statements.length === 0) {
        box.appendChild(buildPlainParagraph(t("none_found")));
    } else {
        facts.key_statements.forEach((item) => {
            box.appendChild(buildStatementWithSource(item.statement, item));
        });
    }
}

function renderContextualStatements(statements) {
    const list = document.getElementById("result-contextual-statements");
    list.innerHTML = "";
    if (!statements || statements.length === 0) {
        list.innerHTML = "";
        const item = document.createElement("li");
        item.className = "text-slate-400";
        item.textContent = t("no_contextual_statements");
        list.appendChild(item);
        return;
    }
    statements.forEach((item) => {
        const entry = document.createElement("li");
        entry.className = "border-l-2 border-slate-700 pl-3";

        const sourceLine = document.createElement("p");
        sourceLine.className = "text-xs text-slate-500";
        sourceLine.textContent = item.source_title + " (" + translateEvidenceType(item.source_type) + ") — " + t("no_specific_time");
        entry.appendChild(sourceLine);

        const statementLine = document.createElement("p");
        statementLine.className = "text-slate-300 mt-1";
        statementLine.textContent = item.statement;
        entry.appendChild(statementLine);

        entry.appendChild(buildSourceLink(item.source_index));
        list.appendChild(entry);
    });
}

function renderTimeline(timeline) {
    const list = document.getElementById("result-timeline");
    list.innerHTML = "";
    if (!timeline || timeline.length === 0) {
        const item = document.createElement("li");
        item.className = "text-slate-400";
        item.textContent = t("no_dated_events");
        list.appendChild(item);
        return;
    }
    timeline.forEach((event) => {
        const item = document.createElement("li");
        item.className = "border-l-2 border-teal-500/40 pl-3";

        const timeSpan = document.createElement("span");
        timeSpan.className = "text-teal-400 font-mono";
        timeSpan.textContent = event.time;
        item.appendChild(timeSpan);

        item.appendChild(document.createTextNode(" — " + event.description + " "));

        const sourceSpan = document.createElement("span");
        sourceSpan.className = "text-slate-500";
        sourceSpan.textContent = "(" + event.source_title + " · " + translateEvidenceType(event.source_type) + ")";
        item.appendChild(sourceSpan);

        item.appendChild(buildSourceLink(event.source_index));
        list.appendChild(item);
    });
}

function renderContradictions(contradictions) {
    const box = document.getElementById("result-contradictions");
    box.innerHTML = "";
    if (!contradictions || contradictions.length === 0) {
        box.innerHTML = "";
        const message = document.createElement("p");
        message.className = "text-sm text-slate-400";
        message.textContent = t("no_contradictions");
        box.appendChild(message);
        return;
    }
    contradictions.forEach((item) => {
        box.appendChild(buildContradictionCard(item));
    });
}

function buildContradictionCard(item) {
    const isHigh = item.severity === "High";
    const card = document.createElement("div");
    card.className = "border rounded-lg p-4 " + (isHigh ? "border-red-500/40 bg-red-500/5" : "border-amber-500/40 bg-amber-500/5");

    const badgeRow = document.createElement("div");
    badgeRow.className = "flex flex-wrap items-center gap-2 mb-3";

    const severityBadge = document.createElement("span");
    severityBadge.className = "text-xs uppercase tracking-widest font-semibold " + (isHigh ? "text-red-400" : "text-amber-400");
    severityBadge.textContent = (isHigh ? t("risk_high") : t("risk_medium"));
    badgeRow.appendChild(severityBadge);

    const confidenceBadge = document.createElement("span");
    confidenceBadge.className = "text-xs px-2 py-0.5 rounded-full border border-slate-700 text-slate-300";
    const confidenceKey = "confidence_" + item.confidence_label.toLowerCase();
    confidenceBadge.textContent = t("confidence_label") + ": " + t(confidenceKey) + " (" + item.confidence_score + "/100)";
    badgeRow.appendChild(confidenceBadge);

    card.appendChild(badgeRow);

    card.appendChild(buildLabeledLine(t("claim_label"), item.claim));
    card.appendChild(buildSourceRow(t("claim_source_label"), item.claim_source_title, item.claim_source_type, item.claim_source_index));

    card.appendChild(buildLabeledLine(t("conflicting_evidence_label"), item.conflicting_evidence));
    card.appendChild(buildSourceRow(t("evidence_source_label"), item.conflicting_evidence_source_title, item.conflicting_evidence_source_type, item.conflicting_evidence_source_index));

    card.appendChild(buildLabeledLine(t("reasoning_label"), item.reasoning));

    return card;
}

function renderEvidenceAssessment(assessment) {
    const box = document.getElementById("result-evidence-assessment");
    box.innerHTML = "";
    if (!assessment || assessment.length === 0) {
        box.appendChild(buildPlainParagraph(t("none_found")));
        return;
    }
    assessment.forEach((item) => {
        const row = document.createElement("div");
        row.className = "flex items-center justify-between border-b border-slate-800 py-2 last:border-0";

        const label = document.createElement("span");
        label.className = "text-slate-300";
        label.textContent = t("evidence_number_prefix") + " " + item.index + " — " + item.title + " (" + translateEvidenceType(item.type) + ")";
        row.appendChild(label);

        const counts = document.createElement("span");
        counts.className = "text-slate-500 text-xs";
        counts.textContent = t("people_label") + ": " + item.people_found + " · " +
            t("organizations_label") + ": " + item.organizations_found + " · " +
            t("dates_label") + ": " + item.dates_found;
        row.appendChild(counts);

        box.appendChild(row);
    });
}

// ---------------------------------------------------------------------------
// Small shared builders
// ---------------------------------------------------------------------------

function formatList(values) {
    return values && values.length ? values.join(", ") : t("none_found");
}

function buildLabeledLine(label, value) {
    const line = document.createElement("p");
    line.className = "mb-1";
    const labelSpan = document.createElement("span");
    labelSpan.className = "text-slate-500";
    labelSpan.textContent = label + ": ";
    line.appendChild(labelSpan);
    line.appendChild(document.createTextNode(value));
    return line;
}

function buildPlainParagraph(text) {
    const paragraph = document.createElement("p");
    paragraph.className = "text-slate-400";
    paragraph.textContent = text;
    return paragraph;
}

function buildStatementWithSource(statement, sourceInfo) {
    const wrapper = document.createElement("div");
    wrapper.className = "border-l-2 border-slate-700 pl-3 mb-2";

    const text = document.createElement("p");
    text.textContent = statement;
    wrapper.appendChild(text);

    const source = document.createElement("p");
    source.className = "text-xs text-slate-500 mt-1";
    source.textContent = sourceInfo.source_title + " (" + translateEvidenceType(sourceInfo.source_type) + ")";
    wrapper.appendChild(source);

    wrapper.appendChild(buildSourceLink(sourceInfo.source_index));
    return wrapper;
}

// A small "Evidence N" link that scrolls to and highlights the source card.
function buildSourceLink(sourceIndex) {
    const link = document.createElement("button");
    link.type = "button";
    link.className = "text-xs text-teal-400 hover:text-teal-300 underline mt-1";
    link.textContent = t("evidence_number_prefix") + " " + sourceIndex;
    link.addEventListener("click", () => scrollToEvidence(sourceIndex));
    return link;
}

// The explicit "View Source Evidence" button used on contradiction cards (Part 6).
function buildSourceRow(label, sourceTitle, sourceType, sourceIndex) {
    const row = document.createElement("div");
    row.className = "flex flex-wrap items-center gap-2 mb-2";

    const text = document.createElement("p");
    text.className = "text-xs text-slate-500";
    text.textContent = label + ": " + sourceTitle + " (" + translateEvidenceType(sourceType) + ")";
    row.appendChild(text);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "text-xs px-2 py-0.5 rounded-full border border-teal-500/40 text-teal-400 hover:bg-teal-500/10 transition-colors";
    button.textContent = t("view_source_button");
    button.addEventListener("click", () => scrollToEvidence(sourceIndex));
    row.appendChild(button);

    return row;
}

// Scrolls to the evidence card matching source_index and briefly highlights it.
// Works on both pages: case_detail.html renders "evidence-card-N" server-side,
// new_investigation.js assigns the same ids to its evidence blocks at submit time.
function scrollToEvidence(sourceIndex) {
    const target = document.getElementById("evidence-card-" + sourceIndex);
    if (!target) {
        return;
    }
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    target.classList.add("evidence-highlight");
    setTimeout(() => target.classList.remove("evidence-highlight"), 2000);
}

// Re-render an already-visible report when the interface language changes,
// so source-type labels and empty-state text switch immediately too.
document.addEventListener("languageChanged", () => {
    if (window.lastInvestigationResult) {
        renderInvestigationResults(window.lastInvestigationResult);
    }
});
