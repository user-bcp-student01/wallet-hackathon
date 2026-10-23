# wallet-onboarding-generation Specification

## Purpose

Defines how the Crew must generate the wallet onboarding demo so its user journey, test-data handling, KYC outcomes, and analytics remain within the approved onboarding scope.

## Requirements

### Requirement: Generated onboarding follows the guided, validated journey
The Crew SHALL direct generated onboarding solutions to show required steps and current progress, block progression when required data is missing or invalid, and provide actionable correction messages.

#### Scenario: User corrects invalid onboarding data
- **WHEN** a required field is missing or contains an invalid value
- **THEN** the flow blocks progression and explains how the user can correct the field

### Requirement: OTP verification is local and deterministic
The Crew SHALL specify OTP as a local demo simulation using a fixed code entered manually for test phone numbers, without an OTP API or real SMS delivery.

#### Scenario: User verifies a test phone in the demo
- **WHEN** the user enters a test phone number and the documented fixed demo code
- **THEN** the local flow marks the simulated OTP step complete without contacting an SMS or OTP service

### Requirement: KYC outcomes are presented consistently
The Crew SHALL direct generated onboarding solutions to present the approved, manual-review, and rejected outcomes, mapping mock KYC statuses `ACTIVE`, `PENDING`, and `REJECTED` to those user-facing outcomes.

#### Scenario: KYC requires manual review
- **WHEN** the mock returns a manual-review scenario with status `PENDING`
- **THEN** the flow shows that review is pending and does not present the wallet as active

#### Scenario: KYC is approved or rejected
- **WHEN** the mock returns status `ACTIVE` or `REJECTED`
- **THEN** the flow clearly presents the corresponding approved-and-active or rejected outcome

### Requirement: Onboarding duration excludes KYC review and activation
The Crew SHALL direct generated solutions to record onboarding start, step completion, and flow closure events and calculate user-flow duration from start until successful submission of all step data, separately from KYC review and activation time.

#### Scenario: Successful submission ends the measured user flow
- **WHEN** the user successfully submits all required onboarding step data
- **THEN** the flow duration ends at that submission and KYC review and wallet activation durations remain separate

### Requirement: Onboarding uses test data only
The Crew SHALL constrain generated onboarding examples and flows to test documents and test phone numbers, without real personal documents, real personal phone numbers, or financial operations.

#### Scenario: Generated test journey uses sample identity data
- **WHEN** the generated journey demonstrates registration and KYC
- **THEN** it uses only test data and does not activate real financial operations

### Requirement: Onboarding generation respects scope exclusions
The Crew SHALL keep generated onboarding solutions limited to onboarding and SHALL NOT add payment, QR, transaction-history, payment-support, MAU, CAC, or checkout-measurement features to satisfy onboarding requirements.

#### Scenario: Onboarding request does not expand into payments or acquisition analytics
- **WHEN** the Crew generates a solution from the onboarding-specific scope
- **THEN** the generated requirements and screens exclude payments, QR, transaction history, payment-support tooling, MAU, CAC, and checkout measurement
