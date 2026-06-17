import json
from modules.llm_service import query_llm
from modules.json_utils import execute_with_retry_and_fallback

def evaluate_presentation_quality(slides_outline, analyst_insights):
    """
    Evaluates the final slides outline against the original consulting insights.
    Returns:
        tuple (dict, dict): Parsed quality evaluation dictionary, and telemetry metrics.
    """
    system_prompt = (
        "You are a senior McKinsey-style business consultant acting as a presentation editor.\n"
        "Your task is to audit the proposed presentation outline against the original business analyst insights.\n"
        "Critique the work constructively and score the deck based on: Insight Relevance, Executive Readability, "
        "Recommendation Quality, and Slide Clarity.\n\n"
        "You MUST respond with a single valid JSON block matching this EXACT schema:\n"
        "{\n"
        '  "overall_score": "An integer score from 0 to 100 representing the deck\'s readiness (e.g., \'85/100\')",\n'
        '  "clarity": "A brief sentence evaluation of whether each slide has clear, concise headings and bullet points.",\n'
        '  "insight_depth": "An evaluation of whether data metrics and categories are used correctly without generic observations.",\n'
        '  "executive_readiness": "An assessment of whether the tone, formatting, and visuals align with board-level expectations.",\n'
        '  "suggestions": [\n'
        '    "Actionable editorial suggestion 1 (e.g. bold certain numbers, rearrange bullets)",\n'
        '    "Actionable editorial suggestion 2"\n'
        '  ]\n'
        "}\n"
        "Do not include any greetings, chatter, or text outside the JSON codeblock."
    )
    
    user_content = (
        "Here are the Original Consulting Insights:\n\n"
        f"{json.dumps(analyst_insights, indent=2)}\n\n"
        "Here is the Generated Presentation Outline:\n\n"
        f"{json.dumps(slides_outline, indent=2)}\n\n"
        "Perform your audit and return the strict JSON score block."
    )
    
    prompt_args = (system_prompt, user_content)
    required_keys = ["overall_score", "clarity", "insight_depth", "executive_readiness", "suggestions"]
    
    fallback_data = {
        "overall_score": "80/100",
        "clarity": "Default quality review: Slide titles are clear and bullets are aligned structurally.",
        "insight_depth": "Data metrics are included in the storyline flow, providing moderate numerical highlights.",
        "executive_readiness": "The tone matches corporate standards, with standard visual options suggested.",
        "suggestions": [
            "Ensure key figures like growth percentages or revenue numbers stand out in bold text.",
            "Re-read slide titles to verify they summarize the primary takeaway of the slide.",
            "Verify that slide durations align with meeting schedules (approx 2 mins per slide)."
        ]
    }
    
    evaluation, metrics = execute_with_retry_and_fallback(
        llm_call_func=query_llm,
        prompt_args=prompt_args,
        required_keys=required_keys,
        fallback_data=fallback_data
    )
    
    return evaluation, metrics
