// new_investigation.js
// Page-specific wiring for the "Create New Investigation" page
// (templates/new_investigation.html): builds the dynamic evidence form,
// validates it, and submits it to POST /analyze-custom-case.
// The pipeline animation and report rendering are shared - see
// static/js/investigation_ui.js.

const MAX_EVIDENCE_ITEMS = 6;
const MIN_EVIDENCE_ITEMS = 2;
const DEFAULT_EVIDENCE_ITEMS = 2;

const EVIDENCE_TYPE_VALUES = [
    "Employee Statement", "Email", "Visitor Log", "Policy Document", "Meeting Note", "Other",
];

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("new-investigation-form");
    if (!form) {
        return; // Only the new-investigation page has this form.
    }

    const evidenceContainer = document.getElementById("evidence-sections");
    const addButton = document.getElementById("add-evidence-btn");
    const loadSampleButton = document.getElementById("load-sample-btn");
    const analyzeButton = document.getElementById("analyze-evidence-btn");
    const statusText = document.getElementById("pipeline-status");
    const validationMessage = document.getElementById("form-validation-message");

    // Pressing Enter in a text field must never reload the page.
    form.addEventListener("submit", (event) => event.preventDefault());

    for (let i = 0; i < DEFAULT_EVIDENCE_ITEMS; i++) {
        evidenceContainer.appendChild(createEvidenceBlock(false));
    }
    renumberEvidenceBlocks();

    addButton.addEventListener("click", () => {
        if (getEvidenceBlocks().length >= MAX_EVIDENCE_ITEMS) {
            validationMessage.textContent = t("max_evidence_reached");
            return;
        }
        evidenceContainer.appendChild(createEvidenceBlock(true));
        renumberEvidenceBlocks();
    });

    loadSampleButton.addEventListener("click", loadSampleCase);

    analyzeButton.addEventListener("click", () => {
        const payload = buildValidatedPayload();
        if (!payload) {
            return; // Validation message already shown; nothing else happens (no reload).
        }
        runInvestigationFlow({
            button: analyzeButton,
            statusText: statusText,
            requestFn: () => postJSON("/analyze-custom-case", payload),
        });
    });

    // Re-apply translated placeholder text (evidence headings, option labels)
    // whenever the interface language changes.
    document.addEventListener("languageChanged", () => {
        renumberEvidenceBlocks();
        translateEvidenceTypeOptions();
        translateEvidenceTitlePlaceholders();
    });

    // -------------------------------------------------------------------
    // Evidence block helpers
    // -------------------------------------------------------------------

    function getEvidenceBlocks() {
        return Array.from(evidenceContainer.querySelectorAll(".evidence-block"));
    }

    function createEvidenceBlock(removable) {
        const block = document.createElement("div");
        block.className = "evidence-block bg-slate-900 border border-slate-800 rounded-xl p-5";

        const headerRow = document.createElement("div");
        headerRow.className = "flex items-center justify-between mb-3";

        const heading = document.createElement("h3");
        heading.className = "evidence-block-heading font-semibold text-slate-100";
        headerRow.appendChild(heading);

        if (removable) {
            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.textContent = t("remove_evidence_button");
            removeButton.className = "text-xs text-red-400 hover:text-red-300 underline";
            removeButton.addEventListener("click", () => {
                block.remove();
                renumberEvidenceBlocks();
            });
            headerRow.appendChild(removeButton);
        }

        block.appendChild(headerRow);

        const titleLabel = buildFieldLabel("evidence_title_label");
        const titleInput = document.createElement("input");
        titleInput.type = "text";
        titleInput.maxLength = 200;
        titleInput.placeholder = t("evidence_title_placeholder");
        titleInput.className = "evidence-title-input w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500 mb-3";
        block.appendChild(titleLabel);
        block.appendChild(titleInput);

        const typeLabel = buildFieldLabel("evidence_type_label");
        const typeSelect = document.createElement("select");
        typeSelect.className = "evidence-type-select w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500 mb-3";
        EVIDENCE_TYPE_VALUES.forEach((value) => {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = translateEvidenceType(value);
            typeSelect.appendChild(option);
        });
        block.appendChild(typeLabel);
        block.appendChild(typeSelect);

        const contentLabel = buildFieldLabel("evidence_content_label");
        const contentTextarea = document.createElement("textarea");
        contentTextarea.rows = 5;
        contentTextarea.maxLength = 20000;
        contentTextarea.className = "evidence-content-input w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500";
        block.appendChild(contentLabel);
        block.appendChild(contentTextarea);

        return block;
    }

    function buildFieldLabel(i18nKey) {
        const label = document.createElement("label");
        label.className = "field-label block text-xs font-medium text-slate-400 mb-1";
        label.setAttribute("data-i18n", i18nKey);
        label.textContent = t(i18nKey);
        return label;
    }

    function renumberEvidenceBlocks() {
        getEvidenceBlocks().forEach((block, index) => {
            const heading = block.querySelector(".evidence-block-heading");
            const n = index + 1;
            const headingKey = n <= MIN_EVIDENCE_ITEMS ? "evidence_section_heading" : "evidence_section_heading_optional";
            heading.textContent = t(headingKey, { n });
        });
    }

    function translateEvidenceTypeOptions() {
        getEvidenceBlocks().forEach((block) => {
            const select = block.querySelector(".evidence-type-select");
            Array.from(select.options).forEach((option) => {
                option.textContent = translateEvidenceType(option.value);
            });
        });
    }

    function translateEvidenceTitlePlaceholders() {
        getEvidenceBlocks().forEach((block) => {
            block.querySelector(".evidence-title-input").placeholder = t("evidence_title_placeholder");
        });
    }

    // Builds an internal title like "Employee Statement #2" for evidence
    // items submitted with no title, based on the selected type and the
    // item's position among the evidence actually being submitted.
    function buildAutoEvidenceTitle(type, position) {
        return t("auto_evidence_title_format", { type: translateEvidenceType(type), n: position });
    }

    // -------------------------------------------------------------------
    // Load Sample Case
    // -------------------------------------------------------------------

    function loadSampleCase() {
        const demoData = JSON.parse(document.getElementById("demo-case-data").textContent);

        document.getElementById("case-title-input").value = demoData.title;
        document.getElementById("case-category-select").value = demoData.case_type;
        document.getElementById("report-language-select").value = "en";

        evidenceContainer.innerHTML = "";
        demoData.documents.forEach((doc, index) => {
            const block = createEvidenceBlock(index >= DEFAULT_EVIDENCE_ITEMS);
            block.querySelector(".evidence-title-input").value = doc.name;
            block.querySelector(".evidence-type-select").value = doc.type;
            block.querySelector(".evidence-content-input").value = doc.content;
            evidenceContainer.appendChild(block);
        });
        renumberEvidenceBlocks();
        validationMessage.textContent = "";
    }

    // -------------------------------------------------------------------
    // Validation (Part 2): case title required, at least 2 non-empty
    // evidence documents required, shown inline without reloading the page.
    // Evidence title is optional - a title is auto-generated from the
    // evidence type and its position among the submitted items when left
    // blank (e.g. "Email #2"); evidence type and text remain required.
    // -------------------------------------------------------------------

    function buildValidatedPayload() {
        const caseTitle = document.getElementById("case-title-input").value.trim();
        if (!caseTitle) {
            validationMessage.textContent = t("validation_title_required");
            return null;
        }

        const evidence = [];
        getEvidenceBlocks().forEach((block) => {
            const title = block.querySelector(".evidence-title-input").value.trim();
            const type = block.querySelector(".evidence-type-select").value;
            const content = block.querySelector(".evidence-content-input").value.trim();
            if (content) {
                const finalTitle = title || buildAutoEvidenceTitle(type, evidence.length + 1);
                evidence.push({ title: finalTitle, type, content, _blockElement: block });
            }
        });

        if (evidence.length < MIN_EVIDENCE_ITEMS) {
            validationMessage.textContent = t("validation_min_evidence", { count: evidence.length });
            return null;
        }

        validationMessage.textContent = "";

        // Clear stale ids from a previous submission, then assign fresh
        // "evidence-card-N" ids matching this payload's order, so "View
        // Source Evidence" can scroll to the right block afterward.
        getEvidenceBlocks().forEach((block) => block.removeAttribute("id"));
        evidence.forEach((item, index) => {
            item._blockElement.id = "evidence-card-" + (index + 1);
        });

        return {
            case_title: caseTitle,
            case_category: document.getElementById("case-category-select").value,
            report_language: document.getElementById("report-language-select").value,
            evidence: evidence.map(({ title, type, content }) => ({ title, type, content })),
        };
    }
});
