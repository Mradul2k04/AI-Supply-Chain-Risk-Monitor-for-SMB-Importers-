# Supply Chain Risk Monitor - Policy & Guardrails

## Data and Privacy
1. Collect only supplier data required for risk monitoring.
2. Keep supplier lists, purchase volumes, and internal performance data private.
3. Use separate tenant/workspace filters in PostgreSQL and ChromaDB.
4. Do not store secrets, API keys, or credit-report contents in ChromaDB.
5. Respect source licenses, rate limits, terms of use, and data-retention policies.

## Risk Interpretation
1. Label outputs as "risk signals" rather than confirmed facts unless independently verified.
2. Display source, date, region, confidence, and retrieval time with every alert.
3. Never generate a financial-health score when there is insufficient lawful data.
4. Do not make causal claims from a single news article or unverified source.
5. Use transparent weighted scoring; show the signals contributing to a score.

## Contingency Planning
1. Treat all contingency plans as drafts.
2. Require human approval for supplier-switch, purchase-volume, inventory, or logistics decisions.
3. Only use approved alternate suppliers.
4. Never invent supplier capacity, pricing, lead time, contractual obligations, or availability.
5. State assumptions and uncertainty in every recommended action.

## LLM and Agent Controls
1. Require RAG evidence for every generated risk explanation.
2. Block unsupported claims and force "insufficient evidence" when retrieval is weak.
3. Use Pydantic validation for all graph-node outputs.
4. Add LangGraph human-review interrupts before high-impact actions.
5. Log agent inputs, sources, output versions, and reviewer decisions for auditability.
