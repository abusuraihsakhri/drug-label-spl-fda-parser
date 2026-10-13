# Drug Label SPL FDA Parser

Extract section headings, narrative text, and identifiers from FDA Structured Product Labeling (SPL) XML. The repository also retains a separate numeric task-audit demonstration and FastAPI interface.

## Features

- **SPL XML extraction:** HL7 v3 namespace-aware parsing of document ID, set ID, version, effective time, title, and nested sections.
- **Section classification:** Recognizes FDA LOINC section codes for boxed warnings, indications, contraindications, dosage, adverse reactions, interactions, and warnings; retains unknown sections.
- **Browser utility:** Open `web/index.html` locally or publish the `web/` directory through GitHub Pages. Select an XML file or paste XML, filter sections, and export JSON or CSV. No server, account, or external data transfer is required.
- **Python CLI:** Parse SPL XML to JSON from the command line.
- **Legacy interfaces:** The existing numeric threshold audit, batch processing, supervisory query, and REST API remain available; these are demonstrations and **do not** validate SPL labels.

## Use

### Browser

Open `web/index.html` in a modern browser. Select **Load example** to try an illustrative sample; select **Parse XML** to extract its sections. Files are processed in browser memory. Export buttons download extracted data. The page works independently of Python.

### Python

Python 3.10 or later:

```bash
python -m pip install -e .
drug-label-spl-fda-parser parse-spl label.xml -o label.json
# Equivalent without installation:
python cli.py parse-spl label.xml -o label.json
```

The parser accepts UTF-8 SPL documents up to 5 MiB and rejects DTD and ENTITY declarations. It extracts document text, not markup fidelity, and does not validate XML against FDA SPL schemas.

### Optional API and legacy numeric audit

```bash
python -m pip install -e '.[api,test]'
export AUDIT_SECRET_KEY="$(openssl rand -hex 32)"
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2
python cli.py serve --host 127.0.0.1 --port 8000
python -m pytest -q
```

The existing API exposes `/health`, `/metrics`, `/api/audit`, `/api/chat`, and `/api/audit/logs`. The `/api/audit` endpoint accepts numeric task metrics, **not** an SPL XML document.

A Docker deployment is also available. Set a unique `AUDIT_SECRET_KEY` in the environment before running `docker compose up --build`. Never commit that key.

## Privacy and security

- The browser utility handles XML locally without sending files to a server. It does not use browser storage.
- The Python parser rejects DTD/ENTITY declarations, caps file size, and performs text-only extraction.
- The separate server-side numeric audit uses a keyed HMAC-SHA256 chain; keep its secret key private. Its heuristic PHI detection is **not** a guarantee of anonymization or HIPAA compliance.
- CSV exports escape formulas to reduce spreadsheet injection risk.
- Do not treat extraction, missing headings, or numeric audit alerts as clinical or regulatory validation. Consult the current FDA-authorized label and appropriate clinical references.

## Technology and compatibility

The Python parser uses the standard library's `xml.etree.ElementTree`. The browser uses built-in `DOMParser`, JavaScript, and CSS; modern Chromium, Firefox, and Safari are the intended targets. FastAPI/Pydantic/Uvicorn are optional API dependencies. GitHub Actions runs the Python suite across 3.10–3.13 and checks browser JavaScript syntax.

Section classification uses the [FDA Section Headings (LOINC)](https://www.fda.gov/industry/structured-product-labeling-resources/section-headings-loinc) reference. LOINC section identification is not schema conformance validation.

## License

MIT — see [LICENSE](LICENSE).
