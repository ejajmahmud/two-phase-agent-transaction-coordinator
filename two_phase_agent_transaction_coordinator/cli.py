"""CLI for two-phase-agent-transaction-coordinator."""
import sys
import argparse
from .coordinator import TwoPhaseCoordinator, TransactionParticipant, TransactionStatus


def main():
    parser = argparse.ArgumentParser(description="Two-Phase Agent Transaction Coordinator CLI")
    parser.add_argument("--demo", action="store_true", help="Run 2PC distributed transaction simulation")
    args = parser.parse_args()

    if args.demo:
        coord = TwoPhaseCoordinator()
        state = {"db": 100, "fs": "ready"}

        p1 = TransactionParticipant(
            "database_agent",
            prepare_fn=lambda tid, p: True,
            commit_fn=lambda tid, p: True,
            rollback_fn=lambda tid, p: True
        )
        p2 = TransactionParticipant(
            "filesystem_agent",
            prepare_fn=lambda tid, p: True,
            commit_fn=lambda tid, p: True,
            rollback_fn=lambda tid, p: True
        )
        coord.register_participant(p1)
        coord.register_participant(p2)

        status = coord.execute_transaction("tx_demo_01", {"action": "write"}, ["database_agent", "filesystem_agent"])
        print(f"Transaction Result: {status.value}")
    else:
        parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
