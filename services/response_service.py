"""
Grounded Response Generation Service for SupportFlow AI.

Synthesizes customer support ticket context and retrieved RAG knowledge base chunks
using Google Gemini to draft accurate, empathetic, and strictly grounded responses.
"""

import time
from typing import List, Dict, Any, Tuple, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import get_gemini_api_key, is_gemini_configured, GEMINI_MODEL_NAME

SYSTEM_PROMPT_GROUNDED = """
You are a professional customer support specialist for SupportFlow AI.
Your task is to draft a helpful, polite, and professional resolution message in response to the customer's support ticket.

Strict Grounding Guidelines:
1. Grounding: All factual statements, policies, turnaround times, eligibility rules, limits, and procedures MUST come strictly from the provided Company Knowledge Base Context.
2. No Hallucination: Do NOT invent, assume, or extrapolate policies, discounts, refund timeframes, or rules that are not explicitly stated in the context.
3. Insufficient Context: If the provided knowledge base context does not contain enough information to resolve the issue, politely inform the customer that their request has been received and escalated to the appropriate support team for detailed review.
4. Tone & Style: Be professional, empathetic, concise, and customer-centric. Address the customer directly.
"""


def extract_deterministic_sources(retrieved_chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Deterministically extracts unique document titles and section references
    from the retrieved chunks rather than relying on LLM hallucination.
    """
    sources = []
    seen = set()
    for chunk in retrieved_chunks:
        doc_title = chunk.get("doc_title", "").strip()
        section = chunk.get("section", "").strip()
        if doc_title:
            label = f"{doc_title} ({section})" if section and section != "General Overview" else doc_title
            if label not in seen:
                seen.add(label)
                sources.append(label)
    return sources


def generate_suggested_response(
    customer_name: str,
    subject: str,
    description: str,
    retrieved_chunks: List[Dict[str, Any]],
    category: Optional[str] = None,
    priority: Optional[str] = None,
    max_retries: int = 3
) -> Tuple[bool, str, List[str]]:
    """
    Generates an AI suggested response grounded strictly in retrieved knowledge base chunks.

    Returns:
        (True, response_text, sources_list) on success
        (False, error_message, []) on failure
    """
    if not is_gemini_configured():
        return False, "Gemini API key is not configured. Please check your .env file.", []

    api_key = get_gemini_api_key()
    sources = extract_deterministic_sources(retrieved_chunks)

    # Format Retrieved Knowledge Base Context
    if retrieved_chunks:
        context_parts = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            doc = chunk.get("doc_title", "Document")
            sec = chunk.get("section", "")
            text = chunk.get("text", "")
            context_parts.append(f"[{idx}] Source: {doc} - {sec}\n{text}")
        context_block = "\n\n".join(context_parts)
    else:
        context_block = "No matching company knowledge base documents found for this inquiry."

    user_prompt = f"""Customer Ticket:
Customer Name: {customer_name.strip() if customer_name else 'Valued Customer'}
Subject: {subject.strip()}
Description: {description.strip()}
{f'Category: {category}' if category else ''}
{f'Priority: {priority}' if priority else ''}

Company Knowledge Base Context:
{context_block}

Instructions:
Draft the response to the customer based only on the above context and ticket details."""

    client = genai.Client(api_key=api_key)

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=f"{SYSTEM_PROMPT_GROUNDED}\n\n{user_prompt}")]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                )
            )

            if not response.text:
                return False, "Gemini API returned an empty response.", []

            return True, response.text.strip(), sources

        except APIError as ae:
            if ae.code == 429 and attempt < max_retries:
                time.sleep(6 * (attempt + 1))
                continue
            elif ae.code == 429:
                return False, "Free-tier rate limit reached. Please wait a few moments and try again.", []
            return False, f"Gemini API error ({ae.code}): {ae.message}", []
        except Exception as e:
            if "429" in str(e) and attempt < max_retries:
                time.sleep(6 * (attempt + 1))
                continue
            elif "429" in str(e):
                return False, "Free-tier rate limit reached. Please wait a few moments and try again.", []
            return False, f"Error generating response: {str(e)}", []

    return False, "Response generation timed out after retry attempts.", []
