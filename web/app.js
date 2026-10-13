"use strict";
const NS = "urn:hl7-org:v3";
const LOINC = "2.16.840.1.113883.6.1";
const MAX_BYTES = 5 * 1024 * 1024;
const CATEGORIES = Object.freeze({
  "34066-1": "boxed_warning", "34067-9": "indications_and_usage",
  "34070-3": "contraindications", "34068-7": "dosage_and_administration",
  "34084-4": "adverse_reactions", "34073-7": "drug_interactions",
  "43685-7": "warnings_and_precautions", "34071-1": "warnings"
});
const EXAMPLE = [
  '<?xml version="1.0" encoding="UTF-8"?>',
  '<document xmlns="urn:hl7-org:v3">',
  '<id root="sample-spl-001"/><setId root="sample-set-001"/>',
  '<versionNumber value="1"/><effectiveTime value="20261013"/>',
  '<title>Illustrative drug label — not for clinical use</title>',
  '<component><structuredBody>',
  '<component><section><code code="34066-1" codeSystem="2.16.840.1.113883.6.1"/>',
  '<title>Boxed Warning</title><text>Example warning text, not a real drug label.</text></section></component>',
  '<component><section><code code="34070-3" codeSystem="2.16.840.1.113883.6.1"/>',
  '<title>Contraindications</title><text>Example contraindications text.</text></section></component>',
  '</structuredBody></component></document>'
].join("\n");

function plainText(element) {
  return element ? (element.textContent || "").replace(/\s+/g, " ").trim() : "";
}
function child(parent, name) {
  return [...parent.children].find(el => el.namespaceURI === NS && el.localName === name) || null;
}
function field(root, name, attribute) {
  const el = child(root, name);
  return el ? (el.getAttribute(attribute) || null) : null;
}
function parseSpl(source) {
  if (new TextEncoder().encode(source).length > MAX_BYTES) throw new Error("SPL XML exceeds the 5 MiB limit.");
  if (/<!\s*(?:DOCTYPE|ENTITY)\b/i.test(source)) throw new Error("DOCTYPE and ENTITY declarations are not allowed.");
  const xml = new DOMParser().parseFromString(source, "application/xml");
  if (xml.querySelector("parsererror")) throw new Error("Malformed XML. Review the document syntax.");
  const root = xml.documentElement;
  if (root.namespaceURI !== NS || root.localName !== "document") throw new Error("Expected an HL7 v3 SPL document root.");
  const sections = [...xml.getElementsByTagNameNS(NS, "section")].map(section => {
    const code = child(section, "code");
    const value = code?.getAttribute("code") || "";
    const codeSystem = code?.getAttribute("codeSystem") || "";
    return {
      code: value, code_system: codeSystem,
      category: codeSystem === LOINC ? (CATEGORIES[value] || "other") : "other",
      title: plainText(child(section, "title")),
      text: plainText(child(section, "text"))
    };
  });
  return {
    document_id: field(root, "id", "root") || field(root, "id", "extension"),
    set_id: field(root, "setId", "root") || field(root, "setId", "extension"),
    version_number: field(root, "versionNumber", "value"),
    effective_time: field(root, "effectiveTime", "value"),
    title: plainText(child(root, "title")), sections
  };
}

let parsed = null;
const byId = id => document.getElementById(id);
function status(message, error = false) {
  byId("feedback").textContent = message;
  byId("feedback").classList.toggle("error", error);
}
function render() {
  const result = byId("results");
  result.hidden = !parsed;
  if (!parsed) return;
  const meta = byId("metadata");
  meta.replaceChildren();
  for (const [label, val] of [
    ["Label title", parsed.title], ["Document ID", parsed.document_id],
    ["Set ID", parsed.set_id], ["Version", parsed.version_number],
    ["Effective time", parsed.effective_time]
  ]) {
    const wrapper = document.createElement("div"); wrapper.className = "meta-item";
    const dt = document.createElement("dt"); dt.textContent = label;
    const dd = document.createElement("dd"); dd.textContent = val || "Not provided";
    wrapper.append(dt, dd); meta.append(wrapper);
  }
  const filter = byId("section-filter").value;
  const shown = parsed.sections.filter(s => filter === "all" || s.category === filter);
  byId("section-count").textContent = shown.length + " shown / " + parsed.sections.length + " extracted";
  const container = byId("sections"); container.replaceChildren();
  if (!shown.length) {
    const p = document.createElement("p"); p.className = "empty";
    p.textContent = "No sections match this filter."; container.append(p);
  }
  for (const section of shown) {
    const card = document.createElement("article"); card.className = "section";
    const heading = document.createElement("h3"); heading.textContent = section.title || "Untitled section";
    const code = document.createElement("small");
    code.textContent = (section.code || "No code") + " · " + section.category.replaceAll("_", " ");
    const text = document.createElement("p"); text.textContent = section.text || "No text supplied";
    card.append(heading, code, text); container.append(card);
  }
}
function download(content, mime, filename) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a"); link.href = url; link.download = filename;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function csvCell(value) {
  const s = String(value ?? "");
  const safe = /^[\s]*[=+@-]/.test(s) ? "'" + s : s;
  return '"' + safe.replaceAll('"', '""') + '"';
}
function toCsv(sections) {
  const keys = ["code", "code_system", "category", "title", "text"];
  return [keys.map(csvCell).join(","), ...sections.map(s => keys.map(k => csvCell(s[k])).join(","))].join("\r\n") + "\r\n";
}

byId("xml-file").addEventListener("change", async event => {
  const file = event.target.files[0]; if (!file) return;
  if (file.size > MAX_BYTES) { status("File exceeds the 5 MiB limit.", true); return; }
  try {
    const text = await file.text();
    if (new TextEncoder().encode(text).length !== file.size && text.includes("\ufffd")) throw new Error("File is not valid UTF-8.");
    byId("xml-input").value = text;
    status("Loaded " + file.name + ". Select Parse XML to extract sections.");
  } catch (error) { status(error.message, true); }
});
byId("demo").addEventListener("click", () => {
  byId("xml-input").value = EXAMPLE;
  byId("xml-file").value = "";
  status("Illustrative sample loaded. Select Parse XML.");
});
byId("parse").addEventListener("click", () => {
  try {
    parsed = parseSpl(byId("xml-input").value);
    status("Parsed " + parsed.sections.length + " section(s).");
  } catch (error) {
    parsed = null; status(error.message, true);
  }
  render();
});
byId("section-filter").addEventListener("change", render);
byId("download-json").addEventListener("click", () => {
  if (parsed) download(JSON.stringify(parsed, null, 2), "application/json", "spl-label.json");
});
byId("download-csv").addEventListener("click", () => {
  if (parsed) download(toCsv(parsed.sections), "text/csv;charset=utf-8", "spl-sections.csv");
});
