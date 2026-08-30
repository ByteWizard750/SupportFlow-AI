"""
AI Ticket Analysis Service for SupportFlow AI.

Utilizes Google Gemini LLM with structured schema outputs to analyze support tickets
for Category, Priority, Sentiment, Department routing, and contextual Reasoning.
"""

import time
from enum import Enum
from typing import Tuple, Dict, Any, Union
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import get_gemini_api_key, is_gemini_configured, GEMINI_MODEL_NAME


class TicketCategory(str, Enum):
    BILLING = "Billing and Payments"
    ACCOUNT = "Account and Login"
    SUBSCRIPTION = "Subscription"
    TECHNICAL = "Technical Issue"
    REFUND = "Refund"
    GENERAL = "General Inquiry"
    OTHER = "Other"


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketSentiment(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"
    FRUSTRATED = "Frustrated"


class RecommendedDepartment(str, Enum):
    BILLING = "Billing Support"
    ACCOUNT = "Account Support"
    TECHNICAL = "Technical Support"
    SUBSCRIPTION = "Subscription Support"
    CUSTOMER_SERVICE = "Customer Service"


class TicketAnalysisSchema(BaseModel):
    """
    Pydantic schema enforcing structured JSON output from the Gemini LLM.
    """
    category: TicketCategory = Field(
        description="The primary classification category for this support ticket."
    )
    priority: TicketPriority = Field(
        description="Assigned urgency level based on issue impact (Low, Medium, High, Critical)."
    )
    sentiment: TicketSentiment = Field(
        description="Customer emotional sentiment detected from the ticket content (Positive, Neutral, Negative, Frustrated)."
    )
    department: RecommendedDepartment = Field(
        description="The recommended internal support department to resolve this ticket."
    )
    reasoning: str = Field(
        description="A concise 1-2 sentence explanation justifying the assigned category, priority, sentiment, and department based strictly on evidence in the ticket."
    )


SYSTEM_PROMPT = """
You are an expert customer support operations assistant. Analyze the incoming customer support ticket carefully.
Determine the most appropriate category, priority level, customer sentiment, recommended department, and a concise 1-2 sentence reasoning.

Priority Classification Guidelines:
- Low: General questions, information requests, feature inquiries, or minor issues with little or no impact on normal usage.
- Medium: Standard customer problems requiring support (such as routine refund requests, duplicate monthly charges, single-user password/login issues, or minor functional problems), where there is no explicit evidence of major business disruption, urgent deadlines, or widespread failure.
- High: Significant disruption to an important/core function, a user or team being substantially blocked from critical work, major financial impact, or urgent issues with explicit deadlines.
- Critical: Complete service outage, security breach, data loss, severe system failure, or an issue affecting many users/business-critical operations.

Important Classification Rules:
1. Do not assume urgency, business impact, financial severity, or widespread impact unless it is explicitly stated in the ticket.
2. Do not classify routine refund requests or single-user billing/login issues as High priority unless the customer explicitly describes severe financial harm or critical business blockage.
3. When uncertain between Medium and High, always choose Medium unless there is clear evidence of significant disruption or urgent impact.
4. Critical should only be used for genuinely severe situations such as outages, security incidents, data loss, or widespread service failures.
5. The AI reasoning must justify the selected priority based only on facts present in the ticket.

Sentiment Classification Guidelines:
- Positive: Gratitude, compliments, pleasant tone.
- Neutral: Direct, matter-of-fact inquiries or status requests.
- Negative: Disappointment, mild dissatisfaction, inconvenience.
- Frustrated: Anger, urgency, repeated unresolved issues, demanding tone.

Always base your classification strictly on the ticket context, without assuming facts not in the text.
"""


def analyze_ticket(
    subject: str,
    description: str,
    max_retries: int = 2
) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    Analyzes a support ticket using the Gemini LLM and returns structured classification metadata.
    Includes automated retry with backoff for transient free-tier rate limits (HTTP 429).

    Returns:
        (True, analysis_dict) on success
        (False, error_message) on failure
    """
    if not is_gemini_configured():
        return False, "Gemini API key is not configured. Please check your .env file."

    if not subject.strip() and not description.strip():
        return False, "Ticket subject and description cannot both be empty."

    api_key = get_gemini_api_key()

    prompt = f"""Support Ticket:
Subject: {subject.strip()}
Description: {description.strip()}

Analyze the ticket and provide your structured classification."""

    client = genai.Client(api_key=api_key)

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=f"{SYSTEM_PROMPT}\n\n{prompt}")]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TicketAnalysisSchema,
                    temperature=0.1,
                )
            )

            if not response.text:
                return False, "Gemini API returned an empty response."

            # Validate JSON output using Pydantic
            parsed_data = TicketAnalysisSchema.model_validate_json(response.text)
            return True, parsed_data.model_dump()

        except APIError as ae:
            # Handle rate limit (429) with retry backoff
            if ae.code == 429 and attempt < max_retries:
                time.sleep(4 * (attempt + 1))
                continue
            elif ae.code == 429:
                return False, "Free-tier rate limit reached (20 requests/minute). Please wait ~15 seconds and try again."
            return False, f"Gemini API error ({ae.code}): {ae.message}"
        except ValidationError as ve:
            return False, f"Structured output validation error: {str(ve)}"
        except Exception as e:
            if "429" in str(e) and attempt < max_retries:
                time.sleep(4 * (attempt + 1))
                continue
            elif "429" in str(e):
                return False, "Free-tier rate limit reached (20 requests/minute). Please wait ~15 seconds and try again."
            return False, f"Unexpected error during AI analysis: {str(e)}"

    return False, "Analysis failed after retry attempts."
