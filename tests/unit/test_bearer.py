import pytest

from app.control_layer.bearer_control import BearerCredentialControl
from app.control_layer.domain import Finding, Interaction, Span


def detect(text):
    return BearerCredentialControl().evaluate(Interaction.create("local-echo", text))


@pytest.mark.parametrize("token", ["a", "aB_9+/~.==", "A" * 4096, "a" + "=" * 4095])
@pytest.mark.parametrize(
    "framing", ["Authorization: Bearer {}", "\tAUTHORIZATION \t:\t bEaReR   {}\t "]
)
def test_supported_and_exact_spans(token, framing):
    text = framing.format(token)
    start = len(framing.split("{}", 1)[0])
    assert detect(text) == (
        Finding("bearer-credential", "secret.bearer", Span(start, start + len(token))),
    )


@pytest.mark.parametrize(
    "text",
    [
        "Bearer abc",
        "Proxy-Authorization: Bearer abc",
        '"Authorization: Bearer abc"',
        '{"Authorization": "Bearer abc"}',
        "prefix Authorization: Bearer abc",
        "Authorization: Bearer\tabc",
        "Authorization: Bearer ",
        "Authorization: Bearer a=b",
        "Authorization: Bearer =",
        "Authorization: Bearer abc def",
        "Authorization: Bearer abc,",
        "Authorization: Bearer 'abc'",
        "Authorization: Bearer abc\r",
        "Authorization: Bearer a\rb",
        "Authorization: Bearer åabc",
        "Authorization: Bearer " + "A" * 4097,
        "Authorization: Bearer abc%20def",
        "Authorization: Bearer abc\u2028",
    ],
)
def test_malformed_unsupported_no_partial(text):
    assert detect(text) == ()


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_multiple_multiline_unicode_offsets_and_recovery(newline):
    text = newline.join(
        [
            "😀 malformed",
            "Authorization: Bearer a=b",
            "Authorization: Bearer first==",
            "Authorization: Bearer second",
        ]
    )
    findings = detect(text)
    assert [text[f.span.start : f.span.end] for f in findings] == ["first==", "second"]
    assert [f.span.start for f in findings] == [
        text.index("first=="),
        text.index("second"),
    ]


def test_no_secondary_decode():
    assert detect(r"Authorization: Bearer abc\ndef") == ()
