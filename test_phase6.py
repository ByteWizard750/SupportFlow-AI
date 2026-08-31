"""
Automated Test Suite for Phase 6: SLA Monitoring & Intelligent Escalation.

Tests:
1. Correct SLA targets for all priorities (Critical=4h, High=12h, Medium=24h, Low=48h).
2. Deterministic 'On Track' SLA status (< 75% SLA elapsed).
3. Deterministic 'At Risk' SLA status (>= 75% and < 100% SLA elapsed).
4. Deterministic 'Breached' SLA status for unresolved overdue tickets (>= 100% SLA elapsed).
5. 'Met' SLA status for tickets resolved within SLA target.
6. 'Breached' / Missed SLA status for tickets resolved after SLA deadline.
7. SLA compliance rate calculation ((resolved_within_sla / total_resolved) * 100).
8. Empty database handling (zero division protection, clean defaults).
9. At-risk ticket retrieval and priority sorting.
10. Breached ticket retrieval and ordering by longest breach duration first.
11. Rule-based escalation recommendations across severity tiers.
"""

import os
import unittest
import tempfile
from datetime import datetime, timedelta, timezone

from database.database import (
    init_db,
    create_ticket,
    save_ticket_analysis,
    mark_ticket_resolved,
    get_ticket_sla_status,
    get_sla_summary,
    get_at_risk_tickets,
    get_sla_breached_tickets,
    get_escalation_queue_tickets,
    get_connection,
)
from services.sla_service import (
    get_sla_target_hours,
    calculate_sla_status,
    get_escalation_recommendation,
    format_sla_duration,
)


class TestPhase6SLAMonitoring(unittest.TestCase):
    """
    Unit tests for Phase 6 deterministic SLA calculations, breach detection,
    and escalation recommendations against an isolated temporary SQLite database.
    """

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def set_ticket_created_at(self, ticket_id: int, dt: datetime):
        """Helper to backdate ticket created_at timestamp in SQLite."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tickets SET created_at = ? WHERE id = ?;",
                (dt.strftime("%Y-%m-%d %H:%M:%S"), ticket_id)
            )

    def set_resolution_resolved_at(self, ticket_id: int, dt: datetime):
        """Helper to backdate ticket resolved_at timestamp in SQLite."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ticket_resolutions SET resolved_at = ? WHERE ticket_id = ?;",
                (dt.strftime("%Y-%m-%d %H:%M:%S"), ticket_id)
            )

    def test_1_sla_targets_by_priority(self):
        """
        Verify SLA targets: Critical=4h, High=12h, Medium=24h, Low=48h.
        """
        self.assertEqual(get_sla_target_hours("Critical"), 4.0)
        self.assertEqual(get_sla_target_hours("critical"), 4.0)
        self.assertEqual(get_sla_target_hours("High"), 12.0)
        self.assertEqual(get_sla_target_hours("Medium"), 24.0)
        self.assertEqual(get_sla_target_hours("Low"), 48.0)
        self.assertEqual(get_sla_target_hours(None), 24.0)
        self.assertEqual(get_sla_target_hours("Unknown"), 24.0)

    def test_2_on_track_status(self):
        """
        Verify that a ticket with < 75% elapsed SLA is 'On Track'.
        """
        now = datetime.now(timezone.utc)
        # Critical SLA is 4h. 1 hour ago is 25% (< 75%)
        created = now - timedelta(hours=1.0)
        res = calculate_sla_status(
            created_at=created,
            priority="Critical",
            current_status="New",
            current_time=now
        )
        self.assertEqual(res["sla_status"], "On Track")
        self.assertFalse(res["is_at_risk"])
        self.assertFalse(res["is_breached"])
        self.assertEqual(res["elapsed_hours"], 1.0)
        self.assertEqual(res["remaining_hours"], 3.0)

    def test_3_at_risk_status(self):
        """
        Verify that a ticket with >= 75% elapsed SLA and < 100% is 'At Risk'.
        """
        now = datetime.now(timezone.utc)
        # High SLA is 12h. 75% is 9.0h. 10 hours elapsed is 83.3% -> At Risk
        created = now - timedelta(hours=10.0)
        res = calculate_sla_status(
            created_at=created,
            priority="High",
            current_status="In Progress",
            current_time=now
        )
        self.assertEqual(res["sla_status"], "At Risk")
        self.assertTrue(res["is_at_risk"])
        self.assertFalse(res["is_breached"])
        self.assertEqual(res["elapsed_hours"], 10.0)
        self.assertEqual(res["remaining_hours"], 2.0)

    def test_4_breached_status_unresolved(self):
        """
        Verify that an unresolved ticket exceeding 100% SLA target is 'Breached'.
        """
        now = datetime.now(timezone.utc)
        # Critical SLA is 4h. 6 hours elapsed -> Breached
        created = now - timedelta(hours=6.0)
        res = calculate_sla_status(
            created_at=created,
            priority="Critical",
            current_status="AI Analyzed",
            current_time=now
        )
        self.assertEqual(res["sla_status"], "Breached")
        self.assertTrue(res["is_breached"])
        self.assertFalse(res["is_at_risk"])
        self.assertEqual(res["elapsed_hours"], 6.0)
        self.assertEqual(res["remaining_hours"], -2.0)

    def test_5_met_status_resolved(self):
        """
        Verify that a ticket resolved within its SLA target gets 'Met' status.
        """
        created = datetime(2026, 8, 30, 10, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2026, 8, 30, 12, 30, 0, tzinfo=timezone.utc)  # 2.5h elapsed
        # Critical SLA is 4.0h -> Met
        res = calculate_sla_status(
            created_at=created,
            priority="Critical",
            current_status="Resolved",
            resolved_at=resolved
        )
        self.assertEqual(res["sla_status"], "Met")
        self.assertFalse(res["is_breached"])
        self.assertEqual(res["elapsed_hours"], 2.5)

    def test_6_missed_status_resolved(self):
        """
        Verify that a ticket resolved after its SLA deadline gets 'Breached' status.
        """
        created = datetime(2026, 8, 30, 10, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2026, 8, 30, 16, 0, 0, tzinfo=timezone.utc)  # 6.0h elapsed
        # Critical SLA is 4.0h -> Breached
        res = calculate_sla_status(
            created_at=created,
            priority="Critical",
            current_status="Resolved",
            resolved_at=resolved
        )
        self.assertEqual(res["sla_status"], "Breached")
        self.assertTrue(res["is_breached"])

    def test_7_sla_compliance_rate_calculation(self):
        """
        Verify SLA compliance rate formula: (resolved_within_sla / total_resolved) * 100.
        """
        t1 = create_ticket("Customer 1", "Sub 1", "Desc 1", self.db_path)
        save_ticket_analysis(t1, "Billing", "High", "Neutral", "Billing Support", "Reason", self.db_path)
        mark_ticket_resolved(t1, "Resolved", self.db_path)
        # Resolved in 2h for High (12h) -> Met
        self.set_ticket_created_at(t1, datetime(2026, 8, 30, 10, 0, 0))
        self.set_resolution_resolved_at(t1, datetime(2026, 8, 30, 12, 0, 0))

        t2 = create_ticket("Customer 2", "Sub 2", "Desc 2", self.db_path)
        save_ticket_analysis(t2, "Technical", "Critical", "Frustrated", "Tech Support", "Reason", self.db_path)
        mark_ticket_resolved(t2, "Resolved", self.db_path)
        # Resolved in 8h for Critical (4h) -> Breached
        self.set_ticket_created_at(t2, datetime(2026, 8, 30, 10, 0, 0))
        self.set_resolution_resolved_at(t2, datetime(2026, 8, 30, 18, 0, 0))

        summary = get_sla_summary(self.db_path)
        self.assertEqual(summary["total_resolved_tickets"], 2)
        self.assertEqual(summary["resolved_within_sla"], 1)
        self.assertEqual(summary["resolved_after_sla"], 1)
        self.assertEqual(summary["sla_compliance_rate_pct"], 50.0)

    def test_8_empty_database_handling(self):
        """
        Verify zero division protection on an empty database.
        """
        summary = get_sla_summary(self.db_path)
        self.assertEqual(summary["total_tickets"], 0)
        self.assertEqual(summary["total_open_tickets"], 0)
        self.assertEqual(summary["total_resolved_tickets"], 0)
        self.assertEqual(summary["on_track_count"], 0)
        self.assertEqual(summary["at_risk_count"], 0)
        self.assertEqual(summary["breached_count"], 0)
        self.assertEqual(summary["sla_compliance_rate_pct"], 100.0)

        self.assertEqual(get_at_risk_tickets(10, self.db_path), [])
        self.assertEqual(get_sla_breached_tickets(10, self.db_path), [])
        self.assertEqual(get_escalation_queue_tickets(10, self.db_path), [])

    def test_9_at_risk_ticket_filtering_and_priority(self):
        """
        Verify that only open tickets with >= 75% SLA are returned by get_at_risk_tickets,
        sorted by priority severity.
        """
        now = datetime.now(timezone.utc)
        # t_low: Low (48h), 40h elapsed (83%) -> At Risk
        t_low = create_ticket("User A", "Low issue", "Desc", self.db_path)
        save_ticket_analysis(t_low, "General", "Low", "Neutral", "Support", "Reason", self.db_path)
        self.set_ticket_created_at(t_low, now - timedelta(hours=40.0))

        # t_high: High (12h), 10h elapsed (83%) -> At Risk
        t_high = create_ticket("User B", "High issue", "Desc", self.db_path)
        save_ticket_analysis(t_high, "Billing", "High", "Negative", "Billing", "Reason", self.db_path)
        self.set_ticket_created_at(t_high, now - timedelta(hours=10.0))

        at_risk = get_at_risk_tickets(10, self.db_path)
        self.assertEqual(len(at_risk), 2)
        # High priority should come before Low priority
        self.assertEqual(at_risk[0]["id"], t_high)
        self.assertEqual(at_risk[1]["id"], t_low)

    def test_10_breached_ticket_ordering(self):
        """
        Verify that get_sla_breached_tickets orders tickets by longest breach duration first.
        """
        now = datetime.now(timezone.utc)
        # t1: 6h overdue (Critical: 4h target, 10h elapsed -> -6h remaining)
        t1 = create_ticket("User 1", "Critical 1", "Desc", self.db_path)
        save_ticket_analysis(t1, "Bug", "Critical", "Frustrated", "Tech Support", "Reason", self.db_path)
        self.set_ticket_created_at(t1, now - timedelta(hours=10.0))

        # t2: 20h overdue (High: 12h target, 32h elapsed -> -20h remaining)
        t2 = create_ticket("User 2", "High 1", "Desc", self.db_path)
        save_ticket_analysis(t2, "Feature", "High", "Negative", "Tech Support", "Reason", self.db_path)
        self.set_ticket_created_at(t2, now - timedelta(hours=32.0))

        breached = get_sla_breached_tickets(10, self.db_path)
        self.assertEqual(len(breached), 2)
        # t2 is 20h overdue vs t1 6h overdue -> t2 must be first
        self.assertEqual(breached[0]["id"], t2)
        self.assertEqual(breached[1]["id"], t1)

    def test_11_escalation_recommendations(self):
        """
        Verify deterministic rule-based escalation recommendation strings.
        """
        rec_crit_breach = get_escalation_recommendation("Critical", "Breached", "Technical Support")
        self.assertIn("Immediate management escalation required", rec_crit_breach)

        rec_high_at_risk = get_escalation_recommendation("High", "At Risk", "Billing Support")
        self.assertIn("Prioritize agent assignment", rec_high_at_risk)

        rec_on_track = get_escalation_recommendation("Medium", "On Track", "General Support")
        self.assertIn("Operating within normal SLA parameters", rec_on_track)

    def test_12_format_sla_duration(self):
        """
        Verify duration formatting helper.
        """
        self.assertEqual(format_sla_duration(0.5), "30m")
        self.assertEqual(format_sla_duration(3.5), "3.5h")
        self.assertEqual(format_sla_duration(28.0), "1.2d (28h)")


if __name__ == "__main__":
    unittest.main()
