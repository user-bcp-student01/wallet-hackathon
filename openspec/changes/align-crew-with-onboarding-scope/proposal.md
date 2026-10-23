# Proposal

## Why

The Crew's current frontend guidance mixes the onboarding flow with payments, payment access, and MAU/CAC analytics, even though the onboarding-specific scope excludes those outcomes. This causes generated solutions to exceed the intended demo and leaves the locally simulated, test-only OTP requirement underspecified.

## What Changes

- Align the Architect and Frontend agent guidance with the onboarding-specific scope: guided steps, input validation, actionable correction messages, simulated KYC outcomes, onboarding events, and the defined duration metric.
- Specify a local, fixed OTP entered manually for test phone numbers; do not add an OTP API or send SMS.
- Keep KYC review and wallet activation timing separate from the user's onboarding duration, and map mock statuses to the outcomes presented by the onboarding flow.
- Exclude payments, QR, transaction history, support consoles, MAU, CAC, and checkout measurement from onboarding generation.
- Add focused checks that guard these prompt requirements and exclusions against regressions.

## Capabilities

### New Capabilities

- `wallet-onboarding-generation`: Requirements for Crew-generated onboarding solutions to follow the onboarding scope, including local OTP simulation and explicit exclusions.

### Modified Capabilities

None.

## Impact

- Crew role guidance, primarily `agents/architect.py` and `agents/frontend.py`; test guidance and workflow verification may also need focused updates.
- Generated product artifacts only; no OTP endpoint, SMS integration, or wallet product implementation is added to this repository by the change itself.
- The onboarding-specific scope is the source for this capability. Related user-story documents still mention payment access and MAU/CAC; this change does not silently expand onboarding to include them.
