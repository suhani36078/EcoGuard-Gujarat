"""
IBM Granite 4-h-small integration via watsonx.ai.
All methods retrieve structured data first, then pass it to Granite as context.
Granite generates grounded responses only — no invented facts.
Includes graceful fallback if Granite is unavailable.
"""

from __future__ import annotations

import os
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

WATSONX_API_KEY  = os.getenv("WATSONX_API_KEY", "")
WATSONX_AI_URL   = os.getenv("WATSONX_AI_URL", "")
GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-4-h-small")

# Medical language that must be stripped from output
_MEDICAL_PATTERNS = re.compile(
    r"(diagnos\w+|treat\w+|prescri\w+|symptom\w+|diseas\w+|medic\w+|clinic\w+|prognos\w+)",
    re.IGNORECASE,
)


def _scrub_medical(text: str) -> str:
    """Replace medical/diagnostic language with safe environmental framing."""
    return _MEDICAL_PATTERNS.sub("[health-assessment-removed]", text)


def _dict_to_context(data: Dict[str, Any], indent: int = 0) -> str:
    """Serialize a dict to a readable plain-text context block."""
    lines = []
    prefix = "  " * indent
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(_dict_to_context(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{prefix}{k}: {', '.join(str(i) for i in v[:10])}")
        else:
            lines.append(f"{prefix}{k}: {v}")
    return "\n".join(lines)


class GraniteService:
    """
    Wrapper around IBM watsonx.ai (ibm-watsonx-ai SDK).
    Lazy-initialises the model client on first use.
    """

    def __init__(self):
        self._client = None
        self._available = None  # None = not yet checked

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_client(self):
        if self._available is not None:
            return self._available
        try:
            from ibm_watsonx_ai import APIClient, Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            if not WATSONX_API_KEY or not WATSONX_AI_URL:
                raise ValueError("WATSONX_API_KEY or WATSONX_AI_URL not set")

            credentials = Credentials(
                url=WATSONX_AI_URL,
                api_key=WATSONX_API_KEY,
            )
            self._client = ModelInference(
                model_id=GRANITE_MODEL_ID,
                credentials=credentials,
            )
            self._available = True
            logger.info("GraniteService: IBM Granite client initialised (%s)", GRANITE_MODEL_ID)
        except Exception as exc:
            logger.warning("GraniteService: unavailable – %s", exc)
            self._available = False
        return self._available

    def _generate(self, prompt: str, max_tokens: int = 512) -> Optional[str]:
        """Call Granite and return the generated text, or None on failure."""
        if not self._init_client():
            return None
        try:
            params = {
                "max_new_tokens": max_tokens,
                "temperature": 0.2,
                "repetition_penalty": 1.1,
            }
            response = self._client.generate_text(prompt=prompt, params=params)
            text = response.strip() if isinstance(response, str) else str(response).strip()
            return _scrub_medical(text)
        except Exception as exc:
            logger.error("GraniteService._generate error: %s", exc)
            return None

    # ── Public API ────────────────────────────────────────────────────────────

    def explain_incident(self, incident_data: dict) -> str:
        """Return a plain-language explanation of an incident using structured data."""
        context = _dict_to_context(incident_data)
        prompt = (
            "You are an environmental compliance analyst. "
            "Using ONLY the structured data below, write a clear 2-3 sentence explanation "
            "of this pollution incident for a regulatory officer. "
            "Do not invent any values, limits, or factory names not present in the data.\n\n"
            f"INCIDENT DATA:\n{context}\n\n"
            "EXPLANATION:"
        )
        result = self._generate(prompt)
        if result:
            return result
        # Fallback
        title = incident_data.get("title", "Unknown Incident")
        severity = incident_data.get("severity", "unknown")
        factory = incident_data.get("factory_name", incident_data.get("factory_id", "Unknown Factory"))
        return (
            f"Incident '{title}' at {factory} classified as {severity} severity. "
            f"Status: {incident_data.get('status', 'unknown')}. "
            "AI narrative unavailable — review structured data above."
        )

    def explain_factory_risk(self, factory_data: dict, risk_data: dict) -> str:
        context = (
            f"FACTORY:\n{_dict_to_context(factory_data)}\n\n"
            f"RISK ASSESSMENT:\n{_dict_to_context(risk_data)}"
        )
        prompt = (
            "You are an industrial pollution risk assessor. "
            "Using ONLY the data below, explain in 3-4 sentences why this factory has its current risk score "
            "and what the primary contributing factors are. Do not invent readings or limits.\n\n"
            f"{context}\n\nRISK EXPLANATION:"
        )
        result = self._generate(prompt)
        if result:
            return result
        score = risk_data.get("overall_score", "N/A")
        level = risk_data.get("risk_level", "N/A")
        return (
            f"Factory risk level: {level} (score: {score}). "
            "AI explanation unavailable — see risk component breakdown for details."
        )

    def explain_community_risk(self, health_data: dict) -> str:
        context = _dict_to_context(health_data)
        prompt = (
            "You are an environmental public-health communicator. "
            "Using ONLY the data below, write 2-3 sentences explaining the potential environmental "
            "exposure risk to nearby communities. Do NOT make medical diagnoses or treatment recommendations. "
            "Focus on pollution levels and regulatory thresholds only.\n\n"
            f"COMMUNITY RISK DATA:\n{context}\n\nENVIRONMENTAL RISK SUMMARY:"
        )
        result = self._generate(prompt)
        if result:
            return result
        community = health_data.get("community_name", "Nearby community")
        risk = health_data.get("risk_level", "unknown")
        return (
            f"{community} faces {risk} environmental exposure risk based on proximity to industrial sources. "
            "AI explanation unavailable. Consult the risk data table for pollutant details."
        )

    def generate_alert_message(self, alert_data: dict) -> str:
        context = _dict_to_context(alert_data)
        prompt = (
            "You are an automated environmental alert system. "
            "Using ONLY the data below, write a concise (1-2 sentence) operational alert message "
            "suitable for sending to a regulatory officer. Include parameter, value, and limit if present.\n\n"
            f"ALERT DATA:\n{context}\n\nALERT MESSAGE:"
        )
        result = self._generate(prompt, max_tokens=128)
        if result:
            return result
        severity = alert_data.get("severity", "UNKNOWN")
        factory = alert_data.get("factory_name", alert_data.get("factory_id", "Unknown"))
        return f"[{severity}] Pollution alert at {factory}. Immediate review required."

    def answer_query(self, query: str, context_data: dict) -> str:
        context = _dict_to_context(context_data)
        prompt = (
            "You are an AI assistant for the Gujarat Industrial Pollution Intelligence Platform. "
            "Answer the user's question using ONLY the structured data provided. "
            "Be factual and concise. Do not invent sensor readings, factory names, or regulatory limits "
            "not present in the data. If the data does not contain enough information, say so clearly.\n\n"
            f"PLATFORM DATA:\n{context}\n\n"
            f"USER QUESTION: {query}\n\n"
            "ANSWER:"
        )
        result = self._generate(prompt, max_tokens=400)
        if result:
            return result
        return (
            "AI assistant is currently unavailable. "
            "Please use the dashboard and data tables to find the information you need."
        )

    def generate_incident_report(self, incident_id: int, full_data: dict) -> str:
        context = _dict_to_context(full_data)
        prompt = (
            "You are a regulatory compliance officer writing a formal incident report. "
            "Using ONLY the data below, write a structured incident report with sections: "
            "Summary, Timeline, Observations, Contributing Factors, and Recommended Actions. "
            "Use formal language. Do not invent any facts.\n\n"
            f"INCIDENT #{incident_id} DATA:\n{context}\n\nFORMAL INCIDENT REPORT:"
        )
        result = self._generate(prompt, max_tokens=700)
        if result:
            return result
        title = full_data.get("title", f"Incident #{incident_id}")
        factory = full_data.get("factory_name", "Unknown Factory")
        return (
            f"INCIDENT REPORT — {title}\n"
            f"Factory: {factory}\n"
            f"Severity: {full_data.get('severity', 'N/A')}\n"
            f"Status: {full_data.get('status', 'N/A')}\n\n"
            "Full AI-generated narrative unavailable. "
            "Refer to the structured incident data for complete details."
        )

    def generate_executive_summary(self, dashboard_data: dict) -> str:
        context = _dict_to_context(dashboard_data)
        prompt = (
            "You are a senior environmental compliance director. "
            "Using ONLY the platform data below, write a 1-paragraph executive summary "
            "of the current pollution situation across all monitored factories. "
            "Highlight critical issues, overall compliance status, and any urgent actions needed.\n\n"
            f"PLATFORM SUMMARY DATA:\n{context}\n\nEXECUTIVE SUMMARY:"
        )
        result = self._generate(prompt, max_tokens=400)
        if result:
            return result
        total = dashboard_data.get("total_factories", "N/A")
        critical = dashboard_data.get("critical_violations", 0)
        alerts = dashboard_data.get("pending_alerts", 0)
        return (
            f"Platform monitoring {total} industrial facilities. "
            f"{critical} critical violations and {alerts} pending alerts require immediate attention. "
            "AI executive summary unavailable — see dashboard KPIs for detailed status."
        )

    def explain_violation(self, violation_data: dict) -> str:
        context = _dict_to_context(violation_data)
        prompt = (
            "You are an environmental compliance analyst. "
            "Using ONLY the data below, explain this pollution violation in 2 sentences: "
            "what parameter exceeded what limit, by how much, and what regulatory risk it represents. "
            "Do not invent values.\n\n"
            f"VIOLATION DATA:\n{context}\n\nVIOLATION EXPLANATION:"
        )
        result = self._generate(prompt, max_tokens=150)
        if result:
            return result
        param = violation_data.get("parameter", "Unknown parameter")
        value = violation_data.get("value", "N/A")
        limit = violation_data.get("limit_value", "N/A")
        pct = violation_data.get("exceedance_percent", "N/A")
        return (
            f"{param} measured at {value} exceeds the regulatory limit of {limit} "
            f"by {pct}%. Immediate corrective action required."
        )


granite_service = GraniteService()
