"""
Automated unit tests for SupportFlow AI Phase 2 (AI Ticket Analysis).

Tests:
1. SQLite database operations for ticket analyses in an isolated temporary database.
2. Ticket status transition from 'New' to 'AI Analyzed'.
3. Pydantic schema validation for all allowed enums.
4. (Optional) Single controlled live Gemini API call when RUN_LIVE_GEMINI=1.
"""

import os
import sys
import tempfile
import unittest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import (
    init_db,
    create_ticket,
    get_ticket_by_id,
    save_ticket_analysis,
    get_ticket_analysis,
    get_ticket_metrics,
)
from services.ai_service import (
    TicketAnalysisSchema,
    TicketCategory,
    TicketPriority,
    TicketSentiment,
    RecommendedDepartment,
    analyze_ticket,
)
from config import is_gemini_configured


class TestPhase2Analysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = os.path.join(self.temp_dir.name, "test_p2.db")
        init_db(self.test_db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_analysis_persistence(self):
        """Test storing and retrieving AI analysis and verify ticket status update."""
        # 1. Create a ticket
        ticket_id = create_ticket(
            customer_name="John Smith",
            subject="Billing question",
            description="Why did my invoice charge $50 instead of $30?",
            db_path=self.test_db_path
        )
        t_initial = get_ticket_by_id(ticket_id, db_path=self.test_db_path)
        self.assertEqual(t_initial["status"], "New")

        # 2. Save analysis
        analysis_id = save_ticket_analysis(
            ticket_id=ticket_id,
            category="Billing and Payments",
            priority="Medium",
            sentiment="Neutral",
            department="Billing Support",
            reasoning="Customer is inquiring about a price discrepancy on their monthly billing invoice.",
            db_path=self.test_db_path
        )
        self.assertGreater(analysis_id, 0)

        # 3. Retrieve analysis
        analysis = get_ticket_analysis(ticket_id, db_path=self.test_db_path)
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis["category"], "Billing and Payments")
        self.assertEqual(analysis["priority"], "Medium")
        self.assertEqual(analysis["sentiment"], "Neutral")
        self.assertEqual(analysis["department"], "Billing Support")
        self.assertIn("discrepancy", analysis["reasoning"])

        # 4. Verify ticket status transitioned to 'AI Analyzed'
        t_updated = get_ticket_by_id(ticket_id, db_path=self.test_db_path)
        self.assertEqual(t_updated["status"], "AI Analyzed")

    def test_analysis_update_idempotency(self):
        """Test that re-analyzing a ticket updates the existing record rather than creating duplicates."""
        ticket_id = create_ticket(
            customer_name="Alice",
            subject="Bug report",
            description="App crashed on save",
            db_path=self.test_db_path
        )
        save_ticket_analysis(
            ticket_id=ticket_id,
            category="Technical Issue",
            priority="High",
            sentiment="Frustrated",
            department="Technical Support",
            reasoning="Initial analysis",
            db_path=self.test_db_path
        )
        
        # Second analysis (refresh)
        save_ticket_analysis(
            ticket_id=ticket_id,
            category="Technical Issue",
            priority="Critical",
            sentiment="Frustrated",
            department="Technical Support",
            reasoning="Updated analysis due to crash severity",
            db_path=self.test_db_path
        )

        analysis = get_ticket_analysis(ticket_id, db_path=self.test_db_path)
        self.assertEqual(analysis["priority"], "Critical")
        self.assertEqual(analysis["reasoning"], "Updated analysis due to crash severity")

    def test_pydantic_schema_validation(self):
        """Test that TicketAnalysisSchema enforces valid categories, priorities, and sentiments."""
        valid_payload = {
            "category": "Refund",
            "priority": "High",
            "sentiment": "Frustrated",
            "department": "Billing Support",
            "reasoning": "Customer demands a full refund for duplicate charge."
        }
        obj = TicketAnalysisSchema.model_validate(valid_payload)
        self.assertEqual(obj.category, TicketCategory.REFUND)
        self.assertEqual(obj.priority, TicketPriority.HIGH)
        self.assertEqual(obj.sentiment, TicketSentiment.FRUSTRATED)
        self.assertEqual(obj.department, RecommendedDepartment.BILLING)

        # Invalid category should raise ValidationError
        invalid_payload = valid_payload.copy()
        invalid_payload["category"] = "Invalid Nonexistent Category"
        with self.assertRaises(ValidationError):
            TicketAnalysisSchema.model_validate(invalid_payload)

        # Invalid priority should raise ValidationError
        invalid_priority = valid_payload.copy()
        invalid_priority["priority"] = "SuperUrgent"
        with self.assertRaises(ValidationError):
            TicketAnalysisSchema.model_validate(invalid_priority)


class TestLiveGeminiAPI(unittest.TestCase):
    """
    Optional live integration test.
    Only executed when RUN_LIVE_GEMINI=1 is explicitly set in environment.
    """

    @unittest.skipUnless(
        os.getenv("RUN_LIVE_GEMINI") == "1",
        "Skipping live Gemini test by default. Set RUN_LIVE_GEMINI=1 to run."
    )
    def test_live_gemini_analysis(self):
        self.assertTrue(is_gemini_configured(), "Gemini API key is not configured in .env")
        
        success, result = analyze_ticket(
            subject="Cannot log in to my account",
            description="I keep getting error 403 invalid credentials even after resetting password."
        )
        self.assertTrue(success, f"Live Gemini API call failed: {result}")
        self.assertIsInstance(result, dict)
        self.assertIn("category", result)
        self.assertIn("priority", result)
        self.assertIn("sentiment", result)
        self.assertIn("department", result)
        self.assertIn("reasoning", result)
        self.assertGreater(len(result["reasoning"]), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
