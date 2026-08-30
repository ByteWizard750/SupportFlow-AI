"""
Automated unit and integration tests for SupportFlow AI Phase 1.
Uses an isolated temporary SQLite database and cleans it up after execution.
"""

import os
import sys
import tempfile
import unittest

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import (
    init_db,
    create_ticket as db_create_ticket,
    get_all_tickets as db_get_all_tickets,
    get_ticket_by_id as db_get_ticket_by_id,
    get_ticket_metrics as db_get_ticket_metrics,
)
from services.ticket_service import (
    validate_ticket_input,
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    get_dashboard_summary,
)


class TestPhase1Foundation(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for isolated database testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = os.path.join(self.temp_dir.name, "test_supportflow.db")
        init_db(self.test_db_path)

    def tearDown(self):
        # Clean up temporary database directory
        self.temp_dir.cleanup()

    def test_database_initialization(self):
        """Test database table creation and empty retrieval."""
        tickets = db_get_all_tickets(self.test_db_path)
        self.assertEqual(len(tickets), 0)
        metrics = db_get_ticket_metrics(self.test_db_path)
        self.assertEqual(metrics["total"], 0)
        self.assertEqual(metrics["new"], 0)

    def test_ticket_validation(self):
        """Test input validation for tickets."""
        # Empty customer name
        valid, msg = validate_ticket_input("", "Valid Subject", "Valid description here")
        self.assertFalse(valid)
        self.assertIn("Customer Name", msg)

        # Empty subject
        valid, msg = validate_ticket_input("Alice", "  ", "Valid description here")
        self.assertFalse(valid)
        self.assertIn("Subject", msg)

        # Empty description
        valid, msg = validate_ticket_input("Alice", "Valid Subject", "")
        self.assertFalse(valid)
        self.assertIn("Description", msg)

        # Valid inputs
        valid, msg = validate_ticket_input("Alice Smith", "Billing issue with renewal", "Please help me resolve the double charge on my account.")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_ticket_creation_and_retrieval(self):
        """Test creating tickets, verifying default status 'New', and retrieving by ID."""
        success, ticket_id = create_ticket(
            customer_name="Alice Smith",
            subject="Invoice issue",
            description="I was billed twice for the annual subscription plan.",
            db_path=self.test_db_path
        )
        self.assertTrue(success)
        self.assertIsInstance(ticket_id, int)
        self.assertGreater(ticket_id, 0)

        # Fetch single ticket
        ticket = get_ticket_by_id(ticket_id, db_path=self.test_db_path)
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket["id"], ticket_id)
        self.assertEqual(ticket["customer_name"], "Alice Smith")
        self.assertEqual(ticket["subject"], "Invoice issue")
        self.assertEqual(ticket["description"], "I was billed twice for the annual subscription plan.")
        self.assertEqual(ticket["status"], "New")
        self.assertIsNotNone(ticket["created_at"])

    def test_multiple_tickets_and_dashboard_metrics(self):
        """Test creating multiple tickets and checking metric calculations."""
        # Create 3 tickets
        t1 = create_ticket("Alice", "Subject 1", "Description for ticket 1", db_path=self.test_db_path)
        t2 = create_ticket("Bob", "Subject 2", "Description for ticket 2", db_path=self.test_db_path)
        t3 = create_ticket("Charlie", "Subject 3", "Description for ticket 3", db_path=self.test_db_path)

        self.assertTrue(t1[0])
        self.assertTrue(t2[0])
        self.assertTrue(t3[0])

        # Get all tickets
        all_tickets = get_all_tickets(db_path=self.test_db_path)
        self.assertEqual(len(all_tickets), 3)

        # Verify ordering (newest first)
        self.assertEqual(all_tickets[0]["id"], 3)
        self.assertEqual(all_tickets[1]["id"], 2)
        self.assertEqual(all_tickets[2]["id"], 1)

        # Check dashboard summary
        summary = get_dashboard_summary(db_path=self.test_db_path)
        self.assertEqual(summary["total_tickets"], 3)
        self.assertEqual(summary["new_tickets"], 3)
        self.assertEqual(len(summary["recent_tickets"]), 3)

    def test_nonexistent_ticket(self):
        """Test retrieving a ticket ID that does not exist."""
        ticket = get_ticket_by_id(9999, db_path=self.test_db_path)
        self.assertIsNone(ticket)


if __name__ == "__main__":
    unittest.main(verbosity=2)
