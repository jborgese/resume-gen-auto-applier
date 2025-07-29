# src/llm_summary.py
import os
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

    :param job_title: The job title being applied for.
    :param company: The company name.
    :param description: The cleaned job description text.
    :param keywords: Optional list of extracted keywords to weave into the summary.
    :param max_tokens: Token limit for the summary (default 120).
    :return: A one-paragraph resume summary as a string.
    """
    if not OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY is missing — add it to your .env file.")

    # Prompt for GPT model
    prompt = f"""
    Write a concise 2–3 sentence resume summary for a software developer applying to the role of
    '{job_title}' at '{company}'. Highlight relevant skills, adaptability, and enthusiasm for the role.

    Use a professional tone and avoid clichés. The job description is:

    {description[:800]}

    From the description above, create a list of emphasized keywords that are relevant to the job.
    Emphasize technical skills like Python, Docker, React, and LLM integration. Limit to a maximum of 7 keywords.

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

        content = response.choices[0].message.content
        summary = content.strip() if content else ""
        print(f"[INFO] ✅ Summary generated: {summary}")
        return summary

    except Exception as e:
        print(f"[ERROR] 🚨 Failed to generate summary: {e}")
        return "Software developer with proven experience in backend systems, automation, and modern technologies."
