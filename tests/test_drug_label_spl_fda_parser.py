"""
Automated Pytest Test Suite for Drug Label Spl Fda Parser.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set a test audit secret key before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-for-pytest-only-32chars")

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_does_not_leak_pattern():
    """Verify PHI guard exception does not expose the matched pattern."""
    try:
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive")
        assert False, "Should have raised SecurityException"
    except SecurityException as e:
        error_msg = str(e)
        # Should not contain the regex pattern itself
        assert "MRN" not in error_msg or "pattern" not in error_msg.lower()
        assert "PHI Outbound Guard Violation" in error_msg


def test_phi_guard_redaction():
    """Verify PHI redaction replaces sensitive data."""
    text = "Patient John Doe has MRN-1234567 and phone 555-123-4567"
    redacted = PHIGuard.redact_phi(text)
    assert "John Doe" not in redacted
    assert "MRN-1234567" not in redacted
    assert "555-123-4567" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_nan_metric_rejected():
    """Verify NaN metric values are rejected by validation."""
    import math
    with pytest.raises(ValueError, match="finite"):
        SystemTaskPayload(
            task_id="T-NAN",
            target_identifier="KEY-NAN",
            primary_metric=math.nan
        )


def test_infinity_metric_rejected():
    """Verify Infinity metric values are rejected by validation."""
    import math
    with pytest.raises(ValueError, match="finite"):
        SystemTaskPayload(
            task_id="T-INF",
            target_identifier="KEY-INF",
            secondary_metric=math.inf
        )


def test_empty_task_id_rejected():
    """Verify empty task_id is rejected by validation."""
    with pytest.raises(ValueError, match="empty"):
        SystemTaskPayload(
            task_id="   ",
            target_identifier="KEY-01",
            primary_metric=10.0
        )


def test_audit_trail_requires_secret_key():
    """Verify AuditTrail raises error when no secret key is provided."""
    import os
    # Temporarily remove the env var
    original = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        from agents.base import AuditTrail
        with pytest.raises(SecurityException, match="AUDIT_SECRET_KEY"):
            AuditTrail()
    finally:
        # Restore the env var
        if original:
            os.environ["AUDIT_SECRET_KEY"] = original


def test_audit_trail_rejects_short_key():
    """Verify AuditTrail rejects short secret keys."""
    from agents.base import AuditTrail
    with pytest.raises(SecurityException, match="16 characters"):
        AuditTrail(secret_key="short")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0
