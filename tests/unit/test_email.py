import pytest

from app.control_layer.controls import EmailAddressControl
from app.control_layer.domain import Interaction


def matches(content):
    findings = EmailAddressControl().evaluate(Interaction.create("local-echo", content))
    assert all(
        f.control_id == "email-address" and f.code == "pii.email" for f in findings
    )
    return [content[f.span.start : f.span.end] for f in findings]


@pytest.mark.parametrize(
    "address",
    [
        "Alice+Tag@Sub.Example.COM",
        "a@b.co",
        "first.last@example.com",
        "!#$%&'*+-/=?^_`{|}~@example.com",
        "x" * 64 + "@example.com",
        "a@" + "b" * 63 + ".com",
        "a@b." + "c" * 63,
        "a@" + ".".join(["b" * 63] * 3 + ["c" * 61]),
    ],
)
def test_supported_and_maximum_boundaries(address):
    assert matches(address) == [address]


def test_exact_spans_punctuation_and_unicode_prefix():
    content = "Zażółć: <Alice+Tag@Sub.Example.COM>, (b@example.org)."
    assert matches(content) == ["Alice+Tag@Sub.Example.COM", "b@example.org"]


@pytest.mark.parametrize(
    "candidate",
    [
        "no address",
        "",
        "alice [at] example.com",
        "alice(at)example.com",
        ".a@example.com",
        "a.@example.com",
        "a..b@example.com",
        "x" * 65 + "@example.com",
        "a@" + "b" * 64 + ".com",
        "a@" + ".".join(["b" * 63] * 4),
        "a@b.c",
        "a@b.c0m",
        "a@b.123",
        "a@-b.com",
        "a@b-.com",
        "a@b..com",
        "a@b.com..",
        "a@b.com_extra",
        "a@b.com/path",
        "a@b.com@other.com",
        "a@b.com-",
        "a@b.com!",
        '"alice"@example.com',
        '"a b"@example.com',
        "alice@[127.0.0.1]",
        "éa@example.com",
        "a@example.comé",
        "a@éxample.com",
        "a@xn--example.com",
        "a@b.XN--example.com",
        "a@XN--example.b.com",
        "alice&#64;example.com",
        "alice%40example.com",
        "YWxpY2VAZXhhbXBsZS5jb20=",
        "a@example.com:bad",
    ],
)
def test_malformed_and_documented_unsupported_forms(candidate):
    assert matches(candidate) == []


@pytest.mark.parametrize(
    "candidate",
    [
        '"a(b@example.com)"@example.org',
        '"a<b@example.com>"@example.org',
        '"a,b@example.com,c"@example.net',
        '"a (b@example.com) c"@example.net',
        '"a\\" (b@example.com) c"@example.net',
    ],
)
def test_quoted_local_delimiters_do_not_expose_inner_substrings(candidate):
    assert matches(candidate) == []


def test_quoted_local_does_not_suppress_separate_supported_address():
    assert matches('"a(b@example.com)"@example.org, real@example.com') == [
        "real@example.com"
    ]


@pytest.mark.parametrize(
    "candidate", ["alice&#46;smith@example.com", "alice&#x2e;smith@example.com"]
)
def test_html_entity_local_part_does_not_expose_suffix(candidate):
    assert matches(candidate) == []
