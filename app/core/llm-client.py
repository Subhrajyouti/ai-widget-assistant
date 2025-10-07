"""
app/core/llm_client.py
------------------------------------------------
Handles interaction with the Language Model (LLM).
Supports two modes:
    1. Mock LLM (default, for local development)
    2. Real Gemini model (via LangChain integration)
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings


class LLMClient:
    """
    LLM abstraction layer.
    - If USE_MOCK_LLM=true, uses rule-based mock for local testing.
    - If false, connects to Gemini via LangChain's ChatGoogleGenerativeAI.
    """

    def __init__(self):
        self.use_mock = settings.USE_MOCK_LLM
        self.model = None

        if not self.use_mock:
            try:
                # Lazy import to avoid dependency load in mock mode
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain.schema import SystemMessage, HumanMessage

                self.SystemMessage = SystemMessage
                self.HumanMessage = HumanMessage

                # Initialize Gemini model (choose fast or pro depending on use)
                self.model = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    google_api_key=settings.GEMINI_API_KEY
                )
                logging.info("Initialized Gemini LLM successfully.")
            except Exception as e:
                logging.exception(f"❌ Failed to initialize Gemini model: {e}")
                self.model = None
                self.use_mock = True  # fallback to mock mode

    # -------------------------------------------------------------------------
    async def get_response(self, system_prompt: str, question: str, context: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """
        Main function to get a response from the LLM (real or mock).

        Args:
            system_prompt (str): Instruction template for LLM
            question (str): User question
            context (List[Dict]): Contextual data (e.g., flight cards)

        Returns:
            Dict[str, Optional[str]]: { "answer": str, "excerpt": str or None }
        """
        if self.use_mock or not self.model:
            return self._mock_response(question, context)

        try:
            user_content = (
                f"Question: {question}\n\n"
                f"Context (use only this data to answer):\n{json.dumps(context, ensure_ascii=False)}"
            )

            messages = [
                self.SystemMessage(content=system_prompt),
                self.HumanMessage(content=user_content)
            ]

            response = await self.model.ainvoke(messages)

            # Expect JSON output { "answer": ..., "excerpt": ... }
            text = response.content.strip()
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return {
                        "answer": parsed.get("answer") or "",
                        "excerpt": parsed.get("excerpt") or ""
                    }
                else:
                    raise ValueError("LLM returned non-dict JSON")
            except Exception:
                logging.warning("LLM returned non-JSON output, fallback parsing.")
                # fallback: attempt naive extraction
                return self._extract_answer_excerpt(text)

        except Exception as e:
            logging.exception(f"❌ LLM request failed: {e}")
            return {"answer": "I cannot process your question right now.", "excerpt": None}

    # -------------------------------------------------------------------------
    def _extract_answer_excerpt(self, raw_text: str) -> Dict[str, Optional[str]]:
        """
        Fallback parser for non-JSON responses.
        Attempts to extract an 'excerpt' block and an 'answer' line.
        """
        # naive extraction: look for text inside { ... } or quotes
        match = re.search(r"\\{.*\\}", raw_text, re.S)
        excerpt = match.group(0) if match else None
        answer_line = raw_text.strip().split("\\n")[0]
        return {"answer": answer_line[:500], "excerpt": excerpt}

    # -------------------------------------------------------------------------
    def _mock_response(self, question: str, context: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """
        Rule-based mock model for local development.
        Handles queries like 'cheapest flight after 6 pm' etc.
        """
        q = question.lower()
        import datetime

        def parse_price(p):
            if isinstance(p, (int, float)):
                return float(p)
            s = str(p)
            s = s.replace(",", "")
            m = re.search(r"(\\d+(?:\\.\\d+)?)", s)
            return float(m.group(1)) if m else None

        def get_dep_time(card):
            for k in ("departure_time", "dep_time", "departure", "departureAt", "dep"):
                if k in card and card[k]:
                    return str(card[k])
            if "segments" in card and isinstance(card["segments"], list) and card["segments"]:
                seg = card["segments"][0]
                for k in ("dep_time", "departure_time", "departure"):
                    if k in seg and seg[k]:
                        return str(seg[k])
            return None

        def parse_time_to_minutes(tstr):
            if not tstr:
                return None
            tstr = tstr.strip()
            patterns = ["%I:%M %p", "%I %p", "%H:%M", "%H"]
            for fmt in patterns:
                try:
                    dt = datetime.datetime.strptime(tstr.upper(), fmt)
                    return dt.hour * 60 + dt.minute
                except Exception:
                    pass
            m = re.search(r"(\\d{1,2})(?::(\\d{2}))?\\s*(am|pm)?", tstr.lower())
            if m:
                h = int(m.group(1))
                mm = int(m.group(2)) if m.group(2) else 0
                ampm = m.group(3)
                if ampm == "pm" and h != 12:
                    h += 12
                if ampm == "am" and h == 12:
                    h = 0
                return h * 60 + mm
            return None

        # parse filters
        after_time = None
        m_after = re.search(r"after\\s+(\\d{1,2}(?::\\d{2})?\\s*(?:am|pm)?)", q)
        if m_after:
            after_time = parse_time_to_minutes(m_after.group(1))

        m_airline = re.search(r"(air\\s*india|indigo|spicejet|vistara|airasia|goair|go air)", q)
        airline = m_airline.group(1) if m_airline else None

        # find cheapest matching card
        best = None
        best_price = None
        for card in context:
            price = parse_price(card.get("price") or card.get("fare") or card.get("amount"))
            if price is None:
                continue
            if airline:
                card_air = ""
                for k in ("airline", "carrier", "airline_name"):
                    if k in card and card[k]:
                        card_air = str(card[k]).lower()
                if airline not in card_air:
                    continue
            if after_time is not None:
                dep = get_dep_time(card)
                dep_minutes = parse_time_to_minutes(dep)
                if dep_minutes is None or dep_minutes < after_time:
                    continue
            if best is None or price < best_price:
                best = card
                best_price = price

        if best:
            airline_name = best.get("airline") or best.get("carrier") or best.get("airline_name") or "Unknown Airline"
            dep = get_dep_time(best) or "Unknown"
            ans = f"Cheapest flight{(' from ' + airline_name) if airline else ''} is {airline_name}, departs at {dep}, price {best_price}."
            excerpt = json.dumps(best, ensure_ascii=False)
            return {"answer": ans, "excerpt": excerpt}
        else:
            return {"answer": "I cannot find that information on this page.", "excerpt": None}
