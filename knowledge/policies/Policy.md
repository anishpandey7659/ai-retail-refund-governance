# ReturnGuard Returns and Refund Policy (RG-POL-001 v1.1)

Nov 9, 2026 · @Anish pandey

This policy tells ReturnGuard when to approve, deny, block or escalate a return, and how to calculate the refund. Version 1.1 keeps the intent of v1.0 and resolves its four conflicts. Every value marked **(demo assumption)** is a sample setting that Customer Operations can change.

## Document control

| Field | Value |
| --- | --- |
| Document ID | RG-POL-001 |
| Version | 1.1 (supersedes 1.0) |
| Effective date | 2026-11-09 |
| Owner | Customer Operations |
| System | ReturnGuard |
| Status | Active, sample policy for a ReturnGuard demo |

## 1. Return eligibility by reason

Each request carries exactly one reason code. The code decides the conditions, the evidence needed and who pays return shipping.

| Reason code | Eligibility | Required conditions |
| --- | --- | --- |
| `damaged` | Eligible | Product arrived damaged. Damage caused by customer misuse after delivery is not covered. |
| `defective` | Eligible | Product fails to work as intended under normal use. Misuse, unauthorized modification and accidental damage are excluded. |
| `wrong_item` | Eligible | Product, model, size or variant differs from the order. |
| `not_as_described` | Eligible | Product materially differs from its listing in specifications, materials, functionality or advertised features. Minor variations do not qualify. |
| `quality` | Conditional | A demonstrable quality issue materially affects use, durability or performance. Subjective dissatisfaction alone does not qualify. |
| `arrived_late` | Conditional | Delivered at least 3 calendar days after the promised date **(demo assumption)** and the customer states the delay made the purchase less useful. |
| `no_longer_needed` | Conditional | Product is unused, in original packaging, with all accessories and manuals. Category exclusions in Section 4 apply. |

## 2. Return windows

The delivery date is Day 0. The last eligible day is Day N, ending at 23:59 in the time zone of the delivery address. A request on Day 30 is on time; a request on Day 31 is late.

| Reason | Standard, clothing, furniture | Electronics |
| --- | --- | --- |
| `no_longer_needed` | 30 days | 15 days |
| `damaged`, `defective`, `wrong_item`, `not_as_described`, `quality`, `arrived_late` | 30 days | 30 days |

The shorter electronics window applies only to change-of-mind returns. A damaged laptop reported on day 20 is within its window.

### Late requests

| Reason | Handling |
| --- | --- |
| `no_longer_needed` | Deny automatically with a clear explanation. The customer may appeal under Section 11. |
| Every other reason | Escalate to a human reviewer, who may approve or deny the exception. |

## 3. Product condition

- **Unused:** original condition, all accessories and original packaging included, no signs of use.
- **Opened:** may be returned if unused, complete and not in a restricted category. Opening the packaging alone does not make a product ineligible.
- **Used:** not eligible for change of mind. A product that failed during normal use is evaluated separately as `defective`.
- **Damaged in transit:** eligible for return or replacement. Missing photos never cause automatic rejection; the case is escalated.

## 4. Non-returnable products

These categories cannot be returned for change of mind:

1. Perishable goods, including fresh food.
2. Personalized or customized products.
3. Digital products after delivery or activation.
4. Products marked final sale.
5. Opened products that cannot be resold for hygiene or safety reasons.
6. Gift cards and prepaid vouchers.

A defect, wrong-item, damage or not-as-described claim on a non-returnable product is escalated for individual review. It is never denied automatically.

## 5. Evidence requirements

The system asks for the minimum evidence below. Missing or conflicting evidence escalates the case; it is never treated as proof of a violation.

| Reason | Minimum evidence |
| --- | --- |
| `damaged` | One photo of the damage and a short description. Packaging photo if available. |
| `defective` | Description of the failure. Photo or video if the failure is visible. |
| `wrong_item` | Photo of the item received, including its label or packaging. |
| `not_as_described` | Photo of the item and the listing statement it contradicts. |
| `quality` | Description and at least one photo. |
| `arrived_late` | None from the customer. The carrier delivery timestamp is checked against the promised date. |
| `no_longer_needed` | Confirmation of condition. Verified at inspection. |

## 6. Return process and inspection

1. The customer submits a request with a reason code and any evidence.
2. ReturnGuard issues a decision: approve, deny, block or escalate.
3. On approval, the customer receives a return label and has 10 days to ship **(demo assumption)**.
4. If a physical return is required, the item is inspected within 5 business days of receipt **(demo assumption)**.
5. If inspection finds the item does not match the claim, the case is escalated. It is not denied automatically.
6. If the carrier reports the parcel lost in transit, the case is escalated and the customer is not penalized.
7. If a replacement is out of stock, the customer chooses a refund or a later replacement.

## 7. Refunds

A refund requires an approved request, a product that meets the return conditions and, where needed, a completed inspection. Refunds go to the original payment method.

### Refund amount

The refund never exceeds the amount paid for the returned item. The calculation uses transaction data, not an LLM estimate, and accounts for:

- Original item price.
- Discounts and promotional adjustments.
- Applicable taxes.
- Previously issued partial refunds.

### Shipping charges

- Original shipping is not refunded for change-of-mind returns.
- Original shipping is refunded for wrong item, damaged, defective and not-as-described returns.
- For `arrived_late`, original shipping is refunded when the delay is 7 calendar days or more **(demo assumption)**.

### Processing time

| Payment method | Expected time |
| --- | --- |
| Credit or debit card | 5 to 10 business days |
| Digital wallet | 3 to 7 business days |
| Bank transfer | 5 to 10 business days |
| Store credit | 1 to 2 business days |

These are estimates. Actual crediting depends on the payment provider.

### Special payment cases

- **Closed or expired payment method:** escalate; a reviewer offers store credit or bank transfer.
- **Gift purchases:** the refund goes to the purchaser's payment method. A recipient with a gift receipt receives store credit.
- **Multi-item orders and bundles:** refund only the returned items, calculated from their share of the order total.

## 8. Return shipping and restocking fees

| Case | Return shipping paid by | Restocking fee |
| --- | --- | --- |
| Change of mind | Customer | Up to 10%, only if disclosed at purchase and the product category qualifies |
| `wrong_item`, `damaged`, `defective`, `not_as_described`, fulfillment error | Retailer | None |
| `quality`, `arrived_late` (approved) | Retailer | None |

A restocking fee is never applied automatically. The system first confirms that the product and the transaction qualify.

## 9. Human review and escalation

A human reviewer decides all of these cases within 2 business days **(demo assumption)**, or 3 business days for refunds above the high-value threshold.

| Situation | Action |
| --- | --- |
| Late request, any reason except change of mind | Human review |
| Product condition disputed | Human review |
| Refund above $500 per return request **(demo assumption)** | Human review |
| Suspicious return behavior or possible product substitution | Human review |
| Missing or conflicting evidence | Human review |
| Defect claim on a non-returnable product | Human review |
| Refund calculation cannot be verified | Human review |
| Order and product details cannot be reconciled | Human review |
| Discretionary partial refund (Section 11) | Human review |
| Two policy rules conflict, or an unusual exception is requested | Human review |

The reviewer can approve or deny exceptions. Each exception records an explanation, the reviewer's identity and the policy version.

## 10. Suspicious and potentially fraudulent returns

The indicators below are risk signals, not proof. They route a case to human review. They never justify automatic denial, and the system never accuses a customer of fraud.

| Indicator | Demo threshold |
| --- | --- |
| Return requests from one account | 3 or more in 30 days |
| Damage or missing-item claims from one account | 2 or more in 90 days |
| Returned value compared with purchases | Above 50% over 90 days, with at least 3 orders |
| High-value refund with insufficient evidence | Above the $500 threshold |
| Photo inconsistent with the customer's description | Any |
| Possible product substitution | Any |
| Related order or payment patterns across accounts | Any |

A high return rate, a new account, a suspicious photo or missing image metadata does not by itself establish fraud.

## 11. Duplicate requests and partial refunds

### Duplicates

- One order item can be refunded once.
- If a request is already approved or completed for the same order item, block the new request from automatic processing.
- If a request is pending, link the new one to the existing case or escalate.
- A denied request is reconsidered only when the customer supplies new relevant evidence.

### Partial refunds

| Case | Handling |
| --- | --- |
| Only some items in an order are returned | Calculated automatically from transaction records |
| Verified pricing discrepancy | Calculated automatically from transaction records |
| Minor defect that does not prevent use | Human reviewer approves the amount |
| Any other discretionary reduction | Human reviewer approves the amount |

The AI system never invents or negotiates a refund amount.

## 12. Customer communication and appeals

- Every decision message states the outcome, the reason in plain language and the next step.
- Denials cite the specific policy rule and never imply fraud.
- A customer may appeal one denial within 14 days **(demo assumption)**. A human reviewer decides the appeal.
- Customer photos and evidence are kept for 180 days after the case closes, then deleted **(demo assumption)**.

## 13. Decision engine requirements

### Evaluation order

ReturnGuard evaluates each request in this order and stops at the first step that ends the case.

1. Select the policy version in force on the request date.
2. Check for duplicates. Block or link as needed.
3. Verify order, delivery and payment data. If it cannot be verified, escalate.
4. Check the non-returnable categories. Escalate any exception claim.
5. Check the return window. Apply the late-request rules.
6. Check reason eligibility and product condition.
7. Check evidence. If it is missing or conflicting, escalate.
8. Check fraud risk signals. If any fire, escalate.
9. Check the high-value threshold. If exceeded, escalate.
10. Calculate the refund with deterministic business logic.
11. Record the decision.

### Decision principles

1. Check policy eligibility before approving any refund.
2. Verified order and payment data outranks customer assumptions.
3. Missing information is never evidence of a violation.
4. Conflicting evidence triggers human review.
5. Fraud signals alone never justify rejection.
6. Refund amounts come from deterministic logic, never from an LLM.
7. Every exception records its explanation and reviewer identity.
8. Every decision records the policy version used.

### Decision record

Each decision stores the request ID, order item ID, reason code, outcome (approve, deny, block or escalate), the policy rule that decided it, the risk signals that fired, the refund amount and its inputs, the policy version, a timestamp and, for exceptions, the reviewer.

### Versioning

Each policy has a unique ID and version. A change creates a new version with its effective date. Earlier versions stay available for historical decisions. The engine chooses the version using the business's configured effective-date rules.

## 14. Configurable parameters

Only the Customer Operations administrator role can change these values, and every change is logged.

| Parameter | Demo value |
| --- | --- |
| Standard return window | 30 days |
| Electronics change-of-mind window | 15 days |
| Late-delivery eligibility threshold | 3 days |
| Late-delivery shipping refund threshold | 7 days |
| High-value review threshold | $500 per return request |
| Maximum restocking fee | 10% |
| Inspection time | 5 business days |
| Ship-back deadline after approval | 10 days |
| Human review time | 2 business days (3 for high value) |
| Appeal window | 14 days |
| Evidence retention | 180 days after case closure |
| Fraud thresholds | As listed in Section 10 |

## 15. Out of scope for this demo

This sample policy does not cover statutory consumer rights or cooling-off periods in any country, tax treatment of refunds, chargeback handling or carrier claims. A production policy needs legal review for each market where the retailer sells.

## 16. Test scenarios

Run these cases against the engine before the demo.

| Scenario | Expected outcome | Section |
| --- | --- | --- |
| Damaged item, photo supplied, day 10 | Approve; retailer pays shipping | 1, 8 |
| Damaged laptop, day 20 | Approve; 30-day window applies | 2 |
| Damaged item, no photo | Escalate, never auto-reject | 5 |
| Change of mind, unopened, day 12 | Approve; customer pays shipping | 1, 8 |
| Change of mind, electronics, day 20 | Deny as late; appeal available | 2 |
| Change of mind, item shows use | Deny; offer defect review if it failed in normal use | 3 |
| Wrong item, photo supplied | Approve; free return, no restocking fee | 1, 8 |
| Defective item above $500 | Escalate for the high-value rule | 9 |
| Defective item, day 40 | Escalate as a late exception | 2 |
| Fresh food, change of mind | Deny; non-returnable | 4 |
| Fresh food arrived damaged | Escalate for individual review | 4 |
| Item delivered 2 days late | Not eligible | 1 |
| Item delivered 8 days late, customer no longer needs it | Approve; item and original shipping refunded | 1, 7 |
| Second request for an item already refunded | Block from automatic processing | 11 |
| Account with 3 returns in 30 days | Route to review as a risk signal, no accusation | 10 |

## 17. Change log

| Version | Date | Change |
| --- | --- | --- |
| 1.1 | 2026-11-09 | Resolved late-request, electronics-window, day-counting and partial-refund conflicts. Added numeric thresholds, evidence minimums, return process, communication rules, decision engine requirements and test scenarios. |
| 1.0 | 2026-10-30 | Initial sample policy. |
