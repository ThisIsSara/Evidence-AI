# tests/test_entity_extraction.py
#
# Tests for the rule-based people/organization/date/time/email extraction in
# services/investigation_engine.py (extract_people, extract_organizations,
# and the report-level "Involved Parties" aggregation).
#
# Run with:  python -m unittest discover -s tests -v

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.investigation_engine import (
    analyze_case,
    build_case_from_custom_input,
    extract_dates,
    extract_emails,
    extract_organizations,
    extract_people,
    extract_times,
    run_investigation,
)


def _involved_parties(text):
    """Run one piece of evidence text through the full report pipeline and return
    the "Involved Parties" section, exactly as the report displays it."""
    items = [{"title": "Evidence 1", "type": "Employee Statement", "content": text}]
    case = build_case_from_custom_input("Entity Test", "Internal Audit", "en", items)
    return analyze_case(case)["involved_parties"]


class RequiredVerificationCases(unittest.TestCase):
    """The three exact cases from the requirements."""

    def test_case_1_people_and_org(self):
        parties = _involved_parties("Ahmed met Sara at Halcyon Supply Co. on March 12, 2026.")
        self.assertEqual(parties["people"], ["Ahmed", "Sara"])
        self.assertEqual(parties["organizations"], ["Halcyon Supply Co."])

    def test_case_2_full_name_and_known_org(self):
        parties = _involved_parties("Jordan Whitmore emailed Microsoft regarding the contract.")
        self.assertEqual(parties["people"], ["Jordan Whitmore"])
        self.assertEqual(parties["organizations"], ["Microsoft"])

    def test_case_3_no_entities(self):
        parties = _involved_parties("No names or organizations.")
        self.assertEqual(parties["people"], [])
        self.assertEqual(parties["organizations"], [])


class SingleWordPeopleNames(unittest.TestCase):
    """Requirement 1: single first names must be recognized, not just "First Last"."""

    def test_each_required_example_name(self):
        for name in ["Ahmed", "Sara", "Khalid", "Fatima", "Omar", "Lina"]:
            with self.subTest(name=name):
                people = extract_people(f"{name} confirmed the delivery on April 1, 2026.")
                self.assertIn(name, people)

    def test_two_word_name_still_recognized(self):
        self.assertEqual(extract_people("Jordan Whitmore signed the form."), ["Jordan Whitmore"])


class OrganizationExamples(unittest.TestCase):
    """Requirement 2: both suffix-based and well-known bare organization names."""

    def test_suffix_based_organizations(self):
        self.assertIn("Halcyon Supply Co.", extract_organizations("The invoice came from Halcyon Supply Co. last week."))
        self.assertIn("ABC Logistics", extract_organizations("ABC Logistics delivered the package on May 2, 2026."))
        self.assertIn(
            "Riyadh Metro Authority",
            extract_organizations("The Riyadh Metro Authority approved the new route."),
        )

    def test_known_bare_organization_names(self):
        self.assertIn("OpenAI", extract_organizations("The report was drafted with input from OpenAI."))
        self.assertIn("Microsoft", extract_organizations("Microsoft confirmed the license renewal."))


class DatesTimesEmailsStillWork(unittest.TestCase):
    """Requirement 3: extraction of dates/times/emails must keep working unchanged."""

    def test_dates_times_emails(self):
        text = "Meeting on March 12, 2026 at 2:00 PM. Contact j.whitmore@fictionalcorp-demo.com for details."
        self.assertEqual(extract_dates(text), ["March 12, 2026"])
        self.assertEqual(extract_times(text), ["2:00 PM"])
        self.assertEqual(extract_emails(text), ["j.whitmore@fictionalcorp-demo.com"])


class DuplicatesAndOrdering(unittest.TestCase):
    """Requirements 4 and 5: no duplicates, and results follow first-appearance order."""

    def test_repeated_name_is_not_duplicated(self):
        people = extract_people("Ahmed entered the room. Later, Ahmed left the room.")
        self.assertEqual(people, ["Ahmed"])

    def test_order_matches_first_appearance_not_alphabetical(self):
        # "Sara" appears before "Ahmed" in the text - alphabetical order would flip this.
        people = extract_people("Sara called Ahmed to confirm the delivery.")
        self.assertEqual(people, ["Sara", "Ahmed"])

    def test_bare_first_name_merges_into_fuller_name_across_documents(self):
        # The same person is named in full in one document and by first name only in
        # another - the report should show one person, not two.
        items = [
            {"title": "Statement", "type": "Employee Statement", "content": "I, Jordan Whitmore, was on site."},
            {"title": "Email", "type": "Email", "content": "Hi Jordan, thanks for confirming."},
        ]
        case = build_case_from_custom_input("Merge Test", "Internal Audit", "en", items)
        people = analyze_case(case)["involved_parties"]["people"]
        self.assertEqual(people, ["Jordan Whitmore"])


class IgnoresCommonNonNameWords(unittest.TestCase):
    """Requirement 6: common sentence-start / structural words must not be treated as names."""

    def test_sentence_start_words_ignored(self):
        people = extract_people("The vendor arrived. This was expected. No issues were found.")
        self.assertEqual(people, [])

    def test_month_name_not_treated_as_a_person(self):
        self.assertNotIn("March", extract_people("The delivery occurred on March 12, 2026."))

    def test_labeled_line_values_dont_leak_as_names(self):
        # "Subject:" and "To:" lines are structured fields, not narrative sentences -
        # their capitalized first words ("Confirming", "To") aren't people.
        text = "To: j.whitmore@fictionalcorp-demo.com\nSubject: Confirming today's meeting\n\nSee you then."
        people = extract_people(text)
        self.assertNotIn("To", people)
        self.assertNotIn("Confirming", people)


class DemoCaseRegression(unittest.TestCase):
    """The built-in demo case must show its real people/organizations, and contradiction
    detection must be unaffected by the entity-extraction changes."""

    def test_demo_case_entities_and_contradictions(self):
        result = run_investigation()
        self.assertEqual(result["involved_parties"]["people"], ["Jordan Whitmore", "Renee Delgado"])
        self.assertEqual(result["involved_parties"]["organizations"], ["Halcyon Supply Co."])
        self.assertEqual(len(result["contradictions"]), 2)
        self.assertEqual(result["risk_level"], "High")


if __name__ == "__main__":
    unittest.main()
