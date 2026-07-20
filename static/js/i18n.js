// i18n.js
// The single source of truth for interface translations (English / Arabic).
//
// IMPORTANT: this only translates fixed INTERFACE labels (buttons, headings,
// messages). Generated report content (executive summary, next steps,
// disclaimer, follow-up questions) is written server-side in the chosen
// report language - see services/investigation_engine.py. Keeping those two
// concerns separate means we never duplicate the same translated text in
// two different dictionaries.

const TRANSLATIONS = {
    en: {
        // Navigation / footer
        nav_subtitle: "Corporate Investigation Platform",
        footer_disclaimer: "Assists human investigators. Does not make legal or disciplinary decisions.",
        footer_data_notice: "Hackathon MVP — fictional or non-sensitive data only.",
        lang_toggle_label: "العربية",

        // Landing page
        landing_subtitle: "AI-powered Corporate Investigation & Evidence Analysis Platform",
        badge_hr: "HR",
        badge_compliance: "Compliance",
        badge_audit: "Internal Audit",
        badge_legal: "Legal",
        try_demo_button: "Try Demo Investigation",
        create_investigation_button: "Create New Investigation",
        problem_heading: "The Problem",
        problem_text: "Internal investigations often require teams to manually cross-reference scattered statements, emails, and records.",
        solution_heading: "The Solution",
        solution_text: "Evidence AI transforms fragmented evidence into structured facts, timelines, contradictions, and investigation reports.",
        engine_section_heading: "How the Local Investigation Engine Works",
        engine_stage_1_name: "Fact Extraction",
        engine_stage_1_desc: "Reads submitted documents and pulls out discrete, sourced factual claims.",
        engine_stage_2_name: "Timeline Building",
        engine_stage_2_desc: "Orders extracted facts into a single chronological sequence of events.",
        engine_stage_3_name: "Contradiction Detection",
        engine_stage_3_desc: "Compares statements across sources to surface conflicting accounts.",
        engine_stage_4_name: "Report Generation",
        engine_stage_4_desc: "Synthesizes findings into a structured investigation report.",
        ethical_disclaimer: "Evidence AI assists human investigators and does not make legal or disciplinary decisions.",

        // Demo case page
        demo_data_notice: "DEMONSTRATION DATA — all names and companies below are fictional.",
        evidence_documents_heading: "Evidence Documents",
        run_demo_button: "Run Intelligent Investigation",

        // New investigation page
        new_investigation_heading: "Create New Investigation",
        new_investigation_subheading: "Submit your own evidence for local rule-based analysis.",
        privacy_notice: "Demo privacy notice: submitted evidence is processed locally by this application and is not sent to an external AI service. Do not use real confidential company data in this public MVP.",
        case_title_label: "Case Title",
        case_category_label: "Case Category",
        category_procurement: "Procurement Compliance",
        category_hr: "HR Misconduct",
        category_audit: "Internal Audit",
        category_data_access: "Data Access Incident",
        category_other: "Other",
        report_language_label: "Report Language",
        lang_option_en: "English",
        lang_option_ar: "العربية",
        evidence_section_heading: "Evidence {n}",
        evidence_section_heading_optional: "Evidence {n} (Optional)",
        evidence_helper_text: "Minimum required: 2 evidence items. You may add more if needed.",
        evidence_title_label: "Evidence Title (Optional)",
        evidence_title_placeholder: "Leave blank to auto-generate (e.g., Employee Statement #1)",
        evidence_type_label: "Evidence Type",
        evidence_content_label: "Evidence Text",
        add_evidence_button: "Add Another Evidence",
        remove_evidence_button: "Remove Evidence",
        load_sample_button: "Load Sample Case",
        analyze_button: "Analyze Evidence",
        max_evidence_reached: "Maximum of 6 evidence items reached.",
        validation_title_required: "Case title is required.",
        validation_min_evidence: "Please add at least 2 evidence items with text before analyzing. You currently have {count} filled in.",
        auto_evidence_title_format: "{type} #{n}",

        // Evidence type option labels (also used to translate source_type in results)
        evidence_type_labels: {
            "Employee Statement": "Employee Statement",
            "Email": "Email",
            "Visitor Log": "Visitor Log",
            "Policy Document": "Policy Document",
            "Meeting Note": "Meeting Note",
            "Other": "Other",
        },

        // Pipeline
        pipeline_heading: "Investigation Pipeline",
        pipeline_step_1: "Extracting facts and claims",
        pipeline_step_2: "Building timeline",
        pipeline_step_3: "Cross-checking evidence",
        pipeline_step_4: "Generating report",
        pipeline_status_pending: "Pending",
        pipeline_status_processing: "Processing",
        pipeline_status_complete: "Complete",
        analysis_running: "Running the local investigation engine...",
        analysis_complete: "Analysis completed in {seconds} seconds.",
        analysis_error: "Something went wrong while running the investigation. Please try again.",

        // Results
        report_heading: "Investigation Report",
        executive_summary_heading: "Executive Summary",
        case_information_heading: "Case Information",
        involved_parties_heading: "Involved Parties",
        people_label: "People",
        organizations_label: "Organizations",
        verified_facts_heading: "Verified Facts",
        dates_label: "Dates",
        emails_label: "Emails",
        key_statements_label: "Key Statements",
        contextual_statements_heading: "Contextual Statements",
        no_specific_time: "No specific time",
        timeline_heading: "Chronological Timeline",
        contradictions_heading: "Detected Contradictions",
        evidence_assessment_heading: "Evidence Assessment",
        risk_level_heading: "Overall Risk Level",
        risk_high: "High",
        risk_medium: "Medium",
        risk_low: "Low",
        confidence_strong: "Strong",
        confidence_moderate: "Moderate",
        confidence_weak: "Weak",
        follow_up_heading: "Recommended Follow-up Questions",
        next_steps_heading: "Recommended Next Steps",
        disclaimer_heading: "Human Review Disclaimer",
        none_found: "None found",
        no_contradictions: "No contradictions were detected between the documents.",
        no_dated_events: "No dated events were found.",
        no_contextual_statements: "No undated contextual statements were found.",
        claim_label: "Claim",
        claim_source_label: "Claim Source",
        conflicting_evidence_label: "Conflicting Evidence",
        evidence_source_label: "Evidence Source",
        reasoning_label: "Reasoning",
        confidence_label: "Rule Confidence",
        view_source_button: "View Source Evidence",
        print_button: "Print / Save Report",
        evidence_number_prefix: "Evidence",
        case_id_label: "Case ID",
        case_type_label: "Case Type",
        evidence_count_label: "Evidence Count",
    },
    ar: {
        nav_subtitle: "منصة التحقيق في الشركات",
        footer_disclaimer: "تساعد المحققين البشريين ولا تتخذ قرارات قانونية أو تأديبية.",
        footer_data_notice: "نسخة هاكاثون — للاستخدام مع بيانات وهمية أو غير حساسة فقط.",
        lang_toggle_label: "English",

        landing_subtitle: "منصة ذكاء اصطناعي للتحقيق المؤسسي وتحليل الأدلة",
        badge_hr: "الموارد البشرية",
        badge_compliance: "الالتزام",
        badge_audit: "التدقيق الداخلي",
        badge_legal: "الشؤون القانونية",
        try_demo_button: "جرّب التحقيق التجريبي",
        create_investigation_button: "إنشاء تحقيق جديد",
        problem_heading: "المشكلة",
        problem_text: "غالبًا ما تحتاج التحقيقات الداخلية إلى فريق يقارن يدويًا بين إفادات ورسائل وسجلات متفرقة.",
        solution_heading: "الحل",
        solution_text: "يحوّل Evidence AI الأدلة المتفرقة إلى حقائق وخط زمني وتناقضات وتقارير تحقيق منظّمة.",
        engine_section_heading: "كيف يعمل محرك التحقيق المحلي",
        engine_stage_1_name: "استخراج الحقائق",
        engine_stage_1_desc: "يقرأ المستندات المقدمة ويستخرج ادعاءات وقائعية محددة المصدر.",
        engine_stage_2_name: "بناء الخط الزمني",
        engine_stage_2_desc: "يرتّب الحقائق المستخرجة في تسلسل زمني واحد للأحداث.",
        engine_stage_3_name: "اكتشاف التناقضات",
        engine_stage_3_desc: "يقارن الإفادات بين المصادر لإظهار الروايات المتضاربة.",
        engine_stage_4_name: "إعداد التقرير",
        engine_stage_4_desc: "يجمع النتائج في تقرير تحقيق منظّم.",
        ethical_disclaimer: "يساعد Evidence AI المحققين البشريين ولا يتخذ قرارات قانونية أو تأديبية.",

        demo_data_notice: "بيانات تجريبية — جميع الأسماء والشركات أدناه وهمية.",
        evidence_documents_heading: "مستندات الأدلة",
        run_demo_button: "بدء التحقيق الذكي",

        new_investigation_heading: "إنشاء تحقيق جديد",
        new_investigation_subheading: "قدّم أدلتك الخاصة للتحليل المحلي القائم على القواعد.",
        privacy_notice: "تنبيه الخصوصية للنسخة التجريبية: تتم معالجة الأدلة داخل التطبيق ولا تُرسل إلى خدمة ذكاء اصطناعي خارجية. لا تستخدم بيانات شركات حقيقية أو سرية في هذه النسخة العامة.",
        case_title_label: "عنوان القضية",
        case_category_label: "فئة القضية",
        category_procurement: "الامتثال في المشتريات",
        category_hr: "مخالفات الموارد البشرية",
        category_audit: "التدقيق الداخلي",
        category_data_access: "حادثة الوصول للبيانات",
        category_other: "أخرى",
        report_language_label: "لغة التقرير",
        lang_option_en: "English",
        lang_option_ar: "العربية",
        evidence_section_heading: "الدليل {n}",
        evidence_section_heading_optional: "الدليل {n} (اختياري)",
        evidence_helper_text: "الحد الأدنى المطلوب: دليلان (2). يمكنك إضافة المزيد عند الحاجة.",
        evidence_title_label: "عنوان الدليل (اختياري)",
        evidence_title_placeholder: "اتركه فارغًا للإنشاء التلقائي (مثال: إفادة موظف #1)",
        evidence_type_label: "نوع الدليل",
        evidence_content_label: "نص الدليل",
        add_evidence_button: "إضافة دليل آخر",
        remove_evidence_button: "إزالة الدليل",
        load_sample_button: "تحميل قضية نموذجية",
        analyze_button: "تحليل الأدلة",
        max_evidence_reached: "تم الوصول إلى الحد الأقصى وهو 6 عناصر أدلة.",
        validation_title_required: "عنوان القضية مطلوب.",
        validation_min_evidence: "يرجى إضافة دليلين على الأقل يحتويان على نص قبل بدء التحليل. لديك حاليًا {count} مكتمل.",
        auto_evidence_title_format: "{type} #{n}",

        evidence_type_labels: {
            "Employee Statement": "إفادة موظف",
            "Email": "بريد إلكتروني",
            "Visitor Log": "سجل زوار",
            "Policy Document": "وثيقة سياسة",
            "Meeting Note": "محضر اجتماع",
            "Other": "أخرى",
        },

        pipeline_heading: "مراحل التحقيق",
        pipeline_step_1: "استخراج الحقائق والادعاءات",
        pipeline_step_2: "بناء الخط الزمني",
        pipeline_step_3: "مقارنة الأدلة",
        pipeline_step_4: "إعداد التقرير",
        pipeline_status_pending: "بانتظار",
        pipeline_status_processing: "جارٍ المعالجة",
        pipeline_status_complete: "مكتمل",
        analysis_running: "جارٍ تشغيل محرك التحقيق المحلي...",
        analysis_complete: "اكتمل التحليل في {seconds} ثانية.",
        analysis_error: "حدث خطأ أثناء تشغيل التحقيق. يرجى المحاولة مرة أخرى.",

        report_heading: "تقرير التحقيق",
        executive_summary_heading: "الملخص التنفيذي",
        case_information_heading: "معلومات القضية",
        involved_parties_heading: "الأطراف المعنية",
        people_label: "الأشخاص",
        organizations_label: "الجهات",
        verified_facts_heading: "الحقائق المؤكدة",
        dates_label: "التواريخ",
        emails_label: "رسائل البريد الإلكتروني",
        key_statements_label: "الإفادات الرئيسية",
        contextual_statements_heading: "إفادات سياقية",
        no_specific_time: "لا يوجد وقت محدد",
        timeline_heading: "الخط الزمني",
        contradictions_heading: "التناقضات المكتشفة",
        evidence_assessment_heading: "تقييم الأدلة",
        risk_level_heading: "مستوى المخاطر الإجمالي",
        risk_high: "مرتفع",
        risk_medium: "متوسط",
        risk_low: "منخفض",
        confidence_strong: "قوي",
        confidence_moderate: "متوسط",
        confidence_weak: "ضعيف",
        follow_up_heading: "أسئلة متابعة مقترحة",
        next_steps_heading: "الخطوات التالية الموصى بها",
        disclaimer_heading: "إخلاء المراجعة البشرية",
        none_found: "لم يعثر على شيء",
        no_contradictions: "لم يتم اكتشاف أي تناقضات بين المستندات.",
        no_dated_events: "لم يتم العثور على أحداث مؤرّخة.",
        no_contextual_statements: "لا توجد إفادات سياقية غير مؤرّخة.",
        claim_label: "الادعاء",
        claim_source_label: "مصدر الادعاء",
        conflicting_evidence_label: "الدليل المتعارض",
        evidence_source_label: "مصدر الدليل",
        reasoning_label: "التبرير",
        confidence_label: "درجة الثقة القائمة على القواعد",
        view_source_button: "عرض مصدر الدليل",
        print_button: "طباعة / حفظ التقرير",
        evidence_number_prefix: "الدليل",
        case_id_label: "رقم القضية",
        case_type_label: "نوع القضية",
        evidence_count_label: "عدد الأدلة",
    },
};

// The current interface language, persisted across page loads via localStorage.
// Falls back to English if nothing was saved yet or localStorage is unavailable.
function getCurrentLanguage() {
    try {
        return localStorage.getItem("evidenceAiLang") || "en";
    } catch (error) {
        return "en";
    }
}

function setCurrentLanguage(lang) {
    try {
        localStorage.setItem("evidenceAiLang", lang);
    } catch (error) {
        // localStorage can be unavailable (e.g. private browsing) - not translating
        // is a minor inconvenience, so we just silently continue.
    }
}

// Look up one translated string for the current language, with an optional
// {placeholder} substitution (e.g. t("analysis_complete", {seconds: "1.23"})).
function t(key, replacements) {
    const lang = getCurrentLanguage();
    let text = (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || TRANSLATIONS.en[key] || key;
    if (replacements) {
        Object.keys(replacements).forEach((name) => {
            text = text.replace("{" + name + "}", replacements[name]);
        });
    }
    return text;
}

// Translates a stored evidence type value (e.g. "Employee Statement") for display.
function translateEvidenceType(type) {
    const lang = getCurrentLanguage();
    const table = (TRANSLATIONS[lang] && TRANSLATIONS[lang].evidence_type_labels) || {};
    return table[type] || type;
}

// Walks every element with a data-i18n attribute and updates its text,
// then updates <html lang/dir> and the language toggle button itself.
function applyLanguage(lang) {
    setCurrentLanguage(lang);

    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

    document.querySelectorAll("[data-i18n]").forEach((element) => {
        const key = element.getAttribute("data-i18n");
        if (key) {
            element.textContent = t(key);
        }
    });

    const toggleButton = document.getElementById("lang-toggle-btn");
    if (toggleButton) {
        toggleButton.textContent = t("lang_toggle_label");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    applyLanguage(getCurrentLanguage());

    const toggleButton = document.getElementById("lang-toggle-btn");
    if (toggleButton) {
        toggleButton.addEventListener("click", () => {
            const nextLang = getCurrentLanguage() === "ar" ? "en" : "ar";
            applyLanguage(nextLang);
            // Let other scripts (e.g. a rendered report) know the language changed,
            // in case they want to re-render already-visible dynamic content.
            document.dispatchEvent(new CustomEvent("languageChanged", { detail: { lang: nextLang } }));
        });
    }
});
