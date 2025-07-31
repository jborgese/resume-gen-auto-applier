# src/llm_summary.py
import json
import os
import re
from openai import OpenAI

# ✅ Load API key from environment (set in .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize client once
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_resume_summary(
    job_title: str,
    company: str,
    description: str,
    max_tokens: int = 120
) -> str:
    """
    Generates a concise, tailored resume summary for a specific job using OpenAI.
    Always returns clean JSON (code fences stripped if GPT adds them).
    """
    if not OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY is missing — add it to your .env file.")

    # Prompt for GPT model
    prompt = f"""
    Here is a job description for an open position of {job_title} at {company}:
    {description[:5000]}

    From the description above, create a list of emphasized keywords that are relevant to the job.
    Emphasize technical skills like Python, Docker, React, and LLM integration. Limit to a maximum of 7 keywords.

    Write a concise 2–3 sentence resume summary for a software developer applying to this role. 
    Highlight relevant skills, adaptability, and enthusiasm for the role. Use a professional tone and avoid clichés.

    I need the return for all of this to explicitly be JSON in this format below:
    {{
        "summary": "<generated_summary>",
        "keywords": "<emphasized_keywords>"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that writes professional, concise resume summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )

        raw_content = response.choices[0].message.content or ""
        cleaned_content = raw_content.strip()

        # ✅ Remove code fences if GPT wraps JSON in ```json ... ```
        if cleaned_content.startswith("```"):
            cleaned_content = re.sub(r"^```(?:json)?", "", cleaned_content, flags=re.IGNORECASE).strip()
            cleaned_content = re.sub(r"```$", "", cleaned_content).strip()

        # ✅ Validate JSON — if bad, raise so scraper can skip this job
        try:
            json.loads(cleaned_content)
        except json.JSONDecodeError:
            raise ValueError(f"[LLM ERROR] GPT returned invalid JSON: {cleaned_content}")

        print(f"[INFO] ✅ Summary generated (cleaned): {cleaned_content}")
        return cleaned_content

    except Exception as e:
        # ✅ Raise the error so scraper.py can skip
        raise RuntimeError(f"❌ Summary generation failed: {e}")