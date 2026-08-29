import os
import time
import logging
import threading
from typing import List, Optional, Dict, Tuple
from langchain_core.prompts import PromptTemplate
from src.config.settings import settings
from src.schemas.supplier import Supplier
from src.schemas.risk_event import RiskEvent
from src.schemas.contingency import ContingencyPlan
from src.rag.retriever import retrieve_risk_evidence
from guardrails.prompt_rules import inject_grounding_rules
from guardrails.validators import validate_contingency_plan_rules

logger = logging.getLogger(__name__)

# Global cache and thread-safe throttling primitives
_PLAN_CACHE: Dict[Tuple[str, str], ContingencyPlan] = {}
_LAST_GROQ_CALL_TIME: float = 0.0
MIN_GROQ_CALL_INTERVAL_SEC: float = 2.5
_GROQ_THROTTLE_LOCK = threading.Lock()

try:
    import groq
    GroqRateLimitError = groq.RateLimitError
except ImportError:
    GroqRateLimitError = Exception

def clear_plan_cache():
    """Clears in-memory contingency plan cache."""
    global _PLAN_CACHE
    _PLAN_CACHE.clear()
    logger.info("Contingency plan cache cleared.")

def _throttle_groq_requests():
    """Enforces thread-safe minimum interval between consecutive Groq API calls across all concurrent sessions."""
    global _LAST_GROQ_CALL_TIME
    with _GROQ_THROTTLE_LOCK:
        now = time.time()
        elapsed = now - _LAST_GROQ_CALL_TIME
        if elapsed < MIN_GROQ_CALL_INTERVAL_SEC:
            wait_time = MIN_GROQ_CALL_INTERVAL_SEC - elapsed
            logger.info(f"Throttling Groq request: sleeping for {wait_time:.2f}s to stay under rate limits...")
            time.sleep(wait_time)
        _LAST_GROQ_CALL_TIME = time.time()

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

def run_contingency_planner_agent_batch(
    supplier: Supplier,
    trigger_events: List[RiskEvent],
    force_refresh: bool = False
) -> List[ContingencyPlan]:
    """
    Orchestrates contingency plan drafting for all risk events affecting a supplier in a SINGLE LLM call.
    Uses caching by (supplier_id, trigger_event_id) to eliminate redundant LLM calls.
    """
    if not trigger_events:
        return []

    plans_by_event_id: Dict[str, ContingencyPlan] = {}
    uncached_events: List[RiskEvent] = []

    # 1. Check in-memory cache & database for pre-existing plans
    for event in trigger_events:
        cache_key = (supplier.supplier_id, event.event_id)
        if not force_refresh:
            if cache_key in _PLAN_CACHE:
                logger.info(f"Cache HIT: Returning cached contingency plan for supplier '{supplier.supplier_id}' and event '{event.event_id}'.")
                plans_by_event_id[event.event_id] = _PLAN_CACHE[cache_key]
                continue

            try:
                from src.services.database import SessionLocal, DBContingencyPlan
                db_sess = SessionLocal()
                try:
                    db_plan = db_sess.query(DBContingencyPlan).filter(
                        DBContingencyPlan.supplier_id == supplier.supplier_id,
                        DBContingencyPlan.trigger_event_id == event.event_id
                    ).first()
                    if db_plan:
                        cached_plan = ContingencyPlan(
                            supplier_id=db_plan.supplier_id,
                            trigger_event_id=db_plan.trigger_event_id,
                            recommended_action=db_plan.recommended_action,
                            alternate_supplier_id=db_plan.alternate_supplier_id,
                            proposed_volume_shift_percent=db_plan.proposed_volume_shift_percent,
                            estimated_lead_time_delta_days=db_plan.estimated_lead_time_delta_days,
                            assumptions=db_plan.assumptions or [],
                            evidence_links=db_plan.evidence_links or [],
                            approval_status=db_plan.approval_status or "draft"
                        )
                        _PLAN_CACHE[cache_key] = cached_plan
                        plans_by_event_id[event.event_id] = cached_plan
                        logger.info(f"DB HIT: Loaded existing plan for supplier '{supplier.supplier_id}' and event '{event.event_id}' from DB.")
                        continue
                finally:
                    db_sess.close()
            except Exception as db_err:
                logger.warning(f"DB lookup warning during plan cache check: {db_err}")

        uncached_events.append(event)

    if not uncached_events:
        return [plans_by_event_id[e.event_id] for e in trigger_events if e.event_id in plans_by_event_id]

    logger.info(f"Drafting batch contingency plans for supplier '{supplier.supplier_id}' across {len(uncached_events)} risk events in 1 LLM call.")

    # 2. Retrieve playbooks for uncached events
    event_contexts = []
    playbook_contents_by_event = {}

    for idx, event in enumerate(uncached_events, 1):
        playbooks = retrieve_risk_evidence(
            query=f"{event.risk_type} disruption backup supply routing plan",
            collection_name="contingency_playbooks",
            filters={"risk_type": event.risk_type},
            limit=1
        )
        playbook_content = playbooks[0]["content"] if playbooks else "No specific playbook instructions found in knowledge base."
        playbook_contents_by_event[event.event_id] = playbook_content

        safe_desc = str(event.evidence_text or "")[:800]
        safe_pb = str(playbook_content or "")[:800]

        event_contexts.append(
            f"Risk Event {idx}:\n"
            f"- Event ID: {event.event_id}\n"
            f"- Title: {event.title}\n"
            f"- Risk Type: {event.risk_type}\n"
            f"- Severity: {event.severity}\n"
            f"- Region: {event.region}\n"
            f"- Description: {safe_desc}\n"
            f"- Playbook Evidence: {safe_pb}\n"
        )

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

    # Fallback if LLM unavailable
    if not llm:
        for event in uncached_events:
            pb = playbook_contents_by_event.get(event.event_id, "")
            fb = generate_fallback_plan(supplier, event, pb)
            _PLAN_CACHE[(supplier.supplier_id, event.event_id)] = fb
            plans_by_event_id[event.event_id] = fb
        return [plans_by_event_id[e.event_id] for e in trigger_events if e.event_id in plans_by_event_id]

    try:
        from langchain_core.messages import SystemMessage, HumanMessage

        system_prompt = "You are a professional supply chain risk manager. Draft structured contingency plans for risk events."
        system_prompt = inject_grounding_rules(system_prompt)

        events_str = "\n".join(event_contexts)
        user_prompt = f"""
Supplier Profile:
- Name: {supplier.name}
- ID: {supplier.supplier_id}
- Primary Port: {supplier.primary_port or 'N/A'}
- Approved Alternates: {supplier.approved_alternate_supplier_ids}

Risk Events to address ({len(uncached_events)} events):
{events_str}

Format your output strictly as a JSON ARRAY of objects (one object per risk event), where each object matches these keys:
- trigger_event_id: the matching Event ID string.
- recommended_action: text description of the actions to take.
- alternate_supplier_id: the ID of the alternate supplier (must be from the approved list, or null if none fit).
- proposed_volume_shift_percent: float percentage value (between 0.0 and 100.0) or null.
- estimated_lead_time_delta_days: integer delay estimate in days or null.
- assumptions: list of text assumptions.
- evidence_links: list of strings citing the sources.
"""

        # Construct clean message list (ensures NO context or history leakage between invocations)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # Log full actual request payload sent to Groq
        import json
        serialized_payload = json.dumps([{"role": m.type, "content": m.content} for m in messages], indent=2)
        logger.info(
            f"--- GROQ REQUEST FULL PAYLOAD START ---\n"
            f"Model: {llm_model} | Message Count: {len(messages)} | Total Payload Chars: {len(serialized_payload)}\n"
            f"Payload JSON:\n{serialized_payload}\n"
            f"--- GROQ REQUEST FULL PAYLOAD END ---"
        )

        _throttle_groq_requests()

        max_retries = 3
        backoff_delay = 2.0
        response_obj = None

        for attempt in range(1, max_retries + 1):
            try:
                response_obj = llm.invoke(messages)
                break
            except Exception as llm_err:
                err_str = str(llm_err).lower()
                is_413_payload_too_large = (
                    "413" in err_str or
                    "request entity too large" in err_str or
                    "payload too large" in err_str or
                    "request_too_large" in err_str
                )
                if is_413_payload_too_large:
                    fallback_model = "groq/compound-mini" if llm_model != "groq/compound-mini" else "openai/gpt-oss-120b"
                    logger.warning(
                        f"Groq 413 Request Entity Too Large hit on model '{llm_model}'. "
                        f"Automatically retrying request with non-restricted model '{fallback_model}'..."
                    )
                    from langchain_groq import ChatGroq
                    fallback_llm = ChatGroq(
                        temperature=0.1,
                        groq_api_key=groq_key,
                        model_name=fallback_model
                    )
                    response_obj = fallback_llm.invoke(messages)
                    break

                is_rate_limit = (
                    isinstance(llm_err, GroqRateLimitError) or
                    "429" in err_str or
                    "rate limit" in err_str or
                    "rate_limit_exceeded" in err_str or
                    "too many requests" in err_str
                )
                if is_rate_limit and attempt < max_retries:
                    logger.warning(
                        f"Groq RateLimitError hit on attempt {attempt}/{max_retries}. "
                        f"Retrying with exponential backoff in {backoff_delay}s..."
                    )
                    time.sleep(backoff_delay)
                    backoff_delay *= 2.0
                else:
                    logger.error(f"Groq batch call failed on attempt {attempt}/{max_retries}: {llm_err}")
                    raise llm_err

        # Log Groq rate limit / quota metadata if returned in response headers/metadata
        if hasattr(response_obj, "response_metadata") and isinstance(response_obj.response_metadata, dict):
            metadata = response_obj.response_metadata
            headers = metadata.get("headers", {}) if isinstance(metadata.get("headers"), dict) else {}
            rem_req = headers.get("x-ratelimit-remaining-requests") or metadata.get("x-ratelimit-remaining-requests") or "N/A"
            rem_tok = headers.get("x-ratelimit-remaining-tokens") or metadata.get("x-ratelimit-remaining-tokens") or "N/A"
            reset_req = headers.get("x-ratelimit-reset-requests") or metadata.get("x-ratelimit-reset-requests") or "N/A"
            logger.info(f"[GROQ QUOTA STATUS] Remaining Requests: {rem_req} | Remaining Tokens: {rem_tok} | Reset Requests: {reset_req}")

        response_text = response_obj.content if hasattr(response_obj, "content") else str(response_obj)

        clean_json = response_text.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1]
            if clean_json.startswith("json"):
                clean_json = clean_json[4:]
        clean_json = clean_json.strip()

        # Extract JSON array substring between first [ and last ]
        start_idx = clean_json.find("[")
        end_idx = clean_json.rfind("]")
        
        parsed_array = []
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            raw_array_str = clean_json[start_idx:end_idx + 1]
            try:
                parsed_array = json.loads(raw_array_str)
            except Exception as parse_err:
                logger.warning(f"Failed to parse LLM JSON array response ({parse_err}). Raw output: '{response_text}'.")

        # Map parsed JSON objects by trigger_event_id
        parsed_by_event_id = {}
        if isinstance(parsed_array, list):
            for item in parsed_array:
                if isinstance(item, dict) and "trigger_event_id" in item:
                    parsed_by_event_id[item["trigger_event_id"]] = item

        for event in uncached_events:
            cache_key = (supplier.supplier_id, event.event_id)
            plan_dict = parsed_by_event_id.get(event.event_id)
            pb = playbook_contents_by_event.get(event.event_id, "")

            if not plan_dict:
                logger.warning(f"No valid LLM response object for event '{event.event_id}'. Reverting to local fallback plan.")
                fb = generate_fallback_plan(supplier, event, pb)
                _PLAN_CACHE[cache_key] = fb
                plans_by_event_id[event.event_id] = fb
                continue

            raw_evidence = plan_dict.get("evidence_links", [event.source_url])
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
                sanitized_evidence = [event.source_url]

            raw_assumptions = plan_dict.get("assumptions", [])
            sanitized_assumptions = [str(x) if not isinstance(x, str) else x for x in raw_assumptions] if isinstance(raw_assumptions, list) else []

            plan = ContingencyPlan(
                supplier_id=supplier.supplier_id,
                trigger_event_id=event.event_id,
                recommended_action=str(plan_dict.get("recommended_action", "Alert: Contingency actions not drafted.")),
                alternate_supplier_id=plan_dict.get("alternate_supplier_id"),
                proposed_volume_shift_percent=float(plan_dict["proposed_volume_shift_percent"]) if plan_dict.get("proposed_volume_shift_percent") is not None else None,
                estimated_lead_time_delta_days=int(plan_dict["estimated_lead_time_delta_days"]) if plan_dict.get("estimated_lead_time_delta_days") is not None else None,
                assumptions=sanitized_assumptions,
                evidence_links=sanitized_evidence,
                approval_status="draft"
            )

            errors = validate_contingency_plan_rules(plan, supplier.approved_alternate_supplier_ids)
            if errors:
                logger.warning(f"Guardrail violations for event '{event.event_id}': {errors}. Reverting to safe default fallback.")
                fb = generate_fallback_plan(supplier, event, pb)
                _PLAN_CACHE[cache_key] = fb
                plans_by_event_id[event.event_id] = fb
            else:
                _PLAN_CACHE[cache_key] = plan
                plans_by_event_id[event.event_id] = plan

    except Exception as e:
        logger.error(f"Error calling LLM provider '{llm_provider}' for batch contingency planning: {e}. Reverting to rule-based fallback for uncached events.")
        for event in uncached_events:
            cache_key = (supplier.supplier_id, event.event_id)
            pb = playbook_contents_by_event.get(event.event_id, "")
            fb = generate_fallback_plan(supplier, event, pb)
            _PLAN_CACHE[cache_key] = fb
            plans_by_event_id[event.event_id] = fb

    return [plans_by_event_id[e.event_id] for e in trigger_events if e.event_id in plans_by_event_id]


def run_contingency_planner_agent(
    supplier: Supplier,
    trigger_event: RiskEvent,
    force_refresh: bool = False
) -> ContingencyPlan:
    """
    Backward-compatible single event wrapper around run_contingency_planner_agent_batch.
    """
    plans = run_contingency_planner_agent_batch(supplier, [trigger_event], force_refresh=force_refresh)
    if plans:
        return plans[0]
    return generate_fallback_plan(supplier, trigger_event, "")




