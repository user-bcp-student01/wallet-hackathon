# Design

## Context

The Crew builds each role task from the selected feature's title, description, and acceptance criteria. Its pipeline and generated product code are separate from this repository. The onboarding scope and mock contract are available in the repository, but the downstream model should not be expected to load those files unless their relevant requirements are included in its task instructions.

The onboarding-specific source is [alcance_onboarding.md](../../../docs/alcance/alcance_onboarding.md). The mock contract supports KYC verification and manual decisions, but has no OTP endpoint. Existing user-story and agent guidance also mentions payment access and acquisition analytics; those are not onboarding requirements.

## Goals / Non-Goals

**Goals:**

- Make onboarding-specific role instructions reflect the approved journey, KYC outcomes, test-data restrictions, and duration boundary.
- Keep onboarding-only constraints conditional on an onboarding feature so other wallet work continues to receive relevant guidance.
- Make prompt-level requirements testable without calling Copilot, MCP, or external services.

**Non-Goals:**

- Implement the generated wallet application in this repository.
- Change the Crew role order, checkpoint behavior, output contracts, or MCP feature-loading flow.
- Add or modify OTP, phone-verification, or KYC endpoints in the mock contract.
- Remove payment guidance from payment features or update the conflicting source user stories as part of this change.

## Decisions

### Encode onboarding constraints in role instructions

Update the relevant role prompts rather than adding runtime file loading. The Crew already passes feature context into each role task; embedding a concise onboarding rule set in the prompts avoids a new file dependency and ensures generated agents receive the requirements. Apply these rules when the selected feature is onboarding, not as a global ban on payment work.

The Architect and Frontend prompts define the solution and journey. Testing verifies the onboarding acceptance criteria. Security reinforces test-only identity data and the absence of real SMS. Chapter checks the final output against the feature scope and exclusions. Backend continues to implement only the approved contract; the optional Data role remains governed by the approved architecture.

An alternative was to load `docs/alcance/alcance_onboarding.md` dynamically at runtime. That would add behavior to feature loading and couple the Crew to a local document path, so it is deferred.

### Keep OTP entirely in the generated frontend

For onboarding, the Frontend instructions require a fixed, documented demo code and local generation/comparison in the UI. OTP behavior must not call the Wallet mock or another API and must not send SMS. The code is a test affordance, not a credential or proof of real phone ownership. Do not add an OTP route to `docs/openapi.json`.

An alternative was to use an existing mock endpoint, but the contract has no OTP capability and the user explicitly chose a frontend-only simulation.

### Use the existing mock only for KYC

The generated solution continues to use the documented KYC mock for onboarding verification. Present `ACTIVE` as approved and active, `PENDING` as manual review, and `REJECTED` as rejected. A pending review is resolved through the mock's decision capability; do not generate a separate support console.

### Define the metric boundary at successful data submission

Record onboarding start, completion of each step, and flow closure. End the user-flow duration when the complete onboarding submission is successfully accepted, before waiting for manual KYC review or later activation. Keep review and activation durations separate from the user-flow duration, and do not add MAU, CAC, or checkout analytics to onboarding.

### Verify prompts with local tests

Add focused tests over the task instructions or role prompts to check required onboarding guidance, the fixed local OTP boundary, KYC status mapping, data restrictions, and excluded features. Include a non-onboarding feature fixture to ensure onboarding-only exclusions do not suppress payment guidance for payment work. These tests must not invoke the model or external services.

## Risks / Trade-offs

- [Prompt rules can drift from the onboarding source] -> Keep the embedded rules concise and cover the required behavior with prompt-focused regression tests.
- [Onboarding exclusions could suppress valid payment work if applied globally] -> Make the rules conditional on the selected feature and test with a payment fixture.
- [A fixed OTP may be mistaken for real verification] -> Label it as a demo-only code and state that it is entered and checked locally with test phone data.
- [The mock's KYC status names differ from product outcome labels] -> State the `ACTIVE` / `PENDING` / `REJECTED` mapping directly in the Architect, Frontend, and Testing instructions.

## Migration Plan

No data migration or deployment is required. Update role instructions and their local regression checks; generated output is produced on a subsequent Crew run.
