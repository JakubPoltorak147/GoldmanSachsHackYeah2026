import pytest

from app.control_layer.domain import Finding, Interaction, Span
from app.control_layer.github_control import GitHubTokenControl


def detect(text):
    return GitHubTokenControl().evaluate(Interaction.create("local-echo", text))


@pytest.mark.parametrize(
    "prefix,code", [("ghp_", "secret.github_pat"), ("gho_", "secret.github_oauth")]
)
@pytest.mark.parametrize(
    "delimiter", ["", " ", "\n", "'", '"', ",", ".", "(", ")", "[", "]"]
)
def test_whole_shapes_delimiters_exact_spans(prefix, code, delimiter):
    token = prefix + "aB09" * 9
    text = delimiter + token + delimiter
    assert detect(text) == (
        Finding("github-token", code, Span(len(delimiter), len(delimiter) + 40)),
    )


@pytest.mark.parametrize("prefix", ["ghp_", "gho_"])
@pytest.mark.parametrize("size", [0, 35, 37, 1000])
def test_wrong_lengths(prefix, size):
    assert detect(prefix + "A" * size) == ()


@pytest.mark.parametrize("extension", ["a", "0", "_", "-", "é", "١", "中"])
@pytest.mark.parametrize("side", ["left", "right"])
def test_whole_candidate_continuations(extension, side):
    token = "ghp_" + "A" * 36
    text = extension + token if side == "left" else token + extension
    assert detect(text) == ()


@pytest.mark.parametrize(
    "prefix", ["GHP_", "GHO_", "github_pat_", "ghu_", "ghs_", "ghr_", "", "sk-"]
)
def test_unsupported_prefixes(prefix):
    assert detect(prefix + "A" * 36) == ()


def test_multiple_embedded_multiline_unicode_offsets_and_malformed_neighbor():
    pat, oauth = "ghp_" + "A" * 36, "gho_" + "b" * 36
    text = f"😀 token='{pat}'\r\n{pat}x ({oauth}), {pat}."
    findings = detect(text)
    assert [text[f.span.start : f.span.end] for f in findings] == [pat, oauth, pat]
    assert [f.code for f in findings] == [
        "secret.github_pat",
        "secret.github_oauth",
        "secret.github_pat",
    ]


def test_unicode_candidate_and_no_reconstruction():
    assert detect("ghp_" + "A" * 35 + "é") == ()
    assert detect("ghp_" + "A" * 18 + " " + "A" * 18) == ()
    assert detect("ghp%5F" + "A" * 36) == ()
