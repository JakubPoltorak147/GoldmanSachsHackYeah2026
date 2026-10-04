from __future__ import annotations

import textwrap
from pathlib import Path


W, H = 1280, 720
OUT = Path(__file__).with_name("ai-control-layer-presentation.pdf")

NAVY = (11, 23, 48)
INK = (27, 38, 63)
MUTED = (93, 108, 133)
BLUE = (35, 102, 214)
CYAN = (38, 181, 207)
MINT = (52, 189, 139)
AMBER = (232, 166, 57)
RED = (216, 74, 83)
PALE = (242, 246, 251)
WHITE = (255, 255, 255)
LINE = (214, 223, 235)


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def rgb(color: tuple[int, int, int]) -> str:
    return " ".join(f"{v / 255:.3f}" for v in color)


class Page:
    def __init__(self, title: str, number: int, dark: bool = False):
        self.ops: list[str] = []
        self.title = title
        self.number = number
        self.dark = dark
        self.bg(NAVY if dark else WHITE)

    def bg(self, color):
        self.rect(0, 0, W, H, color, stroke=None)

    def rect(self, x, y, w, h, fill, stroke=LINE, width=1, radius=0):
        if radius:
            # Rounded corners are represented as a clean rectangle in the PDF
            # source; this keeps the generated deck dependency-free.
            pass
        self.ops.append(f"{rgb(fill)} rg {x} {y} {w} {h} re f")
        if stroke:
            self.ops.append(f"{rgb(stroke)} RG {width} w {x} {y} {w} {h} re S")

    def line(self, x1, y1, x2, y2, color=LINE, width=1):
        self.ops.append(f"{rgb(color)} RG {width} w {x1} {y1} m {x2} {y2} l S")

    def circle(self, x, y, r, fill, stroke=None, width=1):
        k = 0.5522848 * r
        path = (
            f"{x+r} {y} m {x+r} {y+k} {x+k} {y+r} {x} {y+r} "
            f"{x-k} {y+r} {x-r} {y+k} {x-r} {y} "
            f"{x-r} {y-k} {x-k} {y-r} {x} {y-r} "
            f"{x+k} {y-r} {x+r} {y-k} {x+r} {y} c"
        )
        self.ops.append(f"{rgb(fill)} rg {path} f")
        if stroke:
            self.ops.append(f"{rgb(stroke)} RG {width} w {path} S")

    def text(self, x, y, value, size=18, color=INK, font="F1"):
        self.ops.append(f"BT /{font} {size} Tf {rgb(color)} rg {x} {y} Td ({esc(value)}) Tj ET")

    def paragraph(self, x, y, value, width, size=18, leading=25, color=INK, font="F1"):
        chars = max(12, int(width / (size * 0.52)))
        lines = []
        for raw in value.split("\n"):
            lines.extend(textwrap.wrap(raw, width=chars, break_long_words=False) or [""])
        for i, line in enumerate(lines):
            self.text(x, y - i * leading, line, size, color, font)
        return y - len(lines) * leading

    def label(self, x, y, value, color=BLUE):
        self.text(x, y, value.upper(), 12, color, "F2")

    def footer(self):
        color = (160, 176, 202) if self.dark else MUTED
        self.line(64, 45, 1216, 45, (54, 75, 107) if self.dark else LINE, 1)
        self.text(64, 25, "AI CONTROL LAYER  /  HACKYEAH 2026", 10, color, "F2")
        self.text(1170, 25, f"{self.number:02d}", 10, color, "F2")


def header(p: Page, kicker: str, title: str, subtitle: str | None = None):
    p.label(64, 650, kicker, CYAN if p.dark else BLUE)
    p.text(64, 590, title, 38, WHITE if p.dark else NAVY, "F2")
    if subtitle:
        p.paragraph(64, 548, subtitle, 780, 18, 26, (197, 211, 233) if p.dark else MUTED)


def pill(p: Page, x, y, text, fill, color=WHITE, w=None):
    w = w or max(92, len(text) * 9 + 30)
    p.rect(x, y, w, 28, fill, stroke=None)
    p.text(x + 15, y + 8, text, 11, color, "F2")


def make_pages():
    pages: list[Page] = []

    # 1 cover
    p = Page("Cover", 1, dark=True)
    p.circle(1080, 560, 180, (18, 42, 80))
    p.circle(1080, 560, 125, (25, 66, 113))
    p.circle(1080, 560, 70, CYAN)
    p.line(740, 560, 1010, 560, CYAN, 4)
    p.line(740, 560, 880, 470, CYAN, 4)
    p.line(880, 470, 1010, 560, CYAN, 4)
    p.label(72, 612, "AI SAFETY INFRASTRUCTURE", CYAN)
    p.text(72, 520, "Govern every", 66, WHITE, "F2")
    p.text(72, 448, "AI interaction", 66, WHITE, "F2")
    p.text(72, 386, "before it acts.", 66, CYAN, "F2")
    p.paragraph(76, 300, "A provider-independent control layer for model, agent, tool and API traffic.\nBuilt locally. Enforced centrally. Explained clearly.", 590, 23, 34, (197, 211, 233))
    pill(p, 76, 188, "ALLOW", MINT, NAVY, 106)
    pill(p, 196, 188, "REDACT", AMBER, NAVY, 116)
    pill(p, 326, 188, "BLOCK", RED, WHITE, 106)
    p.footer()
    pages.append(p)

    # 2 problem
    p = Page("Problem", 2)
    header(p, "THE THREAT", "AI traffic is becoming a new production boundary.", "Every prompt, tool call and model response can carry sensitive data or risky instructions. The control point must sit between intent and execution.")
    cards = [
        (64, 330, RED, "Sensitive data", "PII, credentials and private-key material can move into model or tool paths."),
        (438, 330, AMBER, "Unsafe intent", "Prompt injection, instruction override and exfiltration intent need policy decisions."),
        (812, 330, BLUE, "Blind operations", "Without safe evidence, operators cannot explain what happened or scale trust."),
    ]
    for x, y, accent, title, body in cards:
        p.rect(x, y, 330, 150, PALE, stroke=LINE)
        p.rect(x, y + 146, 330, 4, accent, stroke=None)
        p.text(x + 24, y + 105, title, 22, NAVY, "F2")
        p.paragraph(x + 24, y + 76, body, 278, 15, 21, MUTED)
    p.rect(64, 150, 1070, 96, NAVY, stroke=None)
    p.text(94, 205, "The opportunity", 15, CYAN, "F2")
    p.text(94, 169, "Make security a reusable service between every caller and every target.", 25, WHITE, "F2")
    p.footer(); pages.append(p)

    # 3 product architecture
    p = Page("Architecture", 3)
    header(p, "THE PRODUCT", "One control point. One decision model.", "The system normalizes an interaction, evaluates registered controls, applies central policy, records safe evidence and forwards only what is eligible.")
    xs = [82, 258, 472, 686, 900, 1098]
    labels = [("CALLER", "app / agent"), ("ADAPTER", "normalized"), ("CONTROLS", "deterministic + semantic"), ("POLICY", "ALLOW / REDACT / BLOCK"), ("AUDIT", "stdout + SQLite"), ("TARGET", "echo / local model")]
    fills = [NAVY, BLUE, CYAN, AMBER, MINT, NAVY]
    for i, ((top, bot), x, fill) in enumerate(zip(labels, xs, fills)):
        p.rect(x, 305, 142, 112, fill, stroke=None)
        p.text(x + 18, 365, top, 12, WHITE if fill != AMBER else NAVY, "F2")
        p.text(x + 18, 338, bot, 11, WHITE if fill != AMBER else NAVY)
        if i < len(xs) - 1:
            p.line(x + 142, 361, xs[i + 1] - 12, 361, BLUE, 3)
            p.line(xs[i + 1] - 20, 369, xs[i + 1] - 12, 361, BLUE, 3)
            p.line(xs[i + 1] - 20, 353, xs[i + 1] - 12, 361, BLUE, 3)
    p.rect(258, 170, 684, 58, PALE, stroke=LINE)
    p.text(292, 193, "Every decision is structured, explainable and auditable before eligible dispatch.", 17, INK, "F2")
    p.footer(); pages.append(p)

    # 4 live feature set
    p = Page("Features", 4)
    header(p, "WHAT IS LIVE", "A focused security pack that already works end to end.", "The current build is deliberately bounded: it proves the control-layer pattern with local targets, strict startup policy and deterministic tests.")
    features = [
        ("6", "registered controls", "email, bearer, PEM, GitHub, labelled SSN, known attacks"),
        ("3", "central actions", "ALLOW preserves, REDACT transforms, BLOCK stops"),
        ("2", "target boundaries", "local echo and operator-configured loopback Ollama"),
        ("19", "demo scenarios", "benign, deterministic, semantic and failure modes"),
    ]
    for i, (num, title, body) in enumerate(features):
        x = 64 + i * 290
        p.rect(x, 330, 250, 160, PALE, stroke=LINE)
        p.text(x + 24, 426, num, 46, BLUE if i != 1 else RED, "F2")
        p.text(x + 24, 390, title, 17, NAVY, "F2")
        p.paragraph(x + 24, 358, body, 200, 13, 18, MUTED)
    p.text(64, 246, "The system is provider-independent by construction:", 18, NAVY, "F2")
    p.paragraph(64, 214, "controls return findings; policy owns enforcement; adapters own protocol behavior; targets remain replaceable.", 980, 19, 27, MUTED)
    p.footer(); pages.append(p)

    # 5 decisions
    p = Page("Decisions", 5, dark=True)
    header(p, "THE MOMENT OF CONTROL", "A simple outcome users can trust.", "The decision engine makes the security posture visible in one line, while retaining the structured reasons behind it.")
    decision_cards = [
        (76, MINT, "ALLOW", "No finding maps to a stronger action.", "Forward the original interaction exactly once."),
        (442, AMBER, "REDACT", "A supported PII finding needs protection.", "Replace selected spans with [REDACTED] before forwarding."),
        (808, RED, "BLOCK", "A credential or known attack indicator is detected.", "Make zero target calls and return a safe reason."),
    ]
    for x, color, action, why, what in decision_cards:
        p.rect(x, 260, 300, 220, (19, 40, 74), stroke=(49, 75, 112))
        p.circle(x + 48, 432, 20, color)
        p.text(x + 84, 421, action, 26, WHITE, "F2")
        p.paragraph(x + 28, 365, why, 240, 16, 22, (197, 211, 233), "F2")
        p.paragraph(x + 28, 302, what, 240, 14, 20, (160, 176, 202))
    p.text(76, 190, "Central precedence:  BLOCK  >  REDACT  >  ALLOW", 18, CYAN, "F2")
    p.footer(); pages.append(p)

    # 6 coverage
    p = Page("Coverage", 6)
    header(p, "CONTROL COVERAGE", "Protection with honest boundaries.", "The pack recognizes precise supported shapes and keeps its claims narrow. That makes the behavior testable, explainable and safe to extend.")
    rows = [
        ("Email address", "pii.email", "REDACT", "bounded ASCII dot-atom"),
        ("Labelled US SSN", "pii.us_ssn", "REDACT", "labelled, fictional syntax"),
        ("Bearer / PEM / GitHub", "secret.*", "BLOCK", "supported token/key shapes"),
        ("Known attack literals", "attack.*", "BLOCK", "5 exact inert signatures"),
        ("Semantic security", "semantic.*", "BLOCK", "optional local evaluator"),
    ]
    p.rect(64, 188, 1090, 286, NAVY, stroke=None)
    cols = [88, 350, 610, 810]
    for x, label in zip(cols, ["CONTROL", "FINDING FAMILY", "DEFAULT", "BOUNDARY"]):
        p.text(x, 442, label, 11, CYAN, "F2")
    for i, row in enumerate(rows):
        y = 400 - i * 48
        if i % 2 == 0:
            p.rect(80, y - 15, 1050, 38, (19, 40, 74), stroke=None)
        p.text(88, y, row[0], 15, WHITE, "F2")
        p.text(350, y, row[1], 14, (197, 211, 233))
        p.text(610, y, row[2], 14, MINT if row[2] == "REDACT" else RED if row[2] == "BLOCK" else CYAN, "F2")
        p.text(810, y, row[3], 14, (197, 211, 233))
    p.paragraph(64, 132, "Current limits: no output inspection, auth, budgets, policy reload, remote provider or general secret / jailbreak detection. Those are product expansion points, not hidden claims.", 1080, 15, 22, MUTED)
    p.footer(); pages.append(p)

    # 7 evidence
    p = Page("Evidence", 7)
    header(p, "SAFE OPERATIONS", "Evidence that helps operators move fast.", "Every relevant decision becomes safe telemetry. The dashboard turns that evidence into a living view of posture, timing and outcomes.")
    p.rect(64, 218, 500, 270, PALE, stroke=LINE)
    p.text(92, 446, "AUDIT EVENT", 13, BLUE, "F2")
    audit_lines = ["server interaction ID", "UTC timestamp", "target + policy digest", "evaluated controls + enablement", "action + finding codes", "evaluation / invocation / total timing"]
    for i, line in enumerate(audit_lines):
        p.circle(100, 402 - i * 35, 5, MINT)
        p.text(120, 397 - i * 35, line, 16, INK)
    p.rect(620, 218, 534, 270, NAVY, stroke=None)
    p.text(650, 446, "DASHBOARD", 13, CYAN, "F2")
    metrics = [("ALLOW", "posture"), ("REDACT", "protected"), ("BLOCK", "stopped"), ("UNKNOWN", "evidence gap")]
    for i, (a, b) in enumerate(metrics):
        x = 650 + (i % 2) * 225
        y = 365 - (i // 2) * 80
        color = MINT if a == "ALLOW" else AMBER if a == "REDACT" else RED if a == "BLOCK" else (197, 211, 233)
        p.text(x, y, a, 20, color, "F2")
        p.text(x, y - 25, b, 14, (197, 211, 233))
    p.text(64, 160, "Privacy by design", 17, NAVY, "F2")
    p.paragraph(64, 132, "Audit and reporting retain safe metadata, never raw prompt content, matched values, spans, hashes, scores or exception text.", 1020, 18, 25, MUTED)
    p.footer(); pages.append(p)

    # 8 demo
    p = Page("Demo", 8, dark=True)
    header(p, "THE OPERATOR EXPERIENCE", "From live walkthrough to repeatable evidence.", "The local dashboard combines a read-only security overview with an interaction workbench for custom input and prepared scenarios.")
    groups = [("BENIGN", "ALLOW", MINT, "safe request"), ("DETERMINISTIC", "REDACT / BLOCK", AMBER, "PII, token, key, attack"), ("SEMANTIC", "BLOCK", RED, "injection, override, exfiltration"), ("FAILURE", "EXPLAIN", CYAN, "evaluator / target unavailable")]
    for i, (group, action, color, detail) in enumerate(groups):
        x = 76 + i * 285
        p.rect(x, 310, 250, 150, (19, 40, 74), stroke=(49, 75, 112))
        p.rect(x, 310, 8, 150, color, stroke=None)
        p.text(x + 28, 420, group, 13, color, "F2")
        p.text(x + 28, 380, action, 21, WHITE, "F2")
        p.text(x + 28, 344, detail, 14, (197, 211, 233))
    p.text(76, 230, "19", 42, CYAN, "F2")
    p.text(130, 242, "code-owned scenarios with expected explanations and actual-result reporting", 17, WHITE, "F2")
    p.paragraph(76, 182, "The operator can see what was expected, what happened, why policy chose the action and whether the target completed. A mismatch stays visible instead of being rewritten as success.", 1010, 17, 24, (197, 211, 233))
    p.footer(); pages.append(p)

    # 9 scalability
    p = Page("Scale", 9)
    header(p, "SCALABILITY", "Scale the boundary first; scale the adapters next.", "The architecture keeps the security decision core small and composable. That gives the product a credible path from local proof to platform service.")
    steps = [
        ("1", "Today", "in-process FastAPI\nlocal SQLite reporting", BLUE),
        ("2", "Next", "stateless control workers\nshared policy distribution", CYAN),
        ("3", "Platform", "remote adapters\ncentral event pipeline", MINT),
        ("4", "Enterprise", "identity, budgets, output DLP\nmodel/tool/resource governance", AMBER),
    ]
    for i, (num, stage, body, color) in enumerate(steps):
        x = 70 + i * 286
        p.circle(x + 32, 430, 25, color)
        p.text(x + 24, 421, num, 18, NAVY, "F2")
        p.text(x, 382, stage, 21, NAVY, "F2")
        p.paragraph(x, 348, body, 220, 15, 22, MUTED)
        if i < 3:
            p.line(x + 72, 430, x + 250, 430, LINE, 3)
    p.rect(70, 198, 1040, 74, NAVY, stroke=None)
    p.text(100, 241, "What scales cleanly", 15, CYAN, "F2")
    p.text(100, 211, "stateless controls  |  immutable registrations  |  policy-owned decisions  |  replaceable target adapters", 18, WHITE, "F2")
    p.paragraph(70, 148, "What remains intentionally local today: synchronous request handling, loopback Ollama, single-node SQLite and no distributed queue. These are clear deployment boundaries, not architecture dead ends.", 1050, 15, 22, MUTED)
    p.footer(); pages.append(p)

    # 10 proof and close
    p = Page("Close", 10, dark=True)
    header(p, "WHY THIS WINS", "A control layer people can adopt before they trust it at scale.", "It starts with a narrow, testable promise: no eligible AI interaction reaches a target without a policy decision and safe evidence.")
    proof = [("1,614", "unit + integration checks"), ("9", "Chromium journeys"), ("PASS", "fresh correctness + security reviews"), ("0", "target calls after BLOCK")]
    for i, (num, label) in enumerate(proof):
        x = 76 + (i % 2) * 520
        y = 300 - (i // 2) * 100
        p.text(x, y, num, 32, CYAN if i != 3 else RED, "F2")
        p.text(x + 150, y + 8, label, 18, WHITE, "F2")
    p.line(76, 160, 1130, 160, (49, 75, 112), 1)
    p.text(76, 117, "Protect the interaction. Preserve the evidence. Earn the next integration.", 25, WHITE, "F2")
    p.text(76, 78, "AI CONTROL LAYER  /  local proof today  /  scalable policy boundary tomorrow", 12, (160, 176, 202), "F2")
    p.footer(); pages.append(p)
    return pages


def build_pdf(pages: list[Page]):
    objects: list[bytes] = []

    def obj(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    font_regular = obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold = obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    page_ids = []
    for page in pages:
        stream = "\n".join(page.ops).encode("ascii")
        content_id = obj(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
        page_id = obj(
            f"<< /Type /Page /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 {font_regular} 0 R /F2 {font_bold} 0 R >> >> /Contents {content_id} 0 R >>".encode()
        )
        page_ids.append(page_id)
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages_id = obj(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode())
    catalog_id = obj(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, content in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{i} 0 obj\n".encode())
        data.extend(content)
        data.extend(b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(objects)+1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"wrote {OUT} ({len(pages)} pages, {len(data)} bytes)")


if __name__ == "__main__":
    build_pdf(make_pages())
