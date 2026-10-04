// Display vocabulary only. Decisions and identities always come from the gateway.
const controls = Object.freeze({
  'email-address': 'Email detection',
  'bearer-credential': 'Authorization credential detection',
  'pem-private-key': 'Private-key envelope detection',
  'github-token': 'GitHub token detection',
  'us-ssn': 'US Social Security number detection',
  'known-attack-signatures': 'Known attack indicators',
  'semantic-security': 'Semantic attack inspection',
});
const findings = Object.freeze({
  'pii.email': ['Email address', 'A supported email-address pattern was detected.'],
  'pii.us_ssn': ['US Social Security number', 'A supported labelled number pattern was detected; identity was not verified.'],
  'secret.bearer': ['Authorization credential', 'A supported authorization-header credential pattern was detected.'],
  'secret.pem_private_key': ['Private-key envelope', 'A supported complete private-key envelope shape was detected; the key was not cryptographically validated.'],
  'secret.github_pat': ['GitHub personal token', 'A supported personal-token shape was detected; provider authenticity was not checked.'],
  'secret.github_oauth': ['GitHub OAuth token', 'A supported OAuth-token shape was detected; provider authenticity was not checked.'],
  'attack.pickle_os_system': ['Pickle OS execution indicator', 'An exact configured serialization execution indicator was detected as inert text.'],
  'attack.pickle_posix_system': ['Pickle POSIX execution indicator', 'An exact configured serialization execution indicator was detected as inert text.'],
  'attack.python_os_system': ['Python execution indicator', 'An exact configured execution indicator was detected; no code was executed.'],
  'attack.python_exec_base64': ['Encoded execution indicator', 'An exact configured encoded-execution indicator was detected; nothing was decoded for execution.'],
  'semantic.prompt_injection': ['Prompt injection', 'Semantic inspection identified an attempt to redirect instructions.'],
  'semantic.instruction_override': ['Instruction override', 'Semantic inspection identified an attempt to replace governing rules.'],
  'semantic.exfiltration_intent': ['Protected-data disclosure attempt', 'Semantic inspection identified an instruction attack seeking protected data.'],
});
const actions = Object.freeze({ ALLOW: 'Allowed by policy', REDACT: 'Sensitive data removed', BLOCK: 'Stopped by policy' });
const errors = Object.freeze({
  evaluation_failed: 'Safety check could not finish',
  audit_failed: 'Required auditing failed',
  target_failed: 'Target could not complete',
  invalid_request: 'Request rejected',
  service_unavailable: 'Service unavailable',
  reporting_unavailable: 'Reporting evidence unavailable',
  reporting_write_failed: 'Reporting write gate failed',
  not_found: 'Not found',
  method_not_allowed: 'Request method unavailable',
});
const own = (table, key) => Object.hasOwn(table, key) ? table[key] : undefined;
export const controlName = id => own(controls, id) ?? 'Other control';
export const findingName = code => own(findings, code)?.[0] ?? 'Other finding';
export const findingMeaning = code => own(findings, code)?.[1] ?? 'A registered control reported this finding; its specific meaning is not in this display vocabulary.';
export const actionName = action => own(actions, action) ?? 'No policy decision';
export const actionLabel = action => action ? `${actionName(action)} (${action})` : 'No policy decision';
export const errorLabel = code => `${own(errors, code) ?? 'Operational outcome unavailable'} (${code})`;
export const findingLabel = code => `${findingName(code)} (${code})`;
export const controlLabel = id => `${controlName(id)} (${id})`;
