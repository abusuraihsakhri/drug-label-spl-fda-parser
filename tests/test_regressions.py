import json

from agents.base import AuditTrail
from spl_label_parser.cli import main as packaged_main
from cli import main as legacy_main


def test_hmac_detects_content_tampering():
    audit = AuditTrail(secret_key="local-test-secret-key-32-characters")
    audit.log("operator", "supervisor", "START", {"ok": True})
    audit.log("operator", "supervisor", "FINISH", {"ok": True})
    assert audit.verify_integrity()
    audit.logs[0]["event_type"] = "ALTERED"
    assert not audit.verify_integrity()


def test_hmac_detects_last_block_tampering():
    audit = AuditTrail(secret_key="local-test-secret-key-32-characters")
    audit.log("operator", "supervisor", "START", {"ok": True})
    audit.logs[0]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()


def test_history_is_defensive_copy():
    audit = AuditTrail(secret_key="local-test-secret-key-32-characters")
    audit.log("operator", "supervisor", "START", {"ok": True})
    audit.get_trail()[0]["actor"] = "changed"
    assert audit.verify_integrity()


def test_spl_cli_roundtrip(tmp_path, capsys):
    path = tmp_path / "label.xml"
    path.write_text(
        '<document xmlns="urn:hl7-org:v3"><title>Example</title></document>',
        encoding="utf-8"
    )
    assert packaged_main(["parse-spl", str(path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["title"] == "Example"
    output = tmp_path / "extracted.json"
    assert legacy_main(["parse-spl", str(path), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["title"] == "Example"


def test_spl_cli_rejects_invalid_xml(tmp_path, capsys):
    path = tmp_path / "label.xml"
    path.write_text("<bad/>", encoding="utf-8")
    assert packaged_main(["parse-spl", str(path)]) == 2
    assert "SPL parsing failed" in capsys.readouterr().err


def test_alternative_api_can_start():
    from spl_label_parser.server import create_app
    app = create_app()
    assert app is not None
    assert "/api/audit" in app.openapi()["paths"]
