"""
Command Line Interface for Drug Label Spl Fda Parser.
"""
import argparse
import csv
import json
import sys
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="drug-label-spl-fda-parser", description="Drug Label Spl Fda Parser")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Parse SPL XML
    p_spl = subparsers.add_parser("parse-spl", help="Extract FDA SPL XML sections as JSON")
    p_spl.add_argument("input", help="Path to UTF-8 SPL XML")
    p_spl.add_argument("-o", "--output", help="JSON output path (default: stdout)")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  DRUG LABEL SPL FDA PARSER")
        print(f"  Domain: Clinical & Biomedical AI | Standard: CAP / CLSI / ISO Standards")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Drug Label Spl Fda Parser Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        out_rows = []
        errors = []
        for idx, r in enumerate(rows):
            try:
                payload = SystemTaskPayload(
                    task_id=r.get("task_id", f"TASK-{idx+1:03d}"),
                    target_identifier=r.get("target_identifier", f"TARGET-{idx+1:03d}"),
                    primary_metric=float(r.get("primary_metric", 15.0)),
                    secondary_metric=float(r.get("secondary_metric", 5.0)),
                    status_descriptor=r.get("status_descriptor", "NOMINAL"),
                    is_critical_flag=str(r.get("is_critical_flag", "")).lower() in ("true", "1", "yes"),
                )
                dossier = supervisor.process_task(payload)
                row_dict = dict(r)
                row_dict["overall_urgency"] = dossier.overall_urgency.value
                row_dict["integrity_status"] = dossier.integrity_status.value
                row_dict["total_alerts"] = dossier.total_alerts
                row_dict["audit_hash"] = dossier.audit_hash
                out_rows.append(row_dict)
            except (ValueError, TypeError) as e:
                errors.append(f"Row {idx+1}: {e}")
                row_dict = dict(r)
                row_dict["overall_urgency"] = "ERROR"
                row_dict["integrity_status"] = "ERROR"
                row_dict["total_alerts"] = 0
                row_dict["audit_hash"] = ""
                out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        if errors:
            print(f"Warnings ({len(errors)} errors):")
            for err in errors:
                print(f"  - {err}")
        return 0

    if args.command == "parse-spl":
        from spl_label_parser.xml_parser import parse_spl_file
        try:
            result = parse_spl_file(args.input)
            output = json.dumps(result, ensure_ascii=False, indent=2)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output + "\n")
            else:
                print(output)
            return 0
        except (OSError, ValueError) as exc:
            print(f"SPL parsing failed: {exc}", file=sys.stderr)
            return 2

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Drug Label Spl Fda Parser API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
