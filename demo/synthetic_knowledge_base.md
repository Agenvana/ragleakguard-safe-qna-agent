# Agenvana Support Operations Handbook

**Classification:** Synthetic demonstration document  
**Purpose:** Test the RAGLeakGuard Safe Q&A ingestion gate and retrieval flow.  
**Data notice:** Every personal identifier in Appendix A is fictional or a
synthetic detector fixture. Never substitute real personal information.

## 1. Support coverage

The customer support desk operates Monday through Friday from **08:00 to
18:00 Canberra local time**, excluding Australian Capital Territory public
holidays.

Priority targets:

- **Priority 1:** acknowledge within **15 minutes** and begin continuous
  incident coordination.
- **Priority 2:** acknowledge within **4 business hours**.
- **Priority 3:** acknowledge within **1 business day**.

The after-hours service accepts Priority 1 security incidents only.

## 2. Refund and cancellation policy

Customers may request a full refund within **30 calendar days** of purchase
when they provide an order identifier. Approved refunds are returned to the
original payment method. Custom implementation work that has already been
delivered is not refundable.

## 3. Knowledge-base maintenance

The production knowledge base is refreshed every **Tuesday at 02:00 UTC**.
Emergency corrections may be published outside that window after approval by
the security lead and the support operations manager.

The retrieval-verification phrase for this demonstration document is:

**ORCHID-LANTERN-27**

## 4. Retention rules

- Customer chat transcripts are retained for **30 days**.
- Troubleshooting attachments are retained for **14 days**.
- Security incident records are retained for **24 months**.
- Tax invoices are retained for **7 years**.

At the end of each retention period, records must be deleted from the primary
system and included in the next backup-expiry cycle.

## 5. Security escalation

A suspected exposure of personal information must be classified as Priority 1.
The support agent must stop further ingestion, preserve metadata-only audit
evidence, notify the security lead, and open an incident record. Raw sensitive
values must not be copied into chat messages, tickets, or audit summaries.

## Appendix A — Synthetic sensitive-data test records

The records below exist only to verify that the ingestion gate refuses the
document until the user explicitly accepts the risk.

### US synthetic record

- Full name: Morgan Testwell
- Email: morgan.testwell@example.com
- Phone: +1 202 555 0156
- Date of birth: March 12, 1990
- US Social Security number: 123-45-6789
- Visa test card: 4111 1111 1111 1111
- Documentation IP address: 198.51.100.25
- Address: 200 Example Boulevard, Austin, Texas 78701

### Australian synthetic record

- Full name: Casey Hart
- Email: casey.hart@example.com
- Mobile: 0491 570 157
- Date of birth: 23 November 1992
- Tax File Number fixture: 000 000 000
- Australian Business Number fixture: 00 000 000 019
- Australian Company Number fixture: 000 000 019
- Medicare-style fixture: 20000000 0 0
- Address: 200 Example Circuit, Canberra ACT 2600

## Retrieval check

A successful answer grounded in this document should state that:

1. the verification phrase is ORCHID-LANTERN-27;
2. the knowledge base refresh occurs Tuesday at 02:00 UTC; and
3. a Priority 1 incident must be acknowledged within 15 minutes.
