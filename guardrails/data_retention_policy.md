# Data Retention & Deletion Policy

## Scope
This policy covers relational database records (suppliers, risk assessments, contingency plans, audit logs) and ChromaDB vector embeddings.

## Retention Periods
1. **Supplier Profiles**: Retained until manually deleted by users or when contract terminates.
2. **Risk Events**: Ingested feed snapshots and risk events are kept for 90 days.
3. **Supplier Risk Assessments**: Kept for 1 year for trend tracking.
4. **Contingency Plans**: Kept for 2 years or until supplier contract changes.
5. **Audit Logs**: Retained for 5 years to meet audit and compliance criteria.

## Deletion Protocol
When a deletion request is executed:
- SQL DB records are hard deleted or soft deleted based on operational flags.
- Related records in the ChromaDB collections (`supplier_profiles`, `risk_events`) are queried by `supplier_id` metadata filter and deleted.
