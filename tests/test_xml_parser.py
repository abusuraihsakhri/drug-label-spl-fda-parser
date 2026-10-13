import pytest
from spl_label_parser.xml_parser import MAX_XML_BYTES, parse_spl

SPL = '''<?xml version="1.0" encoding="UTF-8"?>
<document xmlns="urn:hl7-org:v3">
  <id root="test-document"/><setId root="test-set"/>
  <versionNumber value="3"/><effectiveTime value="20261013"/>
  <title>Example drug labeling</title>
  <component><structuredBody><component><section>
    <code code="34066-1" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Boxed Warning</title>
    <text><paragraph>Severe <content>risk</content> warning.</paragraph></text>
  </section></component><component><section>
    <code code="34070-3" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Contraindications</title><text>Known hypersensitivity.</text>
    <component><section><code code="99999-9" codeSystem="2.16.840.1.113883.6.1"/><title>Other</title><text>Nested.</text></section></component>
  </section></component></structuredBody></component>
</document>'''


def test_metadata_and_sections():
    doc = parse_spl(SPL.encode("utf-8"))
    assert doc["document_id"] == "test-document"
    assert doc["set_id"] == "test-set"
    assert doc["version_number"] == "3"
    assert doc["effective_time"] == "20261013"
    assert doc["title"] == "Example drug labeling"
    assert len(doc["sections"]) == 3
    assert doc["sections"][0]["category"] == "boxed_warning"
    assert doc["sections"][0]["text"] == "Severe risk warning."
    assert doc["sections"][1]["text"] == "Known hypersensitivity."
    assert doc["sections"][2]["category"] == "other"


def test_wrong_code_system_not_classified():
    doc = parse_spl(SPL.replace("2.16.840.1.113883.6.1", "example"))
    assert doc["sections"][0]["category"] == "other"


@pytest.mark.parametrize("xml", [
    '<!DOCTYPE document [<!ENTITY x "unsafe">]><document xmlns="urn:hl7-org:v3"/>',
    '<!doctype document SYSTEM "http://example.test/foo"><document xmlns="urn:hl7-org:v3"/>',
    "<document>",
    "<something/>",
])
def test_reject_invalid_xml(xml):
    with pytest.raises(ValueError):
        parse_spl(xml)


def test_reject_oversized():
    with pytest.raises(ValueError, match="size limit"):
        parse_spl(" " * (MAX_XML_BYTES + 1))


def test_unicode_and_empty():
    doc = parse_spl('\ufeff<document xmlns="urn:hl7-org:v3"><title>Médicament</title></document>')
    assert doc["title"] == "Médicament"
    assert doc["sections"] == []
