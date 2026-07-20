# tests/test_contradiction_detection.py
#
# Tests for the rule-based contradiction detector in
# services/investigation_engine.py (detect_contradictions and its helpers).
#
# Run with:  python -m unittest discover -s tests -v
# (or, from the project root:  python -m unittest tests.test_contradiction_detection -v)
#
# No external test framework is required - this uses the standard library's
# unittest module only, matching the project's "no extra dependencies" rule.

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.investigation_engine import analyze_case, build_case_from_custom_input, run_investigation


def _case_from(evidence_pairs, case_title="Test Case", case_type="Internal Audit"):
    """Build and analyze a case from a list of (type, content) tuples."""
    items = [
        {"title": f"Evidence {i}", "type": ev_type, "content": content}
        for i, (ev_type, content) in enumerate(evidence_pairs, start=1)
    ]
    case = build_case_from_custom_input(case_title, case_type, "en", items)
    return analyze_case(case)


class VendorAccessInvestigationCase(unittest.TestCase):
    """The exact reported bug: a denied warehouse entry vs. a visitor log entry."""

    def setUp(self):
        self.result = _case_from(
            [
                ("Employee Statement", "Ahmed stated that he never entered the warehouse on March 12, 2026."),
                ("Visitor Log", "Visitor log confirms Ahmed entered the warehouse at 1:52 PM on March 12, 2026."),
            ],
            case_title="Vendor Access Investigation",
            case_type="Internal Audit",
        )

    def test_contradiction_is_detected(self):
        self.assertEqual(len(self.result["contradictions"]), 1)

    def test_risk_level_is_high(self):
        self.assertEqual(self.result["risk_level"], "High")

    def test_contradiction_explains_both_sides(self):
        contradiction = self.result["contradictions"][0]
        self.assertIn("never entered", contradiction["claim"])
        self.assertIn("entered the warehouse", contradiction["conflicting_evidence"])
        self.assertEqual(contradiction["claim_source_title"], "Evidence 1")
        self.assertEqual(contradiction["conflicting_evidence_source_title"], "Evidence 2")
        self.assertIn("Evidence 1", contradiction["reasoning"])
        self.assertIn("Evidence 2", contradiction["reasoning"])

    def test_severity_is_high_because_confirming_doc_has_a_timestamp(self):
        self.assertEqual(self.result["contradictions"][0]["severity"], "High")


class DemoCaseRegression(unittest.TestCase):
    """The original built-in demo case must keep detecting its meeting-denial
    contradiction after generalizing the detector - this guards against a
    regression while broadening detection to new action concepts."""

    def test_demo_case_still_detects_two_contradictions_with_high_risk(self):
        result = run_investigation()
        self.assertEqual(len(result["contradictions"]), 2)
        self.assertEqual(result["risk_level"], "High")
        source_pairs = {
            (c["claim_source_title"], c["conflicting_evidence_source_title"])
            for c in result["contradictions"]
        }
        self.assertIn(("Employee Statement - J. Whitmore", "Email Thread - Meeting Confirmation"), source_pairs)
        self.assertIn(("Employee Statement - J. Whitmore", "Building Visitor Log"), source_pairs)


class PositiveContradictionExamples(unittest.TestCase):
    """Each pair from the requirements: a direct positive-vs-negative conflict
    about the same subject, action, and date should be detected."""

    def _assert_detected(self, negative_text, positive_text):
        result = _case_from([
            ("Employee Statement", negative_text),
            ("Email", positive_text),
        ])
        self.assertEqual(
            len(result["contradictions"]), 1,
            f"expected a contradiction between:\n  {negative_text!r}\n  {positive_text!r}",
        )

    def test_entered_vs_never_entered(self):
        self._assert_detected(
            "Ahmed stated that he never entered the warehouse on March 12, 2026.",
            "Visitor log confirms Ahmed entered the warehouse at 1:52 PM on March 12, 2026.",
        )

    def test_attended_vs_did_not_attend(self):
        self._assert_detected(
            "Sara did not attend the training session on May 4, 2026.",
            "The sign-in sheet shows Sara attended the training session on May 4, 2026.",
        )

    def test_approved_vs_rejected(self):
        self._assert_detected(
            "Lina rejected the purchase order on June 1, 2026.",
            "The system log shows Lina approved the purchase order on June 1, 2026.",
        )

    def test_approved_vs_did_not_approve(self):
        self._assert_detected(
            "Lina did not approve the purchase order on June 1, 2026.",
            "The system log shows Lina approved the purchase order on June 1, 2026.",
        )

    def test_paid_vs_did_not_pay(self):
        self._assert_detected(
            "Omar did not pay the invoice on July 9, 2026.",
            "The bank statement shows Omar paid the invoice on July 9, 2026.",
        )

    def test_received_vs_did_not_receive(self):
        self._assert_detected(
            "Fatima stated she did not receive the shipment on August 2, 2026.",
            "The courier confirmed Fatima received the shipment on August 2, 2026.",
        )

    def test_delivered_vs_was_not_delivered(self):
        self._assert_detected(
            "The vendor stated the package was not delivered on September 5, 2026.",
            "The tracking log shows the package was delivered on September 5, 2026.",
        )

    def test_present_vs_absent(self):
        self._assert_detected(
            "Youssef was absent from the meeting on October 10, 2026.",
            "The attendance record shows Youssef was present at the meeting on October 10, 2026.",
        )

    def test_authorized_vs_unauthorized(self):
        self._assert_detected(
            "Khalid was unauthorized to access the server room on November 3, 2026.",
            "The badge log shows Khalid authorized to access the server room on November 3, 2026.",
        )

    def test_authorized_vs_not_authorized(self):
        self._assert_detected(
            "Khalid was not authorized to access the server room on November 3, 2026.",
            "The badge log shows Khalid authorized to access the server room on November 3, 2026.",
        )

    def test_accessed_vs_did_not_access(self):
        self._assert_detected(
            "Nora did not access the database on December 1, 2026.",
            "The system log shows Nora accessed the database on December 1, 2026.",
        )


class NegationFormCoverage(unittest.TestCase):
    """Requirement 5: common negation forms must all be recognized."""

    def _assert_detected(self, negative_text, positive_text):
        result = _case_from([
            ("Employee Statement", negative_text),
            ("Email", positive_text),
        ])
        self.assertEqual(len(result["contradictions"]), 1, f"negation form not recognized in: {negative_text!r}")

    def test_didnt_contraction(self):
        self._assert_detected(
            "Ahmed didn't enter the warehouse on March 12, 2026.",
            "The visitor log shows Ahmed entered the warehouse on March 12, 2026.",
        )

    def test_wasnt_contraction(self):
        self._assert_detected(
            "The package wasn't delivered on September 5, 2026.",
            "The tracking log shows the package was delivered on September 5, 2026.",
        )

    def test_werent_contraction(self):
        self._assert_detected(
            "The goods weren't delivered on September 5, 2026.",
            "The tracking log shows the goods were delivered on September 5, 2026.",
        )

    def test_cant_contraction(self):
        self._assert_detected(
            "Nora can't access the database, the log confirms she never accessed it on December 1, 2026.",
            "The system log shows Nora accessed the database on December 1, 2026.",
        )

    def test_never_form(self):
        self._assert_detected(
            "Ahmed never entered the warehouse on March 12, 2026.",
            "The visitor log shows Ahmed entered the warehouse on March 12, 2026.",
        )


class NormalizationAndCaseInsensitivity(unittest.TestCase):
    """Requirement 4: matching must not depend on exact casing/punctuation."""

    def test_uppercase_and_stray_punctuation_still_detected(self):
        result = _case_from([
            ("Employee Statement", "AHMED NEVER ENTERED THE WAREHOUSE ON MARCH 12, 2026!!"),
            ("Visitor Log", "visitor log confirms ahmed entered the warehouse at 1:52 pm on march 12, 2026."),
        ])
        self.assertEqual(len(result["contradictions"]), 1)


class NegativeCasesNoContradiction(unittest.TestCase):
    """Requirement 10: obvious false positives must be avoided."""

    def test_same_subject_same_action_different_dates(self):
        result = _case_from([
            ("Employee Statement", "Ahmed entered the warehouse on March 12."),
            ("Visitor Log", "Ahmed entered the warehouse on March 13."),
        ])
        self.assertEqual(len(result["contradictions"]), 0)
        self.assertEqual(result["risk_level"], "Low")

    def test_different_subjects_same_action(self):
        result = _case_from([
            ("Employee Statement", "Ahmed entered the warehouse."),
            ("Visitor Log", "Khalid did not enter the warehouse."),
        ])
        self.assertEqual(len(result["contradictions"]), 0)
        self.assertEqual(result["risk_level"], "Low")

    def test_unrelated_statements(self):
        result = _case_from([
            ("Employee Statement", "The quarterly budget report was submitted on March 1, 2026."),
            ("Email", "The office holiday party is scheduled for December 20, 2026."),
        ])
        self.assertEqual(len(result["contradictions"]), 0)

    def test_two_positive_statements_about_same_event_no_contradiction(self):
        result = _case_from([
            ("Employee Statement", "Ahmed entered the warehouse on March 12, 2026."),
            ("Visitor Log", "The visitor log confirms Ahmed entered the warehouse on March 12, 2026."),
        ])
        self.assertEqual(len(result["contradictions"]), 0)

    def test_two_negative_statements_about_same_event_no_contradiction(self):
        result = _case_from([
            ("Employee Statement", "Ahmed never entered the warehouse on March 12, 2026."),
            ("Visitor Log", "The visitor log shows Ahmed did not enter the warehouse on March 12, 2026."),
        ])
        self.assertEqual(len(result["contradictions"]), 0)


if __name__ == "__main__":
    unittest.main()
