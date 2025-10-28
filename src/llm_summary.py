# src/llm_summary.py
import json
import os
import re
from openai import OpenAI
from src.error_handler import retry_with_backoff, ErrorContext, RetryableError, FatalError
import logging

logger = logging.getLogger(__name__)

# [OK] Load API key from environment (set in .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# [OK] Initialize client once (only if API key is available)
client = None
if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI client: {e}")
        client = None
else:
    logger.warning("OPENAI_API_KEY not found in environment variables")

def _create_fallback_json(content: str, job_title: str, company: str) -> str:
    """
    Create a fallback JSON response when the LLM response is malformed.
    Attempts to extract partial data and creates a valid JSON structure.
    """
    import re
    
    # Default fallback keywords based on common tech skills
    default_keywords = "Python, JavaScript, React, Node.js, AWS, Docker, SQL"
    
    # Try to extract summary using regex for better accuracy
    summary_match = re.search(r'"summary":\s*"([^"]*(?:\\.[^"]*)*)"', content)
    if summary_match:
        summary_text = summary_match.group(1)
        # Unescape common escape sequences
        summary_text = summary_text.replace('\\"', '"').replace('\\\\', '\\')
    else:
        # Try to find any text that looks like a summary
        summary_match = re.search(r'"summary":\s*"([^"]*)"', content)
        if summary_match:
            summary_text = summary_match.group(1)
        else:
            # Create a generic summary based on job title
            summary_text = f"Experienced software developer with strong technical skills and proven track record in {job_title.lower()} roles."
    
    # Try to extract keywords
    keywords_match = re.search(r'"keywords":\s*"([^"]*)"', content)
    if keywords_match:
        keywords_text = keywords_match.group(1)
    else:
        keywords_text = default_keywords
    
    # Create valid JSON
    fallback_json = {
        "summary": summary_text,
        "keywords": keywords_text
    }
    
    logger.info(f"[OK] Created fallback JSON for {job_title} at {company}")
    return json.dumps(fallback_json)

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def generate_resume_summary(
    job_title: str,
    company: str,
    description: str,
    max_tokens: int = 300
) -> str:
    """
    Generates a concise, tailored resume summary for a specific job using OpenAI.
    Always returns clean JSON (code fences stripped if GPT adds them).
    """
    if not OPENAI_API_KEY or not client:
        logger.warning("[WARN] OPENAI_API_KEY is missing or client not initialized - returning fallback summary")
        return _create_fallback_json(description, job_title, company)

    # Input validation
    if not job_title or not company or not description:
        raise ValueError("[ERROR] Missing required parameters: job_title, company, and description must be provided")
    
    # Truncate description if too long to avoid token limits
    max_description_length = 4000  # Reduced to leave room for response
    truncated_description = description[:max_description_length]
    if len(description) > max_description_length:
        logger.warning(f"[WARN] Description truncated from {len(description)} to {max_description_length} characters")

    # Prompt for GPT model
    prompt = f"""
    Here is a job description for an open position of {job_title} at {company}:
    {truncated_description}

    From the description above, create a list of emphasized keywords that are relevant to the job.
    Emphasize technical skills like Python, Docker, React, and LLM integration. Limit to a maximum of 7 keywords.

    Write a concise 2-3 sentence resume summary for a software developer applying to this role. 
    Highlight relevant skills, adaptability, and enthusiasm for the role. Use a professional tone and avoid clichés.

    I need the return for all of this to explicitly be JSON in this format below:
    {{
        "summary": "<generated_summary>",
        "keywords": "<emphasized_keywords>"
    }}
    """

    with ErrorContext(f"LLM summary generation for {job_title} at {company}") as context:
        context.add_context("job_title", job_title)
        context.add_context("company", company)
        context.add_context("description_length", len(description))
        
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
            
            # Check for empty response
            if not raw_content.strip():
                logger.warning("[WARN] LLM returned empty response")
                cleaned_content = _create_fallback_json("", job_title, company)
            else:
                cleaned_content = raw_content.strip()
                logger.debug(f"[DEBUG] Raw LLM response length: {len(cleaned_content)} characters")

            # [OK] Remove code fences if GPT wraps JSON in ```json ... ```
            if cleaned_content.startswith("```"):
                cleaned_content = re.sub(r"^```(?:json)?", "", cleaned_content, flags=re.IGNORECASE).strip()
                cleaned_content = re.sub(r"```$", "", cleaned_content).strip()
                logger.info("[OK] Removed code fences from LLM response")

            # [OK] Validate JSON - if bad, try to fix truncated responses
            try:
                json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.warning(f"[WARN] JSON parsing failed: {e}")
                
                # Try to fix truncated JSON by adding missing closing braces
                if cleaned_content.count('{') > cleaned_content.count('}'):
                    missing_braces = cleaned_content.count('{') - cleaned_content.count('}')
                    cleaned_content += '}' * missing_braces
                    logger.info(f"[OK] Added {missing_braces} missing closing braces")
                    
                    # Try parsing again
                    try:
                        json.loads(cleaned_content)
                        logger.info("[OK] Fixed truncated JSON by adding missing braces")
                    except json.JSONDecodeError as parse_error:
                        logger.warning(f"[WARN] JSON still invalid after fixing braces: {parse_error}")
                        cleaned_content = _create_fallback_json(cleaned_content, job_title, company)
                else:
                    # Try to extract partial data using regex for better accuracy
                    cleaned_content = _create_fallback_json(cleaned_content, job_title, company)
                
                # Final validation
                try:
                    json.loads(cleaned_content)
                    logger.info("[OK] Successfully created valid JSON from partial response")
                except json.JSONDecodeError as final_error:
                    raise ValueError(f"[LLM ERROR] GPT returned invalid JSON that could not be fixed: {cleaned_content[:200]}... Error: {final_error}")

            # Log success with summary of what was generated
            try:
                parsed_result = json.loads(cleaned_content)
                summary_preview = parsed_result.get("summary", "")[:100] + "..." if len(parsed_result.get("summary", "")) > 100 else parsed_result.get("summary", "")
                keywords_preview = parsed_result.get("keywords", "")
                logger.info(f"[OK] Summary generated successfully for {job_title} at {company}")
                logger.debug(f"[DEBUG] Summary preview: {summary_preview}")
                logger.debug(f"[TAG] Keywords: {keywords_preview}")
            except:
                logger.info(f"[OK] Summary generated (raw): {cleaned_content[:200]}...")
            
            context.add_context("success", True)
            return cleaned_content

        except Exception as e:
            context.add_context("error", str(e))
            context.add_context("error_type", type(e).__name__)
            
            # Determine if this is a retryable error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["rate limit", "timeout", "connection", "network"]):
                raise RetryableError(f"[ERROR] Summary generation failed (retryable): {e}")
            elif "invalid json" in error_str or "json" in error_str:
                raise FatalError(f"[ERROR] Summary generation failed (fatal - JSON error): {e}")
            else:
                raise FatalError(f"[ERROR] Summary generation failed (fatal): {e}")