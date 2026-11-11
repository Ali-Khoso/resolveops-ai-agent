"""Static safety-contract checks for the Phase 5 SQL migration.

These complement but do not replace live Supabase integration tests.
"""
from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase/migrations/202611120001_phase5_approval_guardrails.sql"
)


def test_approval_database_guards_are_present():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "guard_phase5_approval_insert" in sql
    assert "before insert on public.approval_requests" in sql
    assert "new.owner_id is distinct from auth.uid()" in sql
    assert "linked_run.intent = 'refund'" in sql
    assert "linked_run.status <> 'pending_approval'" in sql


def test_atomic_decisions_are_idempotent_and_audited():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "for update" in sql
    assert "if a.status = p_decision then" in sql
    assert "raise sqlstate 'pt409'" in sql
    assert "rejection reason required" in sql
    assert "refund review requires written rationale" in sql
    assert "public.operation_audit_events" in sql
    assert "on conflict(approval_id) do nothing" in sql


def test_no_external_payment_or_email_actions_in_migration():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "public.ticket_messages" in sql
    assert "send_email(" not in sql
    assert "stripe." not in sql
