import logging

logger = logging.getLogger(__name__)

GROUNDING_INSTRUCTION = """
You are acting as an AI Agent under strict safety and grounding guardrails.
Analyze the provided context documents carefully. Follow these core instructions:
1. Base all risk statements, recommendations, and contingency plans EXCLUSIVELY on the provided context evidence snippets.
2. If the context documents are empty, weak, or do not contain sufficient evidence to answer the question or justify a risk score, respond with exactly "INSUFFICIENT EVIDENCE" and do not invent any details.
3. NEVER invent supplier capacity, pricing, lead times, safety stocks, contractual obligations, or availability. Use only coordinates, ports, and values provided in the input profiles.
4. Include source links (source_url) and source names (source_name) for all evidence cited in your response.
5. All contingency recommendations must be marked clearly as DRAFTS.
"""

def inject_grounding_rules(system_prompt: str) -> str:
    """
    Appends grounding instructions to any agent's system prompt.
    """
    return f"{system_prompt}\n\n=== GROUNDING & AUDITABILITY POLICY ===\n{GROUNDING_INSTRUCTION}"
