import json

def build_dataset_context(df, profile, max_sample_rows=3):
    """
    Constructs a condensed text context of the dataset suitable for feeding into the LLM.
    Returns:
        dict: A compact JSON representation of the dataset context
    """
    # Grab sample rows
    head_sample = df.head(max_sample_rows).to_dict(orient="records")
    tail_sample = df.tail(max_sample_rows).to_dict(orient="records")
    
    context = {
        "dataset_summary": {
            "total_rows": profile["dimensions"]["rows"],
            "total_columns": profile["dimensions"]["columns"],
            "detected_dtypes": {col: profile["column_profiles"][col]["dtype"] for col in profile["column_profiles"]}
        },
        "sample_records": {
            "first_few_rows": head_sample,
            "last_few_rows": tail_sample
        },
        "key_performance_indicators": profile.get("kpis", {}),
        "statistical_highlights": {},
        "top_bottom_performers": profile.get("performers", {}),
        "growth_trends": profile.get("growth_patterns", {}),
        "notable_correlations": profile.get("correlations", {}),
        "data_quality_issues": {}
    }
    
    # Compress numerical summaries
    for col, summary in profile.get("numerical_summaries", {}).items():
        context["statistical_highlights"][col] = {
            "average": summary["mean"],
            "median": summary["median"],
            "range": f"{summary['min']} to {summary['max']}"
        }
        
    # Compress categorical mode and cardinality
    for col, summary in profile.get("categorical_summaries", {}).items():
        context["statistical_highlights"][col] = {
            "unique_values_count": summary["cardinality"],
            "mode": summary["mode"],
            "top_categories": list(summary["top_categories_count"].keys())
        }
        
    # Compress anomaly markers
    for col, anomaly in profile.get("anomalies", {}).items():
        context["data_quality_issues"][col] = {
            "outliers_found": anomaly["outlier_count"],
            "percentage_outliers": anomaly["outlier_percentage"]
        }
        
    # Compress missing value alerts
    for col, info in profile.get("column_profiles", {}).items():
        if info["missing_count"] > 0:
            context["data_quality_issues"][col] = {
                "missing_records": info["missing_count"],
                "missing_percentage": info["missing_percentage"]
            }
            
    return context

def build_analyst_prompt(dataset_context, audience):
    """
    Assembles prompt for the AI Business Analyst Agent.
    """
    audience_instructions = {
        "ceo": "Focus on high-level strategic opportunities, macro financial impact, market risks, and long-term actionable recommendations. Avoid hyper-technical data terms.",
        "cfo": "Focus heavily on capital efficiency, direct revenue impact, cost structures, margins, return on investment (ROI), risks, and bottom-line optimizations.",
        "manager": "Focus on operational execution, team performance, process optimization, department KPIs, and tactical recommendations.",
        "technical": "Focus on engineering details, exact metrics, data anomalies, statistical properties, architecture implications, and data-backed observations."
    }
    
    instruction = audience_instructions.get(audience.lower(), audience_instructions["ceo"])
    
    system_prompt = (
        "You are a senior McKinsey-style business consultant creating board-level executive presentations.\n"
        "Your task is to analyze the provided dataset summary and extract strategic, data-backed insights.\n"
        "Avoid generic observations (e.g., do not just state 'sales increased' without details; use numbers and specific categories).\n"
        "All AI inference happens locally, ensuring enterprise privacy and that business data is secure.\n"
        f"Target Audience for presentation: {audience.upper()}.\n"
        f"Audience Perspective instructions: {instruction}\n\n"
        "You MUST respond with a single, valid JSON block matching this EXACT schema:\n"
        "{\n"
        '  "business_summary": "A concise executive summary paragraph tailored to the target audience.",\n'
        '  "key_findings": ["Bullet point finding 1 with exact data facts.", "Bullet point finding 2..."],\n'
        '  "important_metrics": ["Metric A: Value (growth or share)", "Metric B..."],\n'
        '  "risks": ["Identified operational or financial risk 1", "Risk 2..."],\n'
        '  "opportunities": ["Growth or efficiency opportunity 1", "Opportunity 2..."],\n'
        '  "recommendations": ["Actionable, strategic recommendation 1", "Recommendation 2..."]\n'
        "}\n"
        "Do not include any greeting, explanation, markdown formatting wrappers outside the JSON codeblock, or text before/after the JSON block."
    )
    
    user_content = (
        "Below is the summarized context of the dataset:\n\n"
        f"{json.dumps(dataset_context, indent=2)}\n\n"
        "Analyze the data above and generate your consulting insights. Deliver strict JSON output."
    )
    
    return system_prompt, user_content

def build_planner_prompt(analyst_insights, slide_count, theme, audience):
    """
    Assembles prompt for the AI Presentation Planner Agent.
    """
    system_prompt = (
        "You are a senior McKinsey-style business consultant creating board-level executive presentations.\n"
        "Your task is to translate raw business insights into a structured, narrative-driven presentation storyline.\n"
        "Avoid boring default structures. Choose an engaging storyline flow suited for the target audience.\n"
        f"Audience: {audience.upper()}\n"
        f"Theme style: {theme.upper()}\n"
        f"Target slide count: {slide_count}\n\n"
        "Determine the presentation structure and output a strict JSON outline matching this schema:\n"
        "{\n"
        '  "slides": [\n'
        "    {\n"
        '      "title": "Title of the slide",\n'
        '      "purpose": "A 1-sentence strategic explanation of why this slide is included",\n'
        '      "bullet_points": [\n'
        '        "Detailed, data-backed bullet point 1",\n'
        '        "Detailed bullet point 2",\n'
        '        "Detailed bullet point 3"\n'
        "      ],\n"
        '      "visual_required": "None | Line Chart | Bar Chart | Distribution Chart | Comparison Chart",\n'
        '      "speaker_notes": "A brief script of what the presenter should say on this slide."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Ensure you generate EXACTLY {slide_count} slides. The first slide MUST be the Title Slide. "
        "The second slide should be an Executive Summary or Agenda. The middle slides should cover "
        "findings, metrics, and charts. The final slides must detail recommendations and strategic conclusions.\n\n"
        "Do not include any text, markdown format labels (except ```json), or chatter outside the JSON codeblock."
    )
    
    user_content = (
        "Here are the senior consultant analyst insights generated for our business dataset:\n\n"
        f"{json.dumps(analyst_insights, indent=2)}\n\n"
        "Plan the presentation slide-by-slide structure. Deliver strict JSON output."
    )
    
    return system_prompt, user_content
