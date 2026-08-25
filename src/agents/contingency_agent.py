import os
import logging
from typing import List, Optional
from langchain_core.prompts import PromptTemplate
from src.config.settings import settings
from src.schemas.supplier import Supplier
from src.schemas.risk_event import RiskEvent
from src.schemas.contingency import ContingencyPlan
from src.rag.retriever import retrieve_risk_evidence
from guardrails.prompt_rules import inject_grounding_rules
from guardrails.validators import validate_contingency_plan_rules

logger = logging.getLogger(__name__)

def generate_fallback_plan(
    supplier: Supplier,
    trigger_event: RiskEvent,
    playbook_content: str
) -> ContingencyPlan:
    """Generates a structured contingency plan using local templates."""
    logger.info("Using rules-based local generator for contingency plan.")
    
    # Select alternative supplier from approved list
    alt_supplier = None
    if supplier.approved_alternate_supplier_ids:
        alt_supplier = supplier.approved_alternate_supplier_ids[0]
        
    # Standard recommendations based on risk type
    action = f"Mitigation Action Plan (DRAFT):\nDue to {trigger_event.title} in {trigger_event.region}:\n"
    
    if trigger_event.risk_type == "port_disruption":
        action += (
            f"1. Divert immediate shipments bound for {supplier.primary_port or 'primary port'} to backup channels.\n"
            f"2. Shift 40% of cargo volume to air freight if lead time margins are critical.\n"
            f"3. Coordinate with logistics teams to increase safety stock margins."
        )
        volume_shift = 40.0
        lead_time_delta = 14
    elif trigger_event.risk_type == "weather":
        action += (
            f"1. Freeze outbound cargo processing in affected regions.\n"
            f"2. Draw safety stock reserves to cover manufacturing runs.\n"
            f"3. Initiate backup POs with alternate suppliers to maintain continuity."
        )
        volume_shift = 30.0
        lead_time_delta = 10
    elif trigger_event.risk_type == "financial":
        action += (
            f"1. Halt advance payments for future purchase orders.\n"
            f"2. Audit financial solvency of the vendor.\n"
            f"3. Establish contracts with backup suppliers to protect dependency exposure."
        )
        volume_shift = 50.0
        lead_time_delta = 7
    else:
        action += (
            f"1. Monitor shipment lane bottlenecks daily.\n"
            f"2. Advise logistics partners of potential delay hazards."
        )
        volume_shift = 10.0
        lead_time_delta = 3
        
    assumptions = [
        "Alternative supplier has available open manufacturing capacity.",
        "Freight capacity is securable on secondary routes within 48 hours.",
        f"Internal safety stocks are sufficient to absorb {lead_time_delta} days of delay."
    ]
    
    evidence_links = [
        trigger_event.source_url,
        "internal://playbooks/" + trigger_event.risk_type
    ]
    
    return ContingencyPlan(
        supplier_id=supplier.supplier_id,
        trigger_event_id=trigger_event.event_id,
        recommended_action=action,
        alternate_supplier_id=alt_supplier,
        proposed_volume_shift_percent=volume_shift,
        estimated_lead_time_delta_days=lead_time_delta,
        assumptions=assumptions,
        evidence_links=evidence_links,
        approval_status="draft"
    )

def run_contingency_planner_agent(
    supplier: Supplier,
    trigger_event: RiskEvent
) -> ContingencyPlan:
    """
    Orchestrates the retrieval of matching playbooks and drafts a contingency plan.
    """
    logger.info(f"Drafting contingency plan for supplier {supplier.supplier_id} due to event {trigger_event.event_id}")
    
    # 1. Retrieve playbook evidence from ChromaDB
    playbooks = retrieve_risk_evidence(
        query=f"{trigger_event.risk_type} disruption backup supply routing plan",
        collection_name="contingency_playbooks",
        filters={"risk_type": trigger_event.risk_type},
        limit=1
    )
    
    playbook_content = playbooks[0]["content"] if playbooks else "No specific playbook instructions found in knowledge base."
    
    llm_provider = settings.LLM_PROVIDER
    llm_model = settings.LLM_MODEL or "groq/compound"
    
    llm = None
    try:
        groq_key = settings.GROQ_API_KEY
        if groq_key:
            logger.info(f"Initializing ChatGroq client with model: {llm_model}")
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                temperature=0.1,
                groq_api_key=groq_key,
                model_name=llm_model
            )
        else:
            logger.warning("GROQ_API_KEY not set. Falling back to local rule-based planner.")
    except Exception as e:
        logger.warning(f"Failed to initialize ChatGroq ({e}). Using local rule-based fallback plan generator.")

        
    if not llm:
        return generate_fallback_plan(supplier, trigger_event, playbook_content)
        
    try:
        # Construct grounded LLM query using LangChain
        logger.info(f"Calling LLM ({llm_provider}) to draft contingency plan...")
        
        system_prompt = "You are a professional supply chain risk manager. Draft a structured contingency plan."
        system_prompt = inject_grounding_rules(system_prompt)
        
        prompt_tmpl = PromptTemplate.from_template(
            """
            {system_prompt}
            
            Supplier Profile:
            - Name: {supplier_name}
            - ID: {supplier_id}
            - Primary Port: {primary_port}
            - Approved Alternates: {alternates}
            
            Risk Event:
            - Title: {event_title}
            - Severity: {event_severity}
            - Description: {event_desc}
            
            Playbook Evidence:
            {playbook_evidence}
            
            Format your output strictly as a valid JSON object matching these keys:
            - recommended_action: text description of the actions to take.
            - alternate_supplier_id: the ID of the alternate supplier (must be from the approved list, or null if none fit).
            - proposed_volume_shift_percent: float percentage value (between 0.0 and 100.0) or null.
            - estimated_lead_time_delta_days: integer delay estimate in days or null.
            - assumptions: list of text assumptions.
            - evidence_links: list of strings citing the sources.
            """
        )
        
        formatted_prompt = prompt_tmpl.format(
            system_prompt=system_prompt,
            supplier_name=supplier.name,
            supplier_id=supplier.supplier_id,
            primary_port=supplier.primary_port or "N/A",
            alternates=supplier.approved_alternate_supplier_ids,
            event_title=trigger_event.title,
            event_severity=trigger_event.severity,
            event_desc=str(trigger_event.evidence_text or "")[:1000],
            playbook_evidence=str(playbook_content or "")[:1000]
        )
        
        # Execute LLM call with rate-limit backoff retry loop
        import time
        max_retries = 3
        backoff_delay = 2.0
        response_obj = None

        for attempt in range(1, max_retries + 1):
            try:
                response_obj = llm.invoke(formatted_prompt)
                break
            except Exception as llm_err:
                err_str = str(llm_err).lower()
                if ("429" in err_str or "rate limit" in err_str or "too many requests" in err_str) and attempt < max_retries:
                    logger.warning(f"Groq 429 Rate Limit hit on attempt {attempt}/{max_retries}. Retrying in {backoff_delay}s...")
                    time.sleep(backoff_delay)
                    backoff_delay *= 2.0
                else:
                    raise llm_err

        response_text = response_obj.content if hasattr(response_obj, "content") else response_obj
            
        # Strip markdown json wrappers if present
        clean_json = str(response_text).strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1]
            if clean_json.startswith("json"):
                clean_json = clean_json[4:]
        clean_json = clean_json.strip()
        
        # Parse output JSON
        import json
        plan_dict = json.loads(clean_json)
        
        # Sanitize evidence_links so every item is a string URL
        raw_evidence = plan_dict.get("evidence_links", [trigger_event.source_url])
        sanitized_evidence = []
        if isinstance(raw_evidence, list):
            for item in raw_evidence:
                if isinstance(item, dict):
                    sanitized_evidence.append(item.get("source_url") or item.get("url") or str(item))
                elif isinstance(item, str):
                    sanitized_evidence.append(item)
                else:
                    sanitized_evidence.append(str(item))
        else:
            sanitized_evidence = [trigger_event.source_url]
            
        # Sanitize assumptions so every item is a string
        raw_assumptions = plan_dict.get("assumptions", [])
        sanitized_assumptions = [str(x) if not isinstance(x, str) else x for x in raw_assumptions] if isinstance(raw_assumptions, list) else []

        plan = ContingencyPlan(
            supplier_id=supplier.supplier_id,
            trigger_event_id=trigger_event.event_id,
            recommended_action=str(plan_dict.get("recommended_action", "Alert: Contingency actions not drafted.")),
            alternate_supplier_id=plan_dict.get("alternate_supplier_id"),
            proposed_volume_shift_percent=float(plan_dict["proposed_volume_shift_percent"]) if plan_dict.get("proposed_volume_shift_percent") is not None else None,
            estimated_lead_time_delta_days=int(plan_dict["estimated_lead_time_delta_days"]) if plan_dict.get("estimated_lead_time_delta_days") is not None else None,
            assumptions=sanitized_assumptions,
            evidence_links=sanitized_evidence,
            approval_status="draft"
        )
        
        # Verify guardrails
        errors = validate_contingency_plan_rules(plan, supplier.approved_alternate_supplier_ids)
        if errors:
            logger.warning(f"Guardrail violations: {errors}. Reverting to safe default fallback.")
            return generate_fallback_plan(supplier, trigger_event, playbook_content)
            
        return plan
        
    except Exception as e:
        logger.error(f"Error calling LLM provider '{llm_provider}' for contingency planning: {e}. Reverting to rule-based fallback.")
        return generate_fallback_plan(supplier, trigger_event, playbook_content)

