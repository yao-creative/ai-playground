from domain import Document


RAW_DOCUMENTS = [
    {
        "id": "doc-001",
        "title": "Remote Work Policy",
        "category": "hr",
        "text": "Employees may work remotely up to three days per week with manager approval. Core collaboration hours are 10:00 to 15:00 local time. Security training must be completed before accessing internal systems from personal networks.",
    },
    {
        "id": "doc-002",
        "title": "Annual Leave Guidelines",
        "category": "hr",
        "text": "Full-time employees receive 18 days of annual leave each calendar year. Leave requests longer than five consecutive working days should be submitted at least two weeks in advance. Unused leave may be carried forward up to five days into the next year.",
    },
    {
        "id": "doc-003",
        "title": "Expense Reimbursement Rules",
        "category": "finance",
        "text": "Meals under 40 USD do not require pre-approval. Hotel bookings above 180 USD per night require director approval unless travel occurs during a peak event period. Expense claims must include receipts and be submitted within 30 days of purchase.",
    },
    {
        "id": "doc-004",
        "title": "Laptop Replacement Standard",
        "category": "it",
        "text": "Engineering laptops are eligible for replacement every 36 months. Early replacement is permitted for repeated hardware failures, battery health below 70 percent, or inability to run required local development tooling.",
    },
    {
        "id": "doc-005",
        "title": "Incident Severity Matrix",
        "category": "ops",
        "text": "A Sev-1 incident means customer-facing downtime affecting more than 50 percent of active users or any confirmed data loss event. Sev-2 covers major degradation with a workaround. Sev-3 covers minor feature impact without broad business disruption.",
    },
    {
        "id": "doc-006",
        "title": "Customer Support SLA",
        "category": "support",
        "text": "Priority enterprise tickets receive a first response within one hour during business hours. Standard tickets receive a first response within eight business hours. Bug reports linked to production outages are escalated immediately to engineering.",
    },
    {
        "id": "doc-007",
        "title": "Product Launch Checklist",
        "category": "product",
        "text": "Before launch, every feature must complete QA sign-off, documentation review, analytics event verification, and rollback plan approval. Features touching billing also require finance review and a staged release plan.",
    },
    {
        "id": "doc-008",
        "title": "Data Retention Policy",
        "category": "security",
        "text": "Application logs are retained for 90 days. Support chat transcripts are retained for 12 months. Deleted customer files remain in backup snapshots for up to 30 days before permanent removal.",
    },
    {
        "id": "doc-009",
        "title": "Engineering On-Call Expectations",
        "category": "engineering",
        "text": "Primary on-call engineers must acknowledge pager alerts within 10 minutes and begin triage within 15 minutes. If no acknowledgment occurs, the alert escalates automatically to the secondary on-call engineer and then to the engineering manager.",
    },
    {
        "id": "doc-010",
        "title": "Office Access Procedures",
        "category": "facilities",
        "text": "Employees may access the office from 07:00 to 22:00 using their badge. Guests must be registered by a host before arrival and remain escorted at all times outside reception and meeting rooms.",
    },
    {
        "id": "doc-011",
        "title": "Hiring Interview Rubric",
        "category": "recruiting",
        "text": "Interviewers score candidates across problem solving, communication, technical depth, and role alignment on a scale from 1 to 4. Written feedback should be submitted within 24 hours and must include at least two evidence-based observations.",
    },
    {
        "id": "doc-012",
        "title": "Vendor Review Requirements",
        "category": "procurement",
        "text": "New vendors handling customer data must complete a security questionnaire, sign a data processing agreement, and provide evidence of encryption at rest and in transit. Annual renewals require reassessment if risk exposure changes.",
    },
]



def build_documents() -> list[Document]:
    return [Document(**raw_document) for raw_document in RAW_DOCUMENTS]
