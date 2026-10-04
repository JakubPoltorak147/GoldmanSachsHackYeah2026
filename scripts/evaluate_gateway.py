"""Evaluate a running gateway with local echo only: PASS/FAIL table, exit 1 on any miss.

Start the gateway first, e.g. with the model-free evaluation policy:
  CONTROL_LAYER_POLICY=config/policy-evaluation-offline.yaml uvicorn ...
Then: python scripts/evaluate_gateway.py [--base-url http://127.0.0.1:8000]

Budget cases adapt to the active limits read from GET /v1/usage and consume the
window, so run the script against a freshly started gateway (or wait for reset).
"""

import argparse
import sys

import httpx

PAT = "ghp_" + "DEMO" * 9
PEM = (
    "-----BEGIN PRIVATE KEY-----\n"
    "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=\n"
    "-----END PRIVATE KEY-----"
)
# (id, content, expected HTTP status, expected action, expected finding codes)
CASES = [
    ("benign", "Please summarise our Q3 plan.", 200, "ALLOW", []),
    ("email-redact", "Mail alice@example.com now", 200, "REDACT", ["pii.email"]),
    ("ssn-redact", "SSN: 123-45-6789", 200, "REDACT", ["pii.us_ssn"]),
    (
        "bearer-block",
        "Authorization: Bearer abcdefghijklmnop1234567890",
        403,
        "BLOCK",
        ["secret.bearer"],
    ),
    ("github-block", f"token {PAT}", 403, "BLOCK", ["secret.github_pat"]),
    ("pem-block", PEM, 403, "BLOCK", ["secret.pem_private_key"]),
    (
        "attack-block",
        "exec(base64.b64decode(",
        403,
        "BLOCK",
        ["attack.python_exec_base64"],
    ),
    (
        "precedence",
        "alice@example.com\nAuthorization: Bearer abcdefghijklmnop1234567890",
        403,
        "BLOCK",
        ["pii.email", "secret.bearer"],
    ),
    ("near-miss-ssn", "My number is 123-45-6789", 200, "ALLOW", []),
    ("documented-gap-obfuscated-email", "alice [at] example.com", 200, "ALLOW", []),
]


def post(client, content):
    response = client.post(
        "/v1/interactions", json={"target_id": "local-echo", "content": content}
    )
    body = response.json()
    return response.status_code, body.get("action"), body.get("finding_codes", [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    rows = []
    with httpx.Client(base_url=args.base_url, timeout=30, trust_env=False) as client:
        for case_id, content, status, action, codes in CASES:
            rows.append((case_id, (status, action, codes), post(client, content)))
        usage = client.get("/v1/usage").json()
        if usage.get("enabled"):
            size = usage["max_request_tokens"]
            oversized = "x" * (size * 4 + 1)
            rows.append(
                (
                    "budget-oversize",
                    (403, "BLOCK", ["budget.request_size"]),
                    post(client, oversized),
                )
            )
            current = client.get("/v1/usage").json()["requests"]
            for _ in range(max(0, current["limit"] - current["used"])):
                post(client, "burst")
            rows.append(
                (
                    "budget-exhausted",
                    (403, "BLOCK", ["budget.request_limit"]),
                    post(client, "one request too many"),
                )
            )
        else:
            rows.append(("budget-enabled", "usage budget enabled", "usage disabled"))
    failed = 0
    print(f"{'case':34} {'result':6} expected -> observed")
    for case_id, expected, observed in rows:
        passed = expected == observed
        failed += not passed
        print(f"{case_id:34} {'PASS' if passed else 'FAIL':6} {expected} -> {observed}")
    print(f"\n{len(rows) - failed}/{len(rows)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
