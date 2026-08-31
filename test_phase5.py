"""
Automated Test Suite for Phase 5: Human-in-the-Loop Support Agent Workflow.

Tests:
1. Agent response draft saving and non-destruction of AI suggested responses.
2. Agent response retrieval.
3. Updating a ticket to 'In Progress' status.
4. Marking a ticket 'Resolved' with agent's approved final response.
5. Resolved timestamp population in SQLite.
6. Permitted vs invalid status transitions (e.g. preventing Resolved -> New).
7. Resolved tickets appearing correctly in analytics and recent resolutions.
8. Lifecycle KPI and resolution rate calculations.
9. Empty database handling (zero counts, 0.0% resolution rate).
"""

import os
import unittest
import tempfile
from typing import Dict, Any

from database.database import (
    init_db,
    create_ticket,
    get_ticket_by_id,
    save_ticket_analysis,
    save_suggested_response,
    get_suggested_response,
    save_agent_response,
    get_agent_response,
    mark_ticket_resolved,
    get_recent_resolutions,
    get_analytics_kpis,
)
from services.agent_service import (
    save_agent_draft,
    mark_in_progress,
    resolve_ticket,
    validate_status_transition,
    get_agent_workspace_data,
)


class TestPhase5HumanInTheLoop(unittest.TestCase):
    """
    Unit tests for Phase 5 Human-in-the-Loop support workflows.
    Uses an isolated temporary SQLite database for every test.
    """

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_database_handling(self):
        """
        Verify that resolution queries and lifecycle KPIs handle an empty database gracefully.
        """
        kpis = get_analytics_kpis(self.db_path)
        self.assertEqual(kpis["total_tickets"], 0)
        self.assertEqual(kpis["open_tickets"], 0)
        self.assertEqual(kpis["in_progress_tickets"], 0)
        self.assertEqual(kpis["resolved_tickets"], 0)
        self.assertEqual(kpis["resolution_rate_pct"], 0.0)

        resolutions = get_recent_resolutions(5, self.db_path)
        self.assertEqual(resolutions, [])

    def test_agent_draft_saving_and_retrieval(self):
        """
        Test saving an agent draft and ensuring it does not overwrite the RAG suggested response.
        """
        t_id = create_ticket("Jane Doe", "Refund issue", "Need refund for duplicate charge", self.db_path)
        
        # Store AI suggested response
        save_suggested_response(
            ticket_id=t_id,
            suggested_response="AI says: We will refund you in 5 days.",
            retrieved_sources=["Refund Policy"],
            db_path=self.db_path
        )

        # Agent edits response and saves draft
        agent_edited = "Agent edited: Hello Jane, I have reviewed your account and initiated the refund of $49.00."
        ok, msg = save_agent_draft(t_id, agent_edited, db_path=self.db_path)
        self.assertTrue(ok, msg)

        # Verify AI suggested response is untouched
        ai_resp = get_suggested_response(t_id, db_path=self.db_path)
        self.assertEqual(ai_resp["suggested_response"], "AI says: We will refund you in 5 days.")

        # Verify agent response is saved in resolutions table
        agent_rec = get_agent_response(t_id, db_path=self.db_path)
        self.assertIsNotNone(agent_rec)
        self.assertEqual(agent_rec["agent_response"], agent_edited)
        self.assertEqual(agent_rec["status"], "Draft")
        self.assertIsNone(agent_rec["resolved_at"])

    def test_mark_in_progress(self):
        """
        Test moving a ticket to 'In Progress' status.
        """
        t_id = create_ticket("Mark", "Login trouble", "Cannot log in with password", self.db_path)
        
        # Simulate AI analysis first
        save_ticket_analysis(t_id, "Account and Login", "Medium", "Neutral", "Account Support", "Reason", self.db_path)
        ticket = get_ticket_by_id(t_id, self.db_path)
        self.assertEqual(ticket["status"], "AI Analyzed")

        # Move to In Progress
        ok, msg = mark_in_progress(t_id, agent_response="Investigating user credentials...", db_path=self.db_path)
        self.assertTrue(ok, msg)

        updated_ticket = get_ticket_by_id(t_id, self.db_path)
        self.assertEqual(updated_ticket["status"], "In Progress")

    def test_resolve_ticket_workflow_and_timestamp(self):
        """
        Test marking a ticket as Resolved and verifying resolution record and timestamp.
        """
        t_id = create_ticket("Sarah", "Crash report", "Application crashed on upload", self.db_path)
        save_ticket_analysis(t_id, "Technical Issue", "High", "Negative", "Technical Support", "Crash", self.db_path)

        final_msg = "Hello Sarah, our engineering team deployed a fix for the file upload issue. You can now upload normally."
        ok, msg = resolve_ticket(t_id, final_msg, db_path=self.db_path)
        self.assertTrue(ok, msg)

        # Check ticket status
        ticket = get_ticket_by_id(t_id, self.db_path)
        self.assertEqual(ticket["status"], "Resolved")

        # Check resolution table
        res_rec = get_agent_response(t_id, self.db_path)
        self.assertIsNotNone(res_rec)
        self.assertEqual(res_rec["status"], "Resolved")
        self.assertEqual(res_rec["agent_response"], final_msg)
        self.assertIsNotNone(res_rec["resolved_at"])

        # Check recent resolutions query
        recent_res = get_recent_resolutions(5, self.db_path)
        self.assertEqual(len(recent_res), 1)
        self.assertEqual(recent_res[0]["id"], t_id)
        self.assertEqual(recent_res[0]["category"], "Technical Issue")

    def test_status_transitions_validation(self):
        """
        Test permitted vs prohibited status transitions.
        """
        # Valid Transitions
        self.assertTrue(validate_status_transition("New", "AI Analyzed")[0])
        self.assertTrue(validate_status_transition("New", "In Progress")[0])
        self.assertTrue(validate_status_transition("New", "Resolved")[0])
        self.assertTrue(validate_status_transition("AI Analyzed", "In Progress")[0])
        self.assertTrue(validate_status_transition("AI Analyzed", "Resolved")[0])
        self.assertTrue(validate_status_transition("In Progress", "Resolved")[0])
        self.assertTrue(validate_status_transition("In Progress", "In Progress")[0])

        # Prohibited Transitions
        self.assertFalse(validate_status_transition("Resolved", "New")[0])
        self.assertFalse(validate_status_transition("Resolved", "AI Analyzed")[0])
        self.assertFalse(validate_status_transition("New", "InvalidStatus")[0])

    def test_lifecycle_kpis_and_resolution_rate(self):
        """
        Test lifecycle KPI calculation across multiple tickets in different statuses.
        """
        t1 = create_ticket("U1", "T1", "Desc1", self.db_path)
        t2 = create_ticket("U2", "T2", "Desc2", self.db_path)
        t3 = create_ticket("U3", "T3", "Desc3", self.db_path)
        t4 = create_ticket("U4", "T4", "Desc4", self.db_path)

        # t1 stays 'New'
        # t2 becomes 'AI Analyzed'
        save_ticket_analysis(t2, "Billing and Payments", "Low", "Neutral", "Billing Support", "Reason", self.db_path)

        # t3 becomes 'In Progress'
        save_ticket_analysis(t3, "Technical Issue", "High", "Negative", "Technical Support", "Reason", self.db_path)
        mark_in_progress(t3, db_path=self.db_path)

        # t4 becomes 'Resolved'
        save_ticket_analysis(t4, "Account and Login", "Medium", "Neutral", "Account Support", "Reason", self.db_path)
        resolve_ticket(t4, "Resolved customer issue.", db_path=self.db_path)

        kpis = get_analytics_kpis(self.db_path)
        self.assertEqual(kpis["total_tickets"], 4)
        self.assertEqual(kpis["new_tickets"], 1)  # t1
        self.assertEqual(kpis["analyzed_tickets"], 1)  # t2
        self.assertEqual(kpis["in_progress_tickets"], 1)  # t3
        self.assertEqual(kpis["resolved_tickets"], 1)  # t4
        self.assertEqual(kpis["open_tickets"], 3)  # t1, t2, t3
        self.assertEqual(kpis["resolution_rate_pct"], 25.0)  # 1/4 = 25%

    def test_agent_workspace_data_assembly(self):
        """
        Test that get_agent_workspace_data correctly combines AI suggestion and agent draft.
        """
        t_id = create_ticket("Alex", "Plan upgrade", "How do I upgrade to Pro?", self.db_path)
        save_suggested_response(t_id, "AI: Upgrade in billing settings.", ["Subscription Policy"], self.db_path)

        # Before agent draft, initial_text is the AI response
        ws1 = get_agent_workspace_data(t_id, self.db_path)
        self.assertEqual(ws1["initial_text"], "AI: Upgrade in billing settings.")
        self.assertFalse(ws1["is_resolved"])

        # After agent saves draft, initial_text is the agent draft
        save_agent_draft(t_id, "Agent: You can upgrade via your dashboard under Billing.", self.db_path)
        ws2 = get_agent_workspace_data(t_id, self.db_path)
        self.assertEqual(ws2["initial_text"], "Agent: You can upgrade via your dashboard under Billing.")


if __name__ == "__main__":
    unittest.main()
