"""Unit tests for two-phase-agent-transaction-coordinator."""
import unittest
from two_phase_agent_transaction_coordinator.coordinator import TwoPhaseCoordinator, TransactionParticipant, TransactionStatus


class TestTwoPhaseCoordinator(unittest.TestCase):
    def setUp(self):
        self.coord = TwoPhaseCoordinator()
        self.state = {"p1_committed": False, "p2_committed": False, "p1_rolled_back": False}

        p1 = TransactionParticipant(
            "p1",
            prepare_fn=lambda tid, p: True,
            commit_fn=lambda tid, p: self.state.__setitem__("p1_committed", True),
            rollback_fn=lambda tid, p: self.state.__setitem__("p1_rolled_back", True)
        )
        self.coord.register_participant(p1)

    def test_successful_commit(self):
        p2 = TransactionParticipant("p2", lambda tid, p: True, lambda tid, p: None, lambda tid, p: None)
        self.coord.register_participant(p2)
        status = self.coord.execute_transaction("tx_1", {}, ["p1", "p2"])
        self.assertEqual(status, TransactionStatus.COMMITTED)
        self.assertTrue(self.state["p1_committed"])

    def test_rollback_on_failure(self):
        p_fail = TransactionParticipant("p_fail", lambda tid, p: False, lambda tid, p: None, lambda tid, p: None)
        self.coord.register_participant(p_fail)
        status = self.coord.execute_transaction("tx_2", {}, ["p1", "p_fail"])
        self.assertEqual(status, TransactionStatus.ABORTED)
        self.assertTrue(self.state["p1_rolled_back"])
