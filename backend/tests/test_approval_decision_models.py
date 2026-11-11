"""Decision-note validation for auditable human review."""
import pytest
from pydantic import ValidationError
from app.models.operations import ApprovalDecision


@pytest.mark.parametrize("note", [None, "", "  ", "\n  \t"])
def test_rejections_require_meaningful_reason(note):
    with pytest.raises(ValidationError):
        ApprovalDecision(decision="rejected", note=note)


def test_rejection_note_is_normalized():
    record = ApprovalDecision(decision="rejected", note="  Insufficient evidence  ")
    assert record.note == "Insufficient evidence"


def test_approval_can_include_optional_note():
    assert ApprovalDecision(decision="approved").note is None
    assert ApprovalDecision(decision="approved", note="  Reviewed  ").note == "Reviewed"


def test_reviewer_cannot_insert_extra_state():
    with pytest.raises(ValidationError):
        ApprovalDecision(decision="approved", actor_id="spoof")
