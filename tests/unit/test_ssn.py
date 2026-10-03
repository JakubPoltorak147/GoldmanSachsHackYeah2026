import pytest

from app.control_layer.domain import Finding, Interaction, Span
from app.control_layer.ssn_control import UsSsnControl


def detect(text):
    return UsSsnControl().evaluate(Interaction.create("local-echo", text))


@pytest.mark.parametrize("label", ["SSN:", "us ssn:\t", "SsN \t: ", "US SSN:"])
@pytest.mark.parametrize(
    "value", ["001-01-0001", "665-99-9999", "667-01-0001", "899-99-9999", "123-45-6789"]
)
def test_supported_labels_group_boundaries_exact_span(label, value):
    text = "😀 (" + label + value + "),"
    start = text.index(value)
    assert detect(text) == (Finding("us-ssn", "pii.us_ssn", Span(start, start + 11)),)


@pytest.mark.parametrize(
    "value",
    [
        "000-45-6789",
        "666-45-6789",
        "900-45-6789",
        "999-45-6789",
        "123-00-6789",
        "123-45-0000",
        "12-45-6789",
        "123-4-6789",
        "123-45-678",
        "123-45-67890",
        "１２３-45-6789",
        "١٢٣-45-6789",
        "123456789",
        "123 45 6789",
        "123-45-6789x",
        "123-45-6789_",
        "123-45-6789-",
        "123-45-6789é",
    ],
)
def test_invalid_whole_candidates(value):
    assert detect("SSN: " + value) == ()


@pytest.mark.parametrize(
    "text",
    [
        "123-45-6789",
        "TIN: 123-45-6789",
        "SSN=123-45-6789",
        "mySSN: 123-45-6789",
        "_SSN: 123-45-6789",
        "éSSN: 123-45-6789",
        "SSN:\n123-45-6789",
        "SSN:\r\n123-45-6789",
        'SSN: "123-45-6789"',
        "SSN: [123-45-6789]",
        "SSN: 123%2D45%2D6789",
    ],
)
def test_unsupported_context(text):
    assert detect(text) == ()


def test_multiline_multiple_unicode_offsets_and_recovery():
    text = "😀 SSN: 000-45-6789\nSSN: 123-45-6789.\r\nSSN:\t321-54-6789"
    findings = detect(text)
    assert [text[f.span.start : f.span.end] for f in findings] == [
        "123-45-6789",
        "321-54-6789",
    ]
    assert findings[0].span.start == text.index("123-45-6789")
    assert detect("SSN:123-45-6789") != ()


@pytest.mark.parametrize("prefix", ["X", "é", "_", "1", "١"])
def test_invalid_long_label_cannot_hide_supported_inner_ssn(prefix):
    text = prefix + "US SSN: 123-45-6789"
    assert detect(text) == (Finding("us-ssn", "pii.us_ssn", Span(9, 20)),)
