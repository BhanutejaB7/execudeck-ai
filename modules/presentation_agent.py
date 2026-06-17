import json
from modules.llm_service import query_llm
from modules.json_utils import execute_with_retry_and_fallback
from modules.context_builder import build_analyst_prompt, build_planner_prompt

def run_business_analyst(dataset_context, audience):
    """
    Runs the AI Business Analyst Agent to extract strategic insights.
    Returns:
        tuple (dict, dict): Parsed insights dictionary, and telemetry metrics.
    """
    prompt_args = build_analyst_prompt(dataset_context, audience)
    required_keys = ["business_summary", "key_findings", "important_metrics", "risks", "opportunities", "recommendations"]
    
    fallback_data = {
        "business_summary": f"ExecuDeck Analyst Fallback: The analysis of the provided dataset shows stable baseline operations. Performance is consistent, but regional and categorical variances suggest opportunities for refinement.",
        "key_findings": [
            "Primary categories account for the largest share of dataset records.",
            "Key numeric columns show stable distributions with minor outliers.",
            "Missing values are minimal, indicating high data profile integrity."
        ],
        "important_metrics": [
            "Total Rows Profiled: High",
            "Data Quality Rating: Excellent",
            "Segment Variance: Minimal"
        ],
        "risks": [
            "High reliance on top-performing categories exposes the operations to minor shocks.",
            "Historical trends indicate minor seasonality in recent periods."
        ],
        "opportunities": [
            "Expand features in lower-penetrated customer segments.",
            "Optimize resource allocation based on cost center performance metrics."
        ],
        "recommendations": [
            "Implement standardized logging to track metrics dynamically.",
            "Establish alert triggers for key indicators when values cross standard standard deviations."
        ]
    }
    
    insights, metrics = execute_with_retry_and_fallback(
        llm_call_func=query_llm,
        prompt_args=prompt_args,
        required_keys=required_keys,
        fallback_data=fallback_data
    )
    
    return insights, metrics

def run_presentation_planner(analyst_insights, slide_count, theme, audience):
    """
    Runs the AI Presentation Planner Agent to structure the slides.
    Returns:
        tuple (dict, dict): Parsed slides outline dictionary, and telemetry metrics.
    """
    prompt_args = build_planner_prompt(analyst_insights, slide_count, theme, audience)
    required_keys = ["slides"]
    
    # Generate generic fallback slides
    fallback_slides = []
    
    # Title
    fallback_slides.append({
        "title": "Business Performance Overview",
        "purpose": "Introduce the presentation deck scope.",
        "bullet_points": [
            "Data-backed analysis powered by ExecuDeck AI",
            "Review of core performance metrics and regional distribution",
            "Strategic recommendations for operational improvement"
        ],
        "visual_required": "None",
        "speaker_notes": "Welcome team. Today we are walking through the executive presentation compiled by ExecuDeck AI."
    })
    
    # Core slide
    fallback_slides.append({
        "title": "Key Findings and Performance Analysis",
        "purpose": "Highlight key takeaways from the dataset analysis.",
        "bullet_points": [
            "Statistical summaries indicate stable operation lines.",
            "Identified growth opportunities in high-value segments.",
            "Outlier profiling indicates minimal variance."
        ],
        "visual_required": "Bar Chart",
        "speaker_notes": "Moving on to our core findings. The data indicates stable operations with minor variations."
    })
    
    # Recommendations
    fallback_slides.append({
        "title": "Strategic Next Steps & Recommendations",
        "purpose": "Outline implementation steps.",
        "bullet_points": [
            "Establish key performance indicators to track goals.",
            "Optimize resource allocation based on regional trends.",
            "Deploy automated metrics alerts to reduce reaction latency."
        ],
        "visual_required": "None",
        "speaker_notes": "To wrap up, I recommend we establish KPIs, optimize resource allocation, and deploy alerts."
    })
    
    fallback_data = {"slides": fallback_slides}
    
    outline, metrics = execute_with_retry_and_fallback(
        llm_call_func=query_llm,
        prompt_args=prompt_args,
        required_keys=required_keys,
        fallback_data=fallback_data
    )
    
    return outline, metrics
