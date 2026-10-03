import base64
import textwrap

import pytest

from app.control_layer.domain import Finding, Interaction, Span
from app.control_layer.pem_control import PemPrivateKeyControl


def envelope(label="PRIVATE KEY", size=32, newline="\n", body=None):
    if body is None:
        body = newline.join(textwrap.wrap(base64.b64encode(b"x" * size).decode(), 64))
    return newline.join([f"-----BEGIN {label}-----", body, f"-----END {label}-----"])


def detect(text):
    return PemPrivateKeyControl().evaluate(Interaction.create("local-echo", text))


@pytest.mark.parametrize(
    "label",
    [
        "PRIVATE KEY",
        "RSA PRIVATE KEY",
        "EC PRIVATE KEY",
        "OPENSSH PRIVATE KEY",
        "ENCRYPTED PRIVATE KEY",
    ],
)
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("size", [32, 33, 48, 97])
def test_all_labels_wrapping_and_exact_span(label, newline, size):
    block = envelope(label, size, newline)
    text = "😀\n" + block + newline
    assert detect(text) == (
        Finding("pem-private-key", "secret.pem_private_key", Span(2, 2 + len(block))),
    )


@pytest.mark.parametrize(
    "body",
    [
        "",
        "eA==",
        base64.b64encode(b"x" * 31).decode(),
        "A" * 65,
        "A" * 42 + "B=",
        "!" * 44,
        "eH==",
        "eA==\neA==",
        "A===",
        "Proc-Type: 4,ENCRYPTED\neA==",
        "\n" + base64.b64encode(b"x" * 32).decode(),
    ],
)
def test_invalid_body(body):
    assert detect(envelope(body=body)) == ()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda b: b.replace("END PRIVATE KEY", "END PUBLIC KEY"),
        lambda b: b.replace("-----BEGIN", "----BEGIN"),
        lambda b: b.replace("-----END", "------END"),
        lambda b: b.replace("BEGIN", "begin"),
        lambda b: b.replace("PRIVATE KEY", "private key"),
        lambda b: b.replace("PRIVATE KEY", "PRIVATE  KEY"),
        lambda b: " " + b,
        lambda b: b.replace("KEY-----", "KEY----- "),
        lambda b: b + "\r",
        lambda b: b.rsplit("\n", 1)[0],
        lambda b: b.replace("\n", "\r"),
    ],
)
def test_malformed_framing(mutation):
    assert detect(mutation(envelope())) == ()


@pytest.mark.parametrize(
    "label", ["PUBLIC KEY", "CERTIFICATE", "DSA PRIVATE KEY", "X" * 65]
)
def test_unsupported_label(label):
    assert detect(envelope(label)) == ()


def test_nested_begin_suppressed_and_unsupported_end_recovery():
    good = envelope()
    text = "-----BEGIN PRIVATE KEY-----\n" + good + "\n" + good
    findings = detect(text)
    assert len(findings) == 1
    assert findings[0].span.start == text.rindex("-----BEGIN")
    first = good.replace("END PRIVATE KEY", "END PUBLIC KEY")
    text = first + "\n" + good
    assert detect(text) == (
        Finding(
            "pem-private-key", "secret.pem_private_key", Span(len(first) + 1, len(text))
        ),
    )


def test_unsupported_nested_marker_invalidates_candidate():
    text = envelope().replace("\n", "\n-----BEGIN PUBLIC KEY-----\n", 1)
    assert detect(text) == ()


def test_multiple_blocks_mixed_newlines_and_content_limit():
    one, two = envelope(), envelope("RSA PRIVATE KEY", 97, "\r\n")
    prefix = "😀" * (16384 - len(one) - len(two) - 2) + "\n"
    text = prefix + one + "\n" + two
    assert len(text) == 16384
    findings = detect(text)
    assert [text[f.span.start : f.span.end] for f in findings] == [one, two]
    mixed = one.replace("\n", "\r\n", 1)
    assert detect(mixed)[0].span == Span(0, len(mixed))


def test_encoded_binary_or_inline_no_detection():
    assert detect(base64.b64encode(envelope().encode()).decode()) == ()
    assert detect(envelope().replace("\n", r"\n")) == ()
    assert detect("prefix " + envelope()) == ()
    assert detect("\x00\x30\x81 key bytes") == ()
