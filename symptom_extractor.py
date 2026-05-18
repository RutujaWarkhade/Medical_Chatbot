from langchain_groq import ChatGroq
import os

# ── Cache LLM instance so it's created only once ─────────────────────
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model_name="llama-3.1-8b-instant",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0
        )
    return _llm


def extract_symptoms_llm(text: str, lang_code: str = "en") -> list[str]:
    """
    Extract medical symptoms from English text.
    If lang_code is 'hi' or 'mr', symptoms are returned in that language too.

    Args:
        text      : English text to extract symptoms from
        lang_code : target language code ("en", "hi", "mr")

    Returns:
        List of symptom strings, or empty list if none found / on error.
    """
    if not text or not text.strip():
        return []

    # Language name for the prompt
    lang_name_map = {
        "en": "English",
        "hi": "Hindi",
        "mr": "Marathi",
    }
    lang_name = lang_name_map.get(lang_code, "English")

    # If non-English, ask LLM to return symptoms in both English and target language
    if lang_code == "en":
        prompt = f"""Extract medical symptoms from the text below.
Rules:
- Return ONLY a comma-separated list of symptoms.
- If no symptoms are found, return exactly: none
- Do not add explanations, numbering, or extra text.

Text: {text}

Symptoms:"""
    else:
        prompt = f"""Extract medical symptoms from the text below.
Rules:
- Return ONLY a comma-separated list of symptoms in {lang_name}.
- If no symptoms are found, return exactly: none
- Do not add explanations, numbering, or extra text.

Text: {text}

Symptoms in {lang_name}:"""

    try:
        llm      = get_llm()
        response = llm.invoke(prompt)
        content  = response.content.strip()

        # If LLM says no symptoms found
        if content.lower() in ("none", "none.", "no symptoms", "no symptoms found", ""):
            return []

        # Parse comma-separated list, clean each item
        symptoms = [
            s.strip().strip(".-•*")
            for s in content.split(",")
            if s.strip() and s.strip().lower() not in ("none", "")
        ]

        return symptoms

    except Exception as e:
        print(f"[symptom_extractor] Error: {e}")
        return []