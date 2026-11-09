"""Core Two-Phase Transaction Coordinator implementation."""
import time
from enum import Enum
from typing import Dict, List, Callable, Optional, Any


class TransactionStatus(str, Enum):
    INITIAL = "INITIAL"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ABORTING = "ABORTING"
    ABORTED = "ABORTED"


class TransactionParticipant:
    def __init__(
        self,
        participant_id: str,
        prepare_fn: Callable[[str, Dict[str, Any]], bool],
        commit_fn: Callable[[str, Dict[str, Any]], bool],
        rollback_fn: Callable[[str, Dict[str, Any]], bool]
    ):
        self.participant_id = participant_id
        self.prepare_fn = prepare_fn
        self.commit_fn = commit_fn
        self.rollback_fn = rollback_fn


class TwoPhaseCoordinator:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self.participants: Dict[str, TransactionParticipant] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}

    def register_participant(self, participant: TransactionParticipant):
        self.participants[participant.participant_id] = participant

    def execute_transaction(self, txn_id: str, payload: Dict[str, Any], participant_ids: List[str]) -> TransactionStatus:
        self.transactions[txn_id] = {
            "status": TransactionStatus.PREPARING,
            "participants": participant_ids,
            "prepared": [],
            "created_at": time.time()
        }

        # Phase 1: Prepare
        all_prepared = True
        prepared_list = []
        for pid in participant_ids:
            if pid not in self.participants:
                all_prepared = False
                break
            part = self.participants[pid]
            try:
                ok = part.prepare_fn(txn_id, payload)
                if ok:
                    prepared_list.append(pid)
                else:
                    all_prepared = False
                    break
            except Exception:
                all_prepared = False
                break

        self.transactions[txn_id]["prepared"] = prepared_list

        # Phase 2: Commit or Abort
        if all_prepared:
            self.transactions[txn_id]["status"] = TransactionStatus.COMMITTING
            for pid in participant_ids:
                try:
                    self.participants[pid].commit_fn(txn_id, payload)
                except Exception:
                    pass
            self.transactions[txn_id]["status"] = TransactionStatus.COMMITTED
            return TransactionStatus.COMMITTED
        else:
            self.transactions[txn_id]["status"] = TransactionStatus.ABORTING
            # Compensate all participants that had successfully prepared
            for pid in prepared_list:
                try:
                    self.participants[pid].rollback_fn(txn_id, payload)
                except Exception:
                    pass
            self.transactions[txn_id]["status"] = TransactionStatus.ABORTED
            return TransactionStatus.ABORTED

    def get_status(self, txn_id: str) -> Optional[TransactionStatus]:
        txn = self.transactions.get(txn_id)
        return txn["status"] if txn else None
