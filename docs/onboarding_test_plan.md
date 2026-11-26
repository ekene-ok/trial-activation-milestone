# Onboarding test plan: first invoice by day 3

## Hypothesis
If new trials are guided to send a first invoice to a real client by day 3, more of them will reach that milestone, and more will convert to paid.

## Why a test is needed
The analysis is observational. Motivated trial users do more of everything, and even after adjustment, adding a client shows a 4.3 point effect when it has no real effect in this data. Every adjusted effect is therefore an upper bound. Only a randomized test shows how much of the invoice effect onboarding can actually create.

## Design
- **Who:** every new trial, randomized 50/50 at sign-up
- **Control:** current onboarding
- **Treatment:** onboarding built around one goal, sending the first invoice to a real client. The checklist puts it first, the day 1 and day 2 emails point to it, and mobile sign-ups get a short in-app walkthrough for invoicing on their phone
- **Guardrails:** trial cancellations in the first 3 days, support tickets per trial, invoices voided within 24 hours (a sign of test invoices sent to get past the prompt)

## Two stages
| Stage | Primary metric | Smallest lift worth detecting | Trials per arm | Length at 462 trials a week |
|---|---|---|---|---|
| 1 | Share of trials sending a first invoice by day 3 (now 28.5%) | 5 points | 1,342 | 6 weeks |
| 2 | Conversion to paid (now 19.6%) | 2.5 points | 4,148 | 18 weeks |

Both are sized for 80% power at a 5% significance level, two-sided.

## Decision rules
- **Stage 1 shows no lift in the milestone:** the onboarding change did not work. Redesign it before reading conversion
- **Stage 1 lifts the milestone, guardrails hold:** keep the test running into stage 2
- **Stage 2 lifts conversion:** roll out to all trials, and make "first invoice by day 3" the trial activation metric that lifecycle and product report on
- **Stage 2 shows no conversion lift despite the milestone lift:** the invoice was a marker of motivation, not a cause. Return to the action ranking and test the next candidate (connect payments)

## Owners
Lifecycle marketing (emails and test readout), Product (checklist and mobile walkthrough), Data (randomization and the readout queries in `sql/`).
