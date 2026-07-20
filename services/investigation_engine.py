# services/investigation_engine.py
#
# This is the "Local Intelligent Investigation Engine" for Evidence AI.
#
# IMPORTANT: There is no AI model, LLM, or external API here. Everything in
# this file is plain Python: regular expressions and simple string/keyword
# checks that look for patterns a human investigator would also notice
# (names, dates, times, denial/confirmation phrases, etc). It is
# intentionally simple, transparent, and rule-based - every decision the
# engine makes can be traced back to a specific pattern in this file.
#
# It understands basic English and Arabic patterns (see the keyword lists
# below). This is NOT full natural-language understanding - it is keyword
# and pattern matching, kept deliberately simple so it stays easy to read,
# explain, and extend.
#
# The two functions other code should call are:
#   - run_investigation()  -> analyzes the built-in fictional demo case
#   - analyze_case(case)   -> analyzes ANY case (demo or user-submitted),
#                             as long as it's shaped like {case_id, title,
#                             case_type, documents: [...], report_language}

import json
import re
from datetime import date, datetime, time

from config import DEMO_CASE_PATH

# ---------------------------------------------------------------------------
# Regular expressions and keyword lists used across the extraction functions.
# Keeping them in one place makes them easy to find and tweak.
# ---------------------------------------------------------------------------

# Matches textual English dates like "March 12, 2026".
DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+\d{4}\b"
)

# Matches numeric dates like "12/03/2026" or "12-03-2026" (day/month/year).
# \d already matches Arabic-Indic digits (٠-٩) in Python, so this also
# catches dates typed with Arabic numerals, e.g. "١٢/٠٣/٢٠٢٦".
NUMERIC_DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b")

# Arabic month names, used for dates like "12 مارس 2026".
ARABIC_MONTHS = {
    "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "مايو": 5, "يونيو": 6,
    "يوليو": 7, "أغسطس": 8, "سبتمبر": 9, "أكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
}
_ARABIC_MONTH_PATTERN = "|".join(ARABIC_MONTHS.keys())
ARABIC_DATE_PATTERN = re.compile(r"\d{1,2}\s+(?:" + _ARABIC_MONTH_PATTERN + r")\s+\d{4}")

# Matches clock times: English "2:00 PM" / 24-hour "14:00" / Arabic "2:00 مساءً" or "1:52 م".
TIME_PATTERN = re.compile(
    r"\b(?:1[0-2]|0?[1-9]):[0-5]\d\s?(?:AM|PM|am|pm)\b"
    r"|\b(?:1[0-2]|0?[1-9]):[0-5]\d\s?(?:صباحاً|صباحا|مساءً|مساء|ص|م)\b"
    r"|\b(?:[01]?\d|2[0-3]):[0-5]\d\b"
)

# Matches email addresses, e.g. "j.whitmore@fictionalcorp-demo.com".
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Matches two-word Capitalized Names, e.g. "Jordan Whitmore".
# NOTE: uses a literal space (not \s) so it can never match across a line break.
PERSON_NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")

# Matches "I, Jordan Whitmore," style self-identification in statements.
SELF_ID_PATTERN = re.compile(r"\bI,\s([A-Z][a-z]+\s[A-Z][a-z]+),")

# Matches email-style signatures like "- Renee Delgado, Halcyon Supply Co."
SIGNATURE_PATTERN = re.compile(r"(?m)^-\s*([A-Z][a-z]+\s[A-Z][a-z]+)")

# Matches "Label: Value" lines, common in logs, emails, and forms.
LABELED_LINE_PATTERN = re.compile(r"^([A-Za-z][A-Za-z \-]*):\s*(.+)$", re.MULTILINE)

# Common company-name endings, used to detect organization names.
ORG_SUFFIXES = [
    "Corporation", "Company", "Partners", "Group",
    "Inc.", "Inc", "LLC", "Ltd.", "Ltd", "Corp.", "Corp", "Co.",
    "Logistics", "Authority", "Agency", "Institute", "Foundation",
    "Bureau", "Association", "University", "Holdings", "Technologies", "Solutions",
]
_ORG_SUFFIX_PATTERN = "|".join(re.escape(suffix) for suffix in ORG_SUFFIXES)
# NOTE: uses a literal space (not \s) so it can never match across a line break.
ORG_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z&]*(?: [A-Z][A-Za-z&]*)* (?:" + _ORG_SUFFIX_PATTERN + r")"
)

# Well-known organization names that don't end in a corporate suffix (so
# ORG_PATTERN can't catch them) and can't be told apart from a person's name
# by shape alone. This is a plain lookup table (still fully rule-based, no
# AI) - short on purpose, just enough to cover common real-world mentions.
KNOWN_ORGANIZATION_NAMES = [
    "OpenAI", "Microsoft", "Google", "Amazon", "Apple", "Meta", "IBM",
    "Anthropic", "Oracle", "Tesla", "Intel", "Samsung", "Nvidia", "Netflix",
]
KNOWN_ORGANIZATION_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(name) for name in KNOWN_ORGANIZATION_NAMES) + r")\b"
)

# Header/label and greeting words that look Capitalized but are not real person names.
HEADER_STOPWORDS = {
    "Visitor", "Log", "Entry", "Email", "Thread", "Meeting", "Confirmation",
    "Building", "Employee", "Statement", "Date", "Subject", "Check",
    "From", "Report", "Case", "Investigation", "Document",
    "Hi", "Hello", "Dear", "See", "Thanks", "Regards",
}

# Capitalized single-word tokens that look like names but are actually
# headers, pronouns, or generic sentence-start words - not real names.
# Shared by entity extraction (extract_people) and contradiction detection's
# "same subject" check (_subject_candidates).
SUBJECT_CANDIDATE_STOPWORDS = HEADER_STOPWORDS | {
    "The", "This", "That", "These", "Those", "It", "He", "She", "They", "We", "You",
    "Was", "Were", "Did", "Does", "Do", "Is", "Are", "Has", "Have", "Had",
    "No", "Yes", "Not",
    "Company", "Vendor", "Warehouse", "Office", "Policy",
    "Corp", "Inc", "Ltd", "Co",
    # Common sentence-start discourse markers/adverbs - capitalized only because
    # they open a sentence, not because they're names.
    "Later", "Then", "Meanwhile", "Afterward", "Afterwards", "Suddenly",
    "Finally", "Additionally", "However", "Also", "Moreover", "Furthermore",
    "Therefore", "Thus", "Nevertheless", "Nonetheless", "Consequently",
    "Overall", "Initially", "Eventually", "Previously", "Subsequently",
}

# Single Capitalized words (e.g. "Ahmed"), unlike PERSON_NAME_PATTERN which
# requires two words - both a person's first name and a contradiction's
# subject are often referred to by a single word.
SINGLE_NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+\b")

# Words/phrases that flag a sentence as an important claim worth surfacing.
# English and Arabic phrases are mixed into the same lists on purpose: the
# matching function is just a case-insensitive substring check, so it works
# for either language with no extra branching.
STATEMENT_KEYWORDS = [
    "confirm", "deny", "denied", "no meeting", "did not", "meeting",
    "checked in", "checked out", "entered", "recall", "state", "believe", "dispute",
    "لم يحدث اجتماع", "لم يتم الاجتماع", "لم أقابل", "لم أحضر", "لا أتذكر", "أنكر", "لم ألتقِ",
    "تم تأكيد الاجتماع", "تم تسجيل الدخول", "حضر الزائر", "دخل المبنى",
    "تم الاجتماع", "تؤكد الرسالة", "يثبت السجل",
]

# Negation cues that flip a neutral action word (e.g. "entered") into a
# denial (e.g. "never entered"). Matched as whole words/phrases so we don't
# false-positive inside unrelated words (e.g. "not" inside "note"). Covers
# the forms called out in the contradiction-detection requirements, plus a
# few obvious siblings ("does not", "is not", ...) for practical coverage.
NEGATION_PATTERN = re.compile(
    r"\b(?:"
    r"did not|didn['’]t|does not|doesn['’]t|"
    r"was not|wasn['’]t|were not|weren['’]t|"
    r"cannot|can['’]t|will not|won['’]t|"
    r"is not|isn['’]t|are not|aren['’]t|"
    r"never|not|no"
    r")\b",
    re.IGNORECASE,
)


def _build_form_pattern(forms):
    """Compile a case-insensitive whole-word/phrase alternation for a list of surface forms."""
    if not forms:
        return None
    return re.compile(r"\b(?:" + "|".join(re.escape(form) for form in forms) + r")\b", re.IGNORECASE)


# Rule-based "action concepts" used by contradiction detection: each is a
# real-world action/state that can be asserted as having happened via a
# neutral "positive form" (e.g. "entered", flipped to a denial by a
# NEGATION_PATTERN cue like "never"), or denied outright via its own
# inherently-negative words (e.g. "rejected" negates "approval" without
# needing a separate negation cue).
_ACTION_CONCEPT_DEFINITIONS = [
    {
        # Kept broad (meeting/visitor-log/check-in phrasing) to match the
        # original demo case, where a denied meeting is corroborated by a
        # building visitor log rather than the word "meeting" itself.
        "key": "meeting",
        "positive_forms": [
            "meeting", "meet", "met", "checked in", "check-in", "check-out",
            "visitor log", "entered the building",
        ],
        "negative_forms": ["never took place", "never happened", "no vendor visit"],
        "label": {"en": "meeting", "ar": "الاجتماع"},
    },
    {
        "key": "entry",
        "positive_forms": ["entered", "enter", "enters", "entering", "entry"],
        "negative_forms": [],
        "label": {"en": "entry", "ar": "الدخول"},
    },
    {
        "key": "attendance",
        "positive_forms": ["attended", "attend", "attends", "attending", "attendance"],
        "negative_forms": [],
        "label": {"en": "attendance", "ar": "الحضور"},
    },
    {
        "key": "approval",
        "positive_forms": ["approved", "approve", "approves", "approving", "approval"],
        "negative_forms": ["rejected", "reject", "rejects", "rejection", "declined", "decline"],
        "label": {"en": "approval", "ar": "الموافقة"},
    },
    {
        "key": "payment",
        "positive_forms": ["paid", "pay", "pays", "paying", "payment"],
        "negative_forms": [],
        "label": {"en": "payment", "ar": "الدفع"},
    },
    {
        "key": "receipt",
        "positive_forms": ["received", "receive", "receives", "receiving", "receipt"],
        "negative_forms": [],
        "label": {"en": "receipt", "ar": "الاستلام"},
    },
    {
        "key": "delivery",
        "positive_forms": ["delivered", "deliver", "delivers", "delivering", "delivery"],
        "negative_forms": [],
        "label": {"en": "delivery", "ar": "التسليم"},
    },
    {
        "key": "presence",
        "positive_forms": ["present"],
        "negative_forms": ["absent", "absence"],
        "label": {"en": "presence", "ar": "الحضور"},
    },
    {
        "key": "authorization",
        "positive_forms": ["authorized", "authorize", "authorizes", "authorizing", "authorization"],
        "negative_forms": ["unauthorized"],
        "label": {"en": "authorization", "ar": "التصريح"},
    },
    {
        "key": "access",
        "positive_forms": ["accessed", "access", "accesses", "accessing"],
        "negative_forms": [],
        "label": {"en": "access", "ar": "الوصول"},
    },
]

ACTION_CONCEPTS = [
    {
        **concept,
        "positive_pattern": _build_form_pattern(concept["positive_forms"]),
        "negative_pattern": _build_form_pattern(concept["negative_forms"]),
    }
    for concept in _ACTION_CONCEPT_DEFINITIONS
]

# Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) -> Western digits (0123456789), used only
# when we need to actually *parse* a number (e.g. for chronological sorting).
# Detection with \d already works on Arabic-Indic digits without this table.
_ARABIC_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

ARABIC_PM_MARKERS = ("مساءً", "مساء", "م")
ARABIC_AM_MARKERS = ("صباحاً", "صباحا", "ص")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _normalize_arabic_digits(text):
    """Convert Arabic-Indic digits to Western digits so strptime can parse them."""
    return text.translate(_ARABIC_DIGIT_TRANSLATION)


def _time_from_hour_minute(hour_minute_text, is_pm):
    """Turn an 'H:MM' string plus an AM/PM flag into a 24-hour Python time, or None."""
    try:
        hour_text, minute_text = hour_minute_text.strip().split(":")
        hour, minute = int(hour_text), int(minute_text)
    except ValueError:
        return None
    if is_pm and hour != 12:
        hour += 12
    if not is_pm and hour == 12:
        hour = 0
    try:
        return time(hour=hour, minute=minute)
    except ValueError:
        return None


def parse_date_string(date_str):
    """Turn a date (English, numeric, or Arabic) into a real Python date, or None if it can't be parsed."""
    if not date_str:
        return None
    normalized = _normalize_arabic_digits(date_str.strip())

    try:
        return datetime.strptime(normalized, "%B %d, %Y").date()
    except ValueError:
        pass

    for numeric_format in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(normalized, numeric_format).date()
        except ValueError:
            continue

    arabic_match = re.match(r"(\d{1,2})\s+(\S+)\s+(\d{4})", normalized)
    if arabic_match:
        day_text, month_name, year_text = arabic_match.groups()
        month_number = ARABIC_MONTHS.get(month_name)
        if month_number:
            try:
                return date(int(year_text), month_number, int(day_text))
            except ValueError:
                return None

    return None


def parse_time_string(time_str):
    """Turn a time (English AM/PM, 24-hour, or Arabic AM/PM) into a real Python time, or None."""
    if not time_str or time_str == "Time not specified":
        return None
    cleaned = _normalize_arabic_digits(time_str.strip())

    for marker in ARABIC_PM_MARKERS:
        if cleaned.endswith(marker):
            return _time_from_hour_minute(cleaned[: -len(marker)], is_pm=True)
    for marker in ARABIC_AM_MARKERS:
        if cleaned.endswith(marker):
            return _time_from_hour_minute(cleaned[: -len(marker)], is_pm=False)

    upper = cleaned.upper()
    for time_format in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(upper, time_format).time()
        except ValueError:
            continue
    return None


def _contains_any(text, keywords):
    """Return True if the text (case-insensitive) contains any of the given keywords."""
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _overlaps_any(span, spans):
    """Check whether (start, end) overlaps any of the given (start, end) spans."""
    start, end = span
    return any(other_start < end and start < other_end for other_start, other_end in spans)


def _date_spans(text):
    """Character ranges of every date mention (English or numeric), so a month name like
    "March" in "March 12, 2026" is never mistaken for a person's name."""
    return (
        [match.span() for match in DATE_PATTERN.finditer(text)]
        + [match.span() for match in NUMERIC_DATE_PATTERN.finditer(text)]
    )


def _organization_spans(text):
    """Character ranges of every likely organization mention (suffix-based or well-known
    name), so extract_people never mistakes an organization's words (e.g. "Halcyon",
    "Riyadh Metro") for a person's name."""
    return (
        [match.span() for match in ORG_PATTERN.finditer(text)]
        + [match.span() for match in KNOWN_ORGANIZATION_PATTERN.finditer(text)]
    )


def _first_appearance_order(indexed_items):
    """Given a list of (start_index, value) tuples, return the unique values ordered by
    where each first appears in the source text (not alphabetically)."""
    return _dedupe_preserve_order(value for _, value in sorted(indexed_items, key=lambda item: item[0]))


def _dedupe_preserve_order(items):
    """Remove duplicates from an already-ordered iterable, keeping each item's first occurrence."""
    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _prefer_full_names(names):
    """If both a bare first name and a fuller "First Last" name are present (e.g. "Jordan"
    and "Jordan Whitmore" - the same person referred to differently in different evidence),
    drop the bare first name and keep only the fuller one."""
    full_name_first_words = {name.split()[0] for name in names if " " in name}
    return [name for name in names if " " in name or name not in full_name_first_words]


def _clean_snippet(text, max_length=150):
    """Collapse a block of text onto one line (no stray newlines) and trim it to a readable length."""
    single_line = " ".join(text.split())
    return single_line[:max_length].strip()


# ---------------------------------------------------------------------------
# Evidence loading
# ---------------------------------------------------------------------------

def load_demo_case():
    """Read the built-in demo case JSON file from disk and return it as a Python dictionary."""
    with open(DEMO_CASE_PATH, "r", encoding="utf-8") as demo_file:
        return json.load(demo_file)


def build_case_from_custom_input(case_title, case_category, report_language, evidence_items):
    """Turn user-submitted form/API data into the same case shape load_demo_case() produces."""
    case_id = "CUSTOM-" + datetime.now().strftime("%Y%m%d%H%M%S")
    documents = [
        {
            "id": f"EVIDENCE-{position}",
            "name": item["title"],
            "type": item["type"],
            "content": item["content"],
        }
        for position, item in enumerate(evidence_items, start=1)
    ]
    return {
        "case_id": case_id,
        "title": case_title,
        "case_type": case_category,
        "report_language": report_language,
        "documents": documents,
    }


# ---------------------------------------------------------------------------
# Fact extraction (regex/keyword-based, no AI)
# ---------------------------------------------------------------------------

def extract_dates(text):
    """Find every date (English, numeric, or Arabic) mentioned in the text."""
    found = DATE_PATTERN.findall(text) + NUMERIC_DATE_PATTERN.findall(text) + ARABIC_DATE_PATTERN.findall(text)
    return sorted(set(found))


def extract_times(text):
    """Find every clock time (English, 24-hour, or Arabic) mentioned in the text."""
    return sorted(set(TIME_PATTERN.findall(text)))


def extract_emails(text):
    """Find every email address mentioned in the text."""
    return sorted(set(EMAIL_PATTERN.findall(text)))


def extract_people(text):
    """Find likely person names using labeled fields, self-identification, signatures, and
    general name patterns - both two-word names ("Jordan Whitmore") and single first names
    ("Ahmed"). Returned in the order each name first appears in the text (not alphabetically).

    NOTE: this only recognizes English Capitalized names. It does not attempt to
    extract Arabic names - if a name can't be reliably identified, none is invented.
    """
    org_spans = _organization_spans(text)
    # Every "Label: Value" line, e.g. "Subject: Confirming today's meeting" or "To: ...".
    # Only the specific labels handled below (visitor/host/employee/attendee) contain a
    # name - the rest are structured fields, not narrative text, so they're excluded from
    # the general name scans below to avoid mistaking a label or its value (e.g.
    # "Confirming", the first word of a Subject line) for a person's name.
    labeled_line_spans = [match.span() for match in LABELED_LINE_PATTERN.finditer(text)]
    matches = []  # (start_index, name)

    # "Label: Value" lines such as "Visitor: Renee Delgado" or "Host: Jordan Whitmore".
    for line_match in LABELED_LINE_PATTERN.finditer(text):
        label, value = line_match.group(1), line_match.group(2)
        if any(keyword in label.lower() for keyword in ["visitor", "host", "employee", "attendee"]):
            value = value.strip()
            if PERSON_NAME_PATTERN.fullmatch(value):
                matches.append((line_match.start(2), value))

    # Sworn-statement style: "I, Jordan Whitmore, confirm ..."
    for id_match in SELF_ID_PATTERN.finditer(text):
        matches.append((id_match.start(1), id_match.group(1)))

    # Email sign-offs: "- Renee Delgado, Halcyon Supply Co."
    for signature_match in SIGNATURE_PATTERN.finditer(text):
        matches.append((signature_match.start(1), signature_match.group(1)))

    # Any other two-word Capitalized phrase that isn't a header word, a labeled field, or
    # an organization name.
    two_word_spans = []
    for name_match in PERSON_NAME_PATTERN.finditer(text):
        candidate = name_match.group()
        if any(word in HEADER_STOPWORDS for word in candidate.split()):
            continue
        if _overlaps_any(name_match.span(), org_spans) or _overlaps_any(name_match.span(), labeled_line_spans):
            continue
        matches.append((name_match.start(), candidate))
        two_word_spans.append(name_match.span())

    # Single Capitalized words (e.g. "Ahmed") that aren't already covered by a two-word
    # name, an organization mention, a date (so "March" isn't mistaken for a name), a
    # labeled field, or a common non-name word (sentence starters, pronouns, headers).
    excluded_spans = org_spans + two_word_spans + labeled_line_spans + _date_spans(text)
    for name_match in SINGLE_NAME_PATTERN.finditer(text):
        candidate = name_match.group()
        if candidate in SUBJECT_CANDIDATE_STOPWORDS:
            continue
        if _overlaps_any(name_match.span(), excluded_spans):
            continue
        matches.append((name_match.start(), candidate))

    return _prefer_full_names(_first_appearance_order(matches))


def extract_organizations(text):
    """Find likely company/organization names: common suffixes (Co., Inc., LLC, Logistics,
    Authority, ...), a small lookup of well-known names that have no suffix (Microsoft,
    OpenAI, ...), and "Label: Value" lines such as "Company: Halcyon Supply Co.". Returned
    in the order each organization first appears in the text (not alphabetically).
    """
    matches = []  # (start_index, name)

    for org_match in ORG_PATTERN.finditer(text):
        name, start = org_match.group(), org_match.start()
        # A sentence-initial "The" (capitalized, so it's swept up by ORG_PATTERN's
        # capitalized-word run) reads oddly in a report - e.g. "The Riyadh Metro
        # Authority" instead of "Riyadh Metro Authority".
        if name.startswith("The "):
            name, start = name[4:], start + 4
        matches.append((start, name))

    for known_match in KNOWN_ORGANIZATION_PATTERN.finditer(text):
        matches.append((known_match.start(), known_match.group()))

    for line_match in LABELED_LINE_PATTERN.finditer(text):
        label, value = line_match.group(1), line_match.group(2)
        if any(keyword in label.lower() for keyword in ["company", "vendor", "organization", "employer"]):
            matches.append((line_match.start(2), value.strip()))

    return _first_appearance_order(matches)


def extract_key_statements(text):
    """Pick out sentences that look investigatively important based on keyword matches."""
    # Skip structured "Label: Value" lines (e.g. email headers) - they aren't narrative sentences.
    narrative_lines = [
        line for line in text.split("\n")
        if line.strip() and not LABELED_LINE_PATTERN.match(line.strip())
    ]
    single_line_text = " ".join(narrative_lines)
    sentences = re.split(r"(?<=[.!?؟])\s+", single_line_text)

    statements = []
    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned and _contains_any(cleaned, STATEMENT_KEYWORDS):
            statements.append(cleaned)
    return statements


def analyze_document(document):
    """Run every extraction function on one document and return the document plus its extracted facts."""
    text = document.get("content", "")
    return {
        **document,
        "people": extract_people(text),
        "organizations": extract_organizations(text),
        "dates": extract_dates(text),
        "times": extract_times(text),
        "emails": extract_emails(text),
        "key_statements": extract_key_statements(text),
    }


# ---------------------------------------------------------------------------
# Timeline builder
# ---------------------------------------------------------------------------

def _source_info(document):
    """Build the small "where did this come from" block reused on facts, timeline events, and contradictions."""
    return {
        "source_title": document["name"],
        "source_type": document.get("type", ""),
        "source_index": document["index"],
    }


def _make_timeline_event(date_text, time_text, description, document):
    """Build one timeline event dictionary, fully traceable back to its source document."""
    return {
        "date": date_text,
        "time": time_text,
        "has_specific_time": True,
        "description": description,
        "evidence_excerpt": _clean_snippet(description, max_length=160),
        **_source_info(document),
    }


def _make_contextual_statement(document, statement_text):
    """Build one undated/untimed contextual statement, traceable back to its source document."""
    return {
        "statement": statement_text,
        "has_specific_time": False,
        **_source_info(document),
    }


def _timeline_sort_key(event):
    """Turn an event's date/time text into something that sorts in real chronological order."""
    parsed_date = parse_date_string(event["date"]) if event["date"] else None
    parsed_time = parse_time_string(event["time"])
    date_key = parsed_date or date.max
    time_key = parsed_time or time.min
    return (date_key, time_key)


def build_timeline(analyzed_documents):
    """Split every document's dated content into two groups: timed events and undated contextual statements."""
    timed_events = []
    contextual_statements = []

    for document in analyzed_documents:
        document_date = document["dates"][0] if document["dates"] else None
        found_a_time = False

        # Look line-by-line so each event description is short and readable.
        for line in document.get("content", "").split("\n"):
            for time_text in TIME_PATTERN.findall(line):
                found_a_time = True
                timed_events.append(_make_timeline_event(document_date, time_text, line.strip(), document))

        # No specific time mentioned - record it as a contextual statement instead of a timed event.
        if not found_a_time:
            if document["key_statements"]:
                statement_text = document["key_statements"][0].strip()
            else:
                statement_text = _clean_snippet(document.get("content", ""), max_length=80)
            contextual_statements.append(_make_contextual_statement(document, statement_text))

    timed_events.sort(key=_timeline_sort_key)
    return timed_events, contextual_statements


# ---------------------------------------------------------------------------
# Contradiction detection
# ---------------------------------------------------------------------------

def _shared_date(dates_a, dates_b):
    """Return a real calendar date mentioned by both documents, or None if they don't share one.

    Dates are compared after parsing (not as raw text), so "March 12, 2026",
    "12/03/2026", and "12 مارس 2026" are all recognized as the same day.
    """
    parsed_a = {parse_date_string(text) for text in dates_a} - {None}
    parsed_b = {parse_date_string(text) for text in dates_b} - {None}
    common_dates = parsed_a & parsed_b
    return min(common_dates) if common_dates else None


def _document_spans(text):
    """Split document text into short, checkable spans: one per narrative sentence,
    plus one per structured "Label: Value" line (e.g. visitor-log fields), so a
    fact like "Check-in: 1:52 PM" is still checkable even though it isn't a sentence.
    """
    spans = []
    narrative_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if LABELED_LINE_PATTERN.match(stripped):
            spans.append(stripped)
        else:
            narrative_lines.append(stripped)

    single_line_text = " ".join(narrative_lines)
    for sentence in re.split(r"(?<=[.!?؟])\s+", single_line_text):
        cleaned = sentence.strip()
        if cleaned:
            spans.append(cleaned)
    return spans


def _subject_candidates(span_text):
    """Best-effort guess at who/what a span is about, using single Capitalized words
    (e.g. "Ahmed"). Used only to avoid contradicting two different subjects'
    statements (e.g. "Ahmed entered" must never contradict "Khalid did not enter").
    An empty result means "no identifiable subject" - callers should then skip the
    subject check rather than treat it as a mismatch.
    """
    date_spans = _date_spans(span_text)
    return {
        match.group() for match in SINGLE_NAME_PATTERN.finditer(span_text)
        if match.group() not in SUBJECT_CANDIDATE_STOPWORDS and not _overlaps_any(match.span(), date_spans)
    }


# How many words immediately before an action word count as "negating" it.
# Kept short on purpose: negation cues in the required patterns always sit
# right next to the word they negate ("never entered", "did not attend",
# "was not delivered", "cannot access"). A short window means a negation
# earlier in a longer sentence doesn't "leak" onto a later, unrelated action
# word - e.g. in "was not authorized to access", this negates "authorized"
# but correctly leaves "access" positive.
NEGATION_WINDOW_WORDS = 2


def _has_preceding_negation(span_text, match_start):
    """Check for a negation cue in the few words immediately before an action word match."""
    preceding_words = re.findall(r"[\w'’-]+", span_text[:match_start])
    window = " ".join(preceding_words[-NEGATION_WINDOW_WORDS:])
    return bool(NEGATION_PATTERN.search(window))


def _extract_claims(document):
    """Break a document into "claims": one entry per (span, action concept) it
    mentions, each tagged with a polarity - "positive" (the action is asserted to
    have happened) or "negative" (asserted NOT to have happened, via a negation
    cue like "never"/"did not" immediately before it, or an inherently-negative
    word like "rejected").
    """
    claims = []
    for span in _document_spans(document.get("content", "")):
        subjects = _subject_candidates(span)
        for concept in ACTION_CONCEPTS:
            if concept["negative_pattern"] and concept["negative_pattern"].search(span):
                claims.append({"concept": concept["key"], "polarity": "negative", "text": span, "subjects": subjects})
                continue
            if concept["positive_pattern"]:
                match = concept["positive_pattern"].search(span)
                if match:
                    polarity = "negative" if _has_preceding_negation(span, match.start()) else "positive"
                    claims.append({"concept": concept["key"], "polarity": polarity, "text": span, "subjects": subjects})
    return claims


def calculate_confidence(negative_doc, positive_doc, has_shared_date=True):
    """Score how strongly the evidence supports a contradiction, using simple additive rules.

    This is NOT machine-learning confidence - it is a transparent point system:
      +25  the two documents share a normalized date
      +20  the first document contains a negative (denying) claim
      +20  the second document contains a matching positive (confirming) claim
      +20  the confirming document includes an exact timestamp (stronger evidence)
      +15  both documents mention the same person or organization
    The score is capped at 100.
    """
    score = (25 if has_shared_date else 0) + 20 + 20  # date + negative claim + positive claim

    if positive_doc["times"]:
        score += 20

    shared_people = set(negative_doc["people"]) & set(positive_doc["people"])
    shared_orgs = set(negative_doc["organizations"]) & set(positive_doc["organizations"])
    if shared_people or shared_orgs:
        score += 15

    score = min(score, 100)

    if score >= 80:
        label = "Strong"
    elif score >= 50:
        label = "Moderate"
    else:
        label = "Weak"

    return score, label


def detect_contradictions(analyzed_documents, language):
    """Flag document pairs that make opposite claims about the same action concept.

    A contradiction requires: the same action concept (e.g. "entry"), opposite
    polarity (one document denies it, the other confirms it), the same subject
    when either side names one (so "Ahmed entered" never contradicts "Khalid did
    not enter"), and a shared date whenever either document mentions one.
    """
    contradictions = []
    claims_by_index = {doc["index"]: _extract_claims(doc) for doc in analyzed_documents}
    seen_pairs = set()

    for negative_doc in analyzed_documents:
        for positive_doc in analyzed_documents:
            if positive_doc is negative_doc:
                continue

            for negative_claim in claims_by_index[negative_doc["index"]]:
                if negative_claim["polarity"] != "negative":
                    continue

                for positive_claim in claims_by_index[positive_doc["index"]]:
                    if positive_claim["polarity"] != "positive":
                        continue
                    if positive_claim["concept"] != negative_claim["concept"]:
                        continue

                    # Only enforce a subject match when BOTH sides actually name one -
                    # a structured log line often has no identifiable subject at all.
                    if negative_claim["subjects"] and positive_claim["subjects"]:
                        if not (negative_claim["subjects"] & positive_claim["subjects"]):
                            continue

                    shared_date = _shared_date(negative_doc["dates"], positive_doc["dates"])
                    dates_mentioned = negative_doc["dates"] or positive_doc["dates"]
                    if dates_mentioned and not shared_date:
                        continue  # one or both sides name a date, but not the same one

                    pair_key = (negative_doc["index"], positive_doc["index"], negative_claim["concept"])
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    concept_label = next(
                        concept["label"][language] for concept in ACTION_CONCEPTS
                        if concept["key"] == negative_claim["concept"]
                    )

                    if shared_date:
                        if language == "ar":
                            shared_date_text = shared_date.strftime("%d/%m/%Y")
                        else:
                            shared_date_text = f"{shared_date.strftime('%B')} {shared_date.day}, {shared_date.year}"
                        reasoning = REASONING_TEXT[language].format(
                            claim_source=negative_doc["name"],
                            date=shared_date_text,
                            evidence_source=positive_doc["name"],
                            concept=concept_label,
                        )
                    else:
                        reasoning = REASONING_TEXT_NO_DATE[language].format(
                            claim_source=negative_doc["name"],
                            evidence_source=positive_doc["name"],
                            concept=concept_label,
                        )

                    # A confirming document with an actual timestamp (e.g. a visitor log) is stronger evidence.
                    severity = "High" if positive_doc["times"] else "Medium"
                    confidence_score, confidence_label = calculate_confidence(
                        negative_doc, positive_doc, has_shared_date=bool(shared_date)
                    )

                    contradictions.append({
                        "claim": negative_claim["text"],
                        "claim_source_title": negative_doc["name"],
                        "claim_source_type": negative_doc.get("type", ""),
                        "claim_source_index": negative_doc["index"],
                        "conflicting_evidence": positive_claim["text"],
                        "conflicting_evidence_source_title": positive_doc["name"],
                        "conflicting_evidence_source_type": positive_doc.get("type", ""),
                        "conflicting_evidence_source_index": positive_doc["index"],
                        "reasoning": reasoning,
                        "severity": severity,
                        "confidence_score": confidence_score,
                        "confidence_label": confidence_label,
                    })

    return contradictions


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

# Text the engine generates itself (as opposed to fixed interface labels,
# which the frontend translates). Keeping this as the one place these
# sentences are written avoids duplicating language dictionaries elsewhere.
NEXT_STEPS_TEXT = {
    "en": {
        "High": [
            "Interview the individuals involved to clarify the discrepancy.",
            "Preserve and cross-check supporting records (emails, visitor logs, access badges).",
            "Escalate the case to Compliance or Legal for formal review.",
        ],
        "Medium": [
            "Request additional documentation to clarify the inconsistency.",
            "Follow up with the relevant parties for clarification.",
        ],
        "Low": ["No contradictions detected. Continue standard documentation review."],
    },
    "ar": {
        "High": [
            "إجراء مقابلات مع الأشخاص المعنيين لتوضيح التناقض.",
            "حفظ ومراجعة السجلات الداعمة (البريد الإلكتروني، سجلات الزوار، بطاقات الدخول).",
            "تصعيد الحالة إلى إدارة الالتزام أو الشؤون القانونية للمراجعة الرسمية.",
        ],
        "Medium": [
            "طلب مستندات إضافية لتوضيح التناقض.",
            "المتابعة مع الأطراف المعنية للحصول على توضيح.",
        ],
        "Low": ["لم يتم اكتشاف أي تناقضات. الاستمرار في المراجعة المستندية القياسية."],
    },
}

RISK_LEVEL_TEXT_AR = {"High": "مرتفع", "Medium": "متوسط", "Low": "منخفض"}

REASONING_TEXT = {
    "en": "\"{claim_source}\" indicates the {concept} did not occur on {date}, while \"{evidence_source}\" contains evidence suggesting it did.",
    "ar": "تشير \"{claim_source}\" إلى أن {concept} لم يحدث في {date}، بينما يقدّم \"{evidence_source}\" دليلاً يشير إلى حدوثه.",
}

REASONING_TEXT_NO_DATE = {
    "en": "\"{claim_source}\" indicates the {concept} did not occur, while \"{evidence_source}\" contains evidence suggesting it did.",
    "ar": "تشير \"{claim_source}\" إلى أن {concept} لم يحدث، بينما يقدّم \"{evidence_source}\" دليلاً يشير إلى حدوثه.",
}

DISCLAIMER_TEXT = {
    "en": (
        "This report is a decision-support tool. It does not determine guilt, "
        "liability, or disciplinary action. All findings must be reviewed by "
        "an authorized human investigator."
    ),
    "ar": (
        "هذا التقرير أداة مساندة لاتخاذ القرار، ولا يحدد الإدانة أو المسؤولية "
        "أو الإجراء التأديبي. يجب مراجعة جميع النتائج من قبل محقق بشري مخوّل."
    ),
}

FOLLOW_UP_TEMPLATES = {
    "en": {
        "clarify_person": "Can {person} clarify the conflicting evidence found in \"{source}\"?",
        "clarify_source": "Can the author of \"{claim_source}\" clarify the conflicting evidence in \"{source}\"?",
        "policy_check": "Was this activity authorized under the applicable {case_type} policy?",
        "policy_check_generic": "Was this activity authorized under the applicable policy?",
        "records_check": (
            "Are any additional records available (badge access, calendar, or "
            "system logs) to corroborate the timeline?"
        ),
    },
    "ar": {
        "clarify_person": "هل يمكن لـ {person} توضيح الدليل المتعارض الوارد في \"{source}\"؟",
        "clarify_source": "هل يمكن لمُعِدّ \"{claim_source}\" توضيح الدليل المتعارض في \"{source}\"؟",
        "policy_check": "هل كان هذا النشاط مصرحًا به بموجب سياسة {case_type} المعمول بها؟",
        "policy_check_generic": "هل كان هذا النشاط مصرحًا به بموجب السياسة المعمول بها؟",
        "records_check": "هل تتوفر سجلات إضافية (الدخول بالبطاقة، التقويم، أو سجلات الأنظمة) لدعم الجدول الزمني؟",
    },
}


def determine_risk_level(contradictions):
    """Turn the detected contradictions into a simple overall risk rating."""
    if any(item["severity"] == "High" for item in contradictions):
        return "High"
    if contradictions:
        return "Medium"
    return "Low"


def recommend_next_steps(risk_level, language):
    """Suggest simple next actions for a human investigator, in the chosen report language."""
    return NEXT_STEPS_TEXT[language][risk_level]


def generate_executive_summary(case, analyzed_documents, contradictions, risk_level, language):
    """Write a short overview of what the engine found, in the chosen report language."""
    if language == "ar":
        risk_text = RISK_LEVEL_TEXT_AR.get(risk_level, risk_level)
        return (
            f"راجع نظام Evidence AI {len(analyzed_documents)} من الأدلة الخاصة بالقضية "
            f"{case['case_id']} (\"{case['title']}\"). وجد التحليل {len(contradictions)} "
            f"من التناقضات بين المصادر، بمستوى مخاطر إجمالي: {risk_text}."
        )
    return (
        f"Evidence AI reviewed {len(analyzed_documents)} document(s) for case {case['case_id']} "
        f"(\"{case['title']}\"). The analysis found {len(contradictions)} contradiction(s) "
        f"between sources, resulting in an overall risk level of {risk_level}."
    )


def generate_follow_up_questions(contradictions, analyzed_documents, case_type, language):
    """Suggest follow-up questions using simple templates filled in from the extracted evidence."""
    templates = FOLLOW_UP_TEMPLATES[language]
    documents_by_index = {doc["index"]: doc for doc in analyzed_documents}
    questions = []

    for item in contradictions:
        claim_doc = documents_by_index.get(item["claim_source_index"])
        claim_person = claim_doc["people"][0] if claim_doc and claim_doc["people"] else None

        if claim_person:
            question = templates["clarify_person"].format(
                person=claim_person,
                source=item["conflicting_evidence_source_title"],
            )
        else:
            question = templates["clarify_source"].format(
                claim_source=item["claim_source_title"],
                source=item["conflicting_evidence_source_title"],
            )
        if question not in questions:
            questions.append(question)

    if contradictions:
        if case_type:
            questions.append(templates["policy_check"].format(case_type=case_type))
        else:
            questions.append(templates["policy_check_generic"])
        questions.append(templates["records_check"])

    return questions


def build_evidence_assessment(analyzed_documents):
    """Summarize what was found in each piece of evidence (a simple per-source scorecard)."""
    return [
        {
            "index": document["index"],
            "title": document["name"],
            "type": document.get("type", ""),
            "people_found": len(document["people"]),
            "organizations_found": len(document["organizations"]),
            "dates_found": len(document["dates"]),
            "times_found": len(document["times"]),
        }
        for document in analyzed_documents
    ]


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def analyze_case(case):
    """Analyze any case (the demo case or a custom one) and return the full investigation report.

    `case` must look like:
        {"case_id": str, "title": str, "case_type": str, "documents": [...],
         "report_language": "en" | "ar" (optional, defaults to "en")}
    """
    language = case.get("report_language", "en")

    documents = case["documents"]
    for position, document in enumerate(documents, start=1):
        document["index"] = position

    analyzed_documents = [analyze_document(document) for document in documents]

    # Order of first appearance (document order, then within-document order) reads more
    # naturally in a report than an alphabetical shuffle - dates/emails stay sorted below
    # since chronological/alphabetical ordering suits them better.
    all_people = _prefer_full_names(
        _dedupe_preserve_order(person for doc in analyzed_documents for person in doc["people"])
    )
    all_organizations = _dedupe_preserve_order(org for doc in analyzed_documents for org in doc["organizations"])
    all_dates = sorted({date_text for doc in analyzed_documents for date_text in doc["dates"]})
    all_emails = sorted({email for doc in analyzed_documents for email in doc["emails"]})
    all_key_statements = [
        {"statement": statement, **_source_info(doc)}
        for doc in analyzed_documents
        for statement in doc["key_statements"]
    ]

    timeline, contextual_statements = build_timeline(analyzed_documents)
    contradictions = detect_contradictions(analyzed_documents, language)
    risk_level = determine_risk_level(contradictions)
    next_steps = recommend_next_steps(risk_level, language)
    follow_up_questions = generate_follow_up_questions(
        contradictions, analyzed_documents, case.get("case_type", ""), language
    )
    evidence_assessment = build_evidence_assessment(analyzed_documents)
    executive_summary = generate_executive_summary(case, analyzed_documents, contradictions, risk_level, language)

    return {
        "case_id": case["case_id"],
        "case_title": case["title"],
        "case_type": case.get("case_type", ""),
        "report_language": language,
        "executive_summary": executive_summary,
        "case_information": {
            "case_id": case["case_id"],
            "case_title": case["title"],
            "case_type": case.get("case_type", ""),
            "evidence_count": len(documents),
            "report_language": language,
        },
        "involved_parties": {
            "people": all_people,
            "organizations": all_organizations,
        },
        "verified_facts": {
            "dates": all_dates,
            "emails": all_emails,
            "key_statements": all_key_statements,
        },
        "contextual_statements": contextual_statements,
        "timeline": timeline,
        "contradictions": contradictions,
        "evidence_assessment": evidence_assessment,
        "risk_level": risk_level,
        "follow_up_questions": follow_up_questions,
        "recommended_next_steps": next_steps,
        "disclaimer": DISCLAIMER_TEXT[language],
    }


def run_investigation():
    """Analyze the built-in fictional demo case (always in English) and return the full report."""
    case = load_demo_case()
    case.setdefault("report_language", "en")
    return analyze_case(case)
