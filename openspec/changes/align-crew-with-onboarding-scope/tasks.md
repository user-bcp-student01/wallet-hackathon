# Tasks

## 1. Align onboarding role guidance

- [ ] 1.1 Update Architect and Frontend instructions so onboarding-specific requirements apply only to onboarding features; verify task prompts cover guided validation, KYC status mapping, the local fixed OTP, the duration boundary, test-only data, and scope exclusions.
- [ ] 1.2 Update Testing, Security, and Chapter instructions to verify onboarding acceptance criteria, test-data restrictions, frontend-only OTP behavior, and scope alignment; add prompt-focused assertions in `tests/test_workflow.py` and verify they run without model or external-service calls.
- [ ] 1.3 Add a non-onboarding payment-feature fixture to the prompt regression tests and verify onboarding exclusions do not suppress relevant payment guidance.

## 2. Verify Crew integration

- [ ] 2.1 Run `python tools/verify.py` and verify the prompt regression tests and existing six- and seven-role pipeline checks pass without Copilot, MCP, or GitHub credentials.
