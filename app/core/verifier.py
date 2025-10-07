"""
app/core/verifier.py
---------------------------------------
Ensures that the excerpt provided by the LLM
actually exists in the given page context.

This acts as a safety guardrail to prevent
hallucinated responses.
"""

def verify_excerpt(context_blob: str, excerpt: str) -> bool:
    """
    Verify if the excerpt (from LLM response)
    actually exists verbatim in the original page context.

    Args:
        context_blob (str): Full serialized context (JSON string of flight cards)
        excerpt (str): Excerpt text from model response

    Returns:
        bool: True if excerpt exists in context, else False
    """
    if not excerpt or not context_blob:
        return False

    # Simple substring match (verbatim check)
    if excerpt in context_blob:
        return True

    # Optional: fallback to trimmed/normalized matching
    normalized_context = " ".join(context_blob.lower().split())
    normalized_excerpt = " ".join(excerpt.lower().split())
    return normalized_excerpt in normalized_context
