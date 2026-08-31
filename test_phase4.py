"""
Automated Test Suite for Phase 4: AI Analytics & Support Intelligence Dashboard.

Tests:
1. Empty database analytics handling (zero counts, 0.0% coverage, empty lists, no divide-by-zero).
2. KPI metrics calculation and accuracy.
3. Category, Department, Priority, and Sentiment distribution aggregations.
4. Urgent ticket filtering (High / Critical priority).
5. Daily ticket volume aggregation.
6. Analytics service DataFrame preparation and data integrity.
7. Optional live Gemini executive brief generation (when RUN_LIVE_GEMINI=1).
"""

import os
import unittest
import tempfile
import sqlite3
from typing import Dict, Any

from database.database import (
    init_db,
    create_ticket,
    save_ticket_analysis,
    save_suggested_response,
    get_analytics_kpis,
    get_category_distribution,
    get_department_distribution,
    get_priority_distribution,
    get_sentiment_distribution,
    get_daily_ticket_volume,
    get_urgent_tickets,
    get_recent_activity,
)
from services.analytics_service import (
    get_dashboard_analytics,
    generate_executive_brief,
    ExecutiveBriefSchema,
)


class TestPhase4Analytics(unittest.TestCase):
    """
    Unit tests for SQL analytics aggregations and service functions.
    Uses isolated temporary SQLite databases.
    """

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_database_analytics(self):
        """
        Verify that an empty database returns zero counts and 0.0% coverage without crashing.
        """
        kpis = get_analytics_kpis(self.db_path)
        self.assertEqual(kpis["total_tickets"], 0)
        self.assertEqual(kpis["new_tickets"], 0)
        self.assertEqual(kpis["analyzed_tickets"], 0)
        self.assertEqual(kpis["urgent_tickets"], 0)
        self.assertEqual(kpis["rag_responses"], 0)
        self.assertEqual(kpis["triage_coverage_pct"], 0.0)
        self.assertEqual(kpis["rag_coverage_pct"], 0.0)

        # Empty distributions
        self.assertEqual(get_category_distribution(self.db_path), [])
        self.assertEqual(get_department_distribution(self.db_path), [])
        self.assertEqual(get_priority_distribution(self.db_path), [])
        self.assertEqual(get_sentiment_distribution(self.db_path), [])
        self.assertEqual(get_daily_ticket_volume(self.db_path), [])
        self.assertEqual(get_urgent_tickets(5, self.db_path), [])
        self.assertEqual(get_recent_activity(5, self.db_path), [])

        # Analytics service empty payload
        data = get_dashboard_analytics(self.db_path)
        self.assertFalse(data["has_data"])
        self.assertFalse(data["has_analysis"])
        self.assertTrue(data["df_categories"].empty)
        self.assertTrue(data["df_departments"].empty)
        self.assertTrue(data["df_priorities"].empty)
        self.assertTrue(data["df_sentiments"].empty)

    def test_kpi_and_distribution_aggregation(self):
        """
        Seed database with known tickets and analyses, verifying exact aggregation results.
        """
        # Create 4 tickets
        t1 = create_ticket("Alice", "Double charge", "I was charged twice.", self.db_path)
        t2 = create_ticket("Bob", "Crash on PDF", "App crashes when uploading PDF.", self.db_path)
        t3 = create_ticket("Charlie", "Reset password", "Cannot reset password.", self.db_path)
        t4 = create_ticket("Diana", "General question", "How to upgrade subscription?", self.db_path)

        # Save AI analysis for t1, t2, t3 (t4 stays 'New')
        save_ticket_analysis(
            ticket_id=t1,
            category="Billing and Payments",
            priority="Medium",
            sentiment="Negative",
            department="Billing Support",
            reasoning="Billing issue with duplicate charges.",
            db_path=self.db_path
        )
        save_ticket_analysis(
            ticket_id=t2,
            category="Technical Issue",
            priority="Critical",
            sentiment="Frustrated",
            department="Technical Support",
            reasoning="Core feature crash.",
            db_path=self.db_path
        )
        save_ticket_analysis(
            ticket_id=t3,
            category="Account and Login",
            priority="High",
            sentiment="Neutral",
            department="Account Support",
            reasoning="User locked out.",
            db_path=self.db_path
        )

        # Save 1 RAG response for t1
        save_suggested_response(
            ticket_id=t1,
            suggested_response="We have refunded the duplicate charge.",
            retrieved_sources=["Refund Policy"],
            db_path=self.db_path
        )

        # Verify KPIs
        kpis = get_analytics_kpis(self.db_path)
        self.assertEqual(kpis["total_tickets"], 4)
        self.assertEqual(kpis["new_tickets"], 1)  # t4
        self.assertEqual(kpis["analyzed_tickets"], 3)  # t1, t2, t3
        self.assertEqual(kpis["urgent_tickets"], 2)  # t2 (Critical), t3 (High)
        self.assertEqual(kpis["rag_responses"], 1)  # t1
        self.assertEqual(kpis["triage_coverage_pct"], 75.0)  # 3/4 = 75%
        self.assertEqual(kpis["rag_coverage_pct"], 25.0)  # 1/4 = 25%

        # Verify Category Distribution
        cats = get_category_distribution(self.db_path)
        cat_map = {c["category"]: c["count"] for c in cats}
        self.assertEqual(cat_map.get("Billing and Payments"), 1)
        self.assertEqual(cat_map.get("Technical Issue"), 1)
        self.assertEqual(cat_map.get("Account and Login"), 1)

        # Verify Department Distribution
        depts = get_department_distribution(self.db_path)
        dept_map = {d["department"]: d["count"] for d in depts}
        self.assertEqual(dept_map.get("Billing Support"), 1)
        self.assertEqual(dept_map.get("Technical Support"), 1)
        self.assertEqual(dept_map.get("Account Support"), 1)

        # Verify Priority Distribution
        prios = get_priority_distribution(self.db_path)
        prio_map = {p["priority"]: p["count"] for p in prios}
        self.assertEqual(prio_map.get("Critical"), 1)
        self.assertEqual(prio_map.get("High"), 1)
        self.assertEqual(prio_map.get("Medium"), 1)

        # Verify Sentiment Distribution
        sents = get_sentiment_distribution(self.db_path)
        sent_map = {s["sentiment"]: s["count"] for s in sents}
        self.assertEqual(sent_map.get("Frustrated"), 1)
        self.assertEqual(sent_map.get("Negative"), 1)
        self.assertEqual(sent_map.get("Neutral"), 1)

    def test_urgent_ticket_filtering(self):
        """
        Verify that get_urgent_tickets only returns High and Critical priority tickets.
        """
        t1 = create_ticket("User1", "Low item", "Just asking", self.db_path)
        t2 = create_ticket("User2", "Urgent item", "Broken feature", self.db_path)
        t3 = create_ticket("User3", "Critical outage", "Server down", self.db_path)

        save_ticket_analysis(t1, "General Inquiry", "Low", "Neutral", "Customer Service", "Info", self.db_path)
        save_ticket_analysis(t2, "Technical Issue", "High", "Negative", "Technical Support", "Impact", self.db_path)
        save_ticket_analysis(t3, "Technical Issue", "Critical", "Frustrated", "Technical Support", "Outage", self.db_path)

        urgent = get_urgent_tickets(limit=5, db_path=self.db_path)
        self.assertEqual(len(urgent), 2)
        urgent_ids = [u["id"] for u in urgent]
        self.assertIn(t2, urgent_ids)
        self.assertIn(t3, urgent_ids)
        self.assertNotIn(t1, urgent_ids)

    def test_daily_ticket_volume(self):
        """
        Verify that daily ticket volume query properly groups tickets by creation date.
        """
        create_ticket("U1", "T1", "D1", self.db_path)
        create_ticket("U2", "T2", "D2", self.db_path)

        daily = get_daily_ticket_volume(self.db_path)
        self.assertGreaterEqual(len(daily), 1)
        self.assertEqual(daily[0]["count"], 2)


class TestLiveExecutiveBrief(unittest.TestCase):
    """
    Live test against Google Gemini API for executive brief generation.
    Only executed when RUN_LIVE_GEMINI=1 is defined.
    """

    @unittest.skipUnless(os.environ.get("RUN_LIVE_GEMINI") == "1", "Skipping live Gemini test by default. Set RUN_LIVE_GEMINI=1 to run.")
    def test_live_executive_brief_generation(self):
        kpis = {
            "total_tickets": 3,
            "new_tickets": 0,
            "analyzed_tickets": 3,
            "urgent_tickets": 2,
            "rag_coverage_pct": 66.7,
        }
        recent_tickets = [
            {"id": 1, "subject": "Double charged on monthly plan", "status": "AI Analyzed", "category": "Billing and Payments"},
            {"id": 2, "subject": "App crashes on file upload", "status": "AI Analyzed", "category": "Technical Issue"},
            {"id": 3, "subject": "Cannot log in after reset", "status": "AI Analyzed", "category": "Account and Login"},
        ]
        categories = [
            {"category": "Technical Issue", "count": 1},
            {"category": "Billing and Payments", "count": 1},
            {"category": "Account and Login", "count": 1},
        ]
        urgent_tickets = [
            {"id": 2, "subject": "App crashes on file upload", "category": "Technical Issue", "priority": "Critical"},
            {"id": 3, "subject": "Cannot log in after reset", "category": "Account and Login", "priority": "High"},
        ]

        ok, brief = generate_executive_brief(kpis, recent_tickets, categories, urgent_tickets)
        self.assertTrue(ok, f"Executive brief generation failed: {brief}")
        self.assertIsInstance(brief, dict)
        self.assertIn("key_pain_point", brief)
        self.assertIn("highest_workload_risk", brief)
        self.assertIn("recommended_action", brief)
        self.assertTrue(len(brief["key_pain_point"]) > 10)
        self.assertTrue(len(brief["highest_workload_risk"]) > 10)
        self.assertTrue(len(brief["recommended_action"]) > 10)


if __name__ == "__main__":
    unittest.main()
