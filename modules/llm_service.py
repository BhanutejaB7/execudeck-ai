import time
import json
from openai import OpenAI
import config

def get_openai_client():
    """
    Returns an initialized OpenAI client pointing to the vLLM server.
    """
    return OpenAI(
        base_url=config.VLLM_BASE_URL,
        api_key="token-not-needed-for-vllm" # vLLM doesn't require keys usually
    )

def query_llm(system_prompt, user_prompt):
    """
    Queries the model on vLLM, tracking tokens and latency.
    Falls back to mock responses if vLLM is not available.
    Returns:
        tuple (str, dict): The raw model response string, and a dictionary of telemetry metrics.
    """
    metrics = {
        "latency_seconds": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "tokens_per_second": 0.0,
        "mode": "vLLM GPU" if config.VLLM_ACTIVE else "Local Fallback"
    }

    if config.VLLM_ACTIVE:
        start_time = time.time()
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2, # low temperature for structured consulting JSON
                max_tokens=2048
            )
            latency = time.time() - start_time
            
            raw_content = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
            metrics["latency_seconds"] = round(latency, 3)
            metrics["prompt_tokens"] = prompt_tokens
            metrics["completion_tokens"] = completion_tokens
            metrics["tokens_per_second"] = round(completion_tokens / latency, 2) if latency > 0 else 0.0
            
            return raw_content, metrics
        except Exception as e:
            # If live call fails mid-way, drop down to local fallback
            metrics["mode"] = f"Local Fallback (vLLM Error: {str(e)[:40]}...)"
            
    # --- Local Fallback Mode ---
    start_time = time.time()
    # Let's inspect the user prompt to see if we are in Analyst mode or Planner mode
    is_planner = "slides" in system_prompt or "presentation structure" in system_prompt
    is_evaluator = "overall_score" in system_prompt or "clarity" in system_prompt
    
    # We will generate a rich mock response depending on the data context in user_prompt
    # Detect what kind of demo data is used
    dataset_type = "generic"
    if "sales_demo.csv" in user_prompt or "Region" in user_prompt or "Product" in user_prompt:
        dataset_type = "sales"
    elif "finance_demo.csv" in user_prompt or "Cost_Center" in user_prompt or "Budget" in user_prompt:
        dataset_type = "finance"
    elif "hr_demo.csv" in user_prompt or "Avg_Salary" in user_prompt or "Avg_Satisfaction" in user_prompt:
        dataset_type = "hr"
        
    time.sleep(0.5) # Simulate slight model processing latency
    
    if is_evaluator:
        mock_response = generate_mock_evaluator_response()
    elif is_planner:
        # Detect slide count from system prompt
        slide_count = 5
        slide_match = config.ROOT_DIR # Dummy check
        try:
            # Find slide count number
            counts = [int(s) for s in system_prompt.split() if s.isdigit()]
            if len(counts) > 0:
                slide_count = counts[-1]
                if slide_count < 3 or slide_count > 15:
                    slide_count = 5
        except Exception:
            pass
        mock_response = generate_mock_planner_response(dataset_type, slide_count)
    else:
        mock_response = generate_mock_analyst_response(dataset_type)
        
    latency = time.time() - start_time
    
    # Estimate tokens
    prompt_tokens = len(system_prompt.split()) + len(user_prompt.split())
    completion_tokens = len(mock_response.split())
    
    metrics["latency_seconds"] = round(latency, 3)
    # Scale token counts realistically for Qwen tokenizer
    metrics["prompt_tokens"] = int(prompt_tokens * 1.3)
    metrics["completion_tokens"] = int(completion_tokens * 1.3)
    metrics["tokens_per_second"] = round(metrics["completion_tokens"] / latency, 2)
    
    return mock_response, metrics


def generate_mock_analyst_response(dataset_type):
    """
    Returns tailored McKinsey analyst insights based on dataset.
    """
    if dataset_type == "sales":
        data = {
            "business_summary": "ExecuDeck AI Business Analyst performed a strategic audit of the Q1-Q2 Sales dataset. The company exhibits robust top-line growth of 45% PoP, heavily driven by the 'Enterprise Cloud Suite' product in the North region. However, the East region represents an under-penetrated market with higher sales cycles, and average discounts for 'AI Security Agent' are compressing product margins by 8.5%.",
            "key_findings": [
                "Total revenue generated reached $240,000, with Enterprise Cloud Suite representing 62.5% ($150,000) of overall sales.",
                "North is the top-performing region, contributing $85,000 in revenue, whereas South and East are bottom performers.",
                "Average profit margin for SMB accounts is 33%, while Enterprise contracts operate at 41% margin.",
                "Outliers were detected in large West contracts, suggesting bespoke pricing structures."
            ],
            "important_metrics": [
                "Overall Growth Rate: +45.0% PoP",
                "Total Sales Revenue: $240,000",
                "Average Enterprise Cloud Suite Margin: 41%",
                "AI Security Agent Margin Compression: -8.5%"
            ],
            "risks": [
                "East region sales performance is stagnating, showing a decline in unit volume.",
                "AI Security Agent pricing is overly reliant on heavy discounting (average 15% discount) to secure Mid-Market contracts."
            ],
            "opportunities": [
                "Expand Analytics Dashboard features to SMB segments where transaction volumes are growing rapidly.",
                "Cross-sell AI Security Agent to existing Enterprise Cloud Suite customers in the North and West regions."
            ],
            "recommendations": [
                "Establish a minimum margin floor of 35% on AI Security Agent contracts to prevent further margin compression.",
                "Reallocate 15% of marketing budget from East to North region to capitalize on higher conversion rates.",
                "Standardize enterprise contracts in the West region to reduce legal overhead and contract cycle duration."
            ]
        }
    elif dataset_type == "finance":
        data = {
            "business_summary": "The finance data analysis reveals a minor Q1-Q4 budget overspend of 3.2% across departments, primarily driven by Research & Development (R&D) which exceeded projections by $55,000. Sales & Marketing successfully optimized spends in Q3, resulting in a favorable variance of $20,000. Operations margins remain stable, but customer support costs are climbing due to increased headcounts.",
            "key_findings": [
                "Total spent across all quarters reached $4,680,000 against a budget of $4,530,000, representing a $150,000 budget overrun.",
                "Research & Development spent $1,170,000 vs a budget of $1,120,000 due to accelerated chip prototyping schedules.",
                "Sales & Marketing is the largest cost center, accounting for 40.2% of total corporate spending.",
                "Operations and Support expenses remained within a +/- 2% band of original budget estimates."
            ],
            "important_metrics": [
                "Total Corporate Spend: $4.68M",
                "R&D Overrun: +4.9% ($55k)",
                "Sales & Marketing Share: 40.2%",
                "Budget Variance: -3.2% (Unfavorable)"
            ],
            "risks": [
                "Accelerating R&D spends could impact short-term operating cash flows if product releases are delayed.",
                "Operations overhead is growing, with G&A costs expanding on a quarter-over-quarter basis."
            ],
            "opportunities": [
                "Implement automated support workflows to offset rising customer support headcount costs.",
                "Renegotiate commercial marketing contracts to capture volume discounts in Q4."
            ],
            "recommendations": [
                "Establish a strict Q3-Q4 cap on non-essential R&D operational expenses.",
                "Transition customer support hiring to lower-cost hubs, targeting a 12% operational saving.",
                "Introduce automated budget alerts inside ERP tool when any cost center exceeds 90% budget in a quarter."
            ]
        }
    elif dataset_type == "hr":
        data = {
            "business_summary": "An executive review of the corporate headcount data reveals strong employee satisfaction (4.2/5) in Engineering, but alarming turnover risks in Sales where satisfaction has dropped to 3.8/5. The average salary across the firm is $98,500, with a positive correlation between employee satisfaction and performance scores.",
            "key_findings": [
                "Total employee count is 137, with Engineering accounting for the largest headcount block (65 employees).",
                "Engineering roles command the highest salaries, averaging $123,333, while Operations averages $76,666.",
                "Sales representatives exhibit the lowest average satisfaction rating (3.8) and have a performance score average of 78.5%.",
                "Operations has the highest employee satisfaction, peaking at 4.6 in the Office Manager role."
            ],
            "important_metrics": [
                "Total Headcount: 137 employees",
                "Engineering Average Salary: $123,333",
                "Sales Satisfaction: 3.8 / 5.0",
                "Average Performance Score: 83.2%"
            ],
            "risks": [
                "Low satisfaction in Sales leads to high talent attrition, increasing recruitment costs.",
                "Underperformance in sales roles directly impacts customer acquisition and corporate revenue targets."
            ],
            "opportunities": [
                "Introduce employee wellness programs in Sales to boost satisfaction ratings.",
                "Create a clear technical career ladder in Engineering to retain top Data Scientists."
            ],
            "recommendations": [
                "Restructure Sales commission models to incentivize performance and boost job satisfaction.",
                "Implement leadership coaching for Sales management to address structural employee relations issues.",
                "Perform an annual compensation review for Data Scientists to align with market benchmarks."
            ]
        }
    else:
        data = {
            "business_summary": "Executive analysis of the uploaded enterprise dataset. Overall metrics show stable operations with minor anomalies in distribution. Key categories account for the majority of the variance, presenting concrete strategic opportunities.",
            "key_findings": [
                "Total records profiled: 100, showing uniform data coverage across standard columns.",
                "Primary metrics align with seasonal historical averages, with variance constrained under 5%.",
                "Top categories represent 75% of overall values, indicating high consolidation.",
                "Anomalies detected in minor fields require clean validation workflows."
            ],
            "important_metrics": [
                "Total Records: 100",
                "Variance: <5.0%",
                "Top Category Share: 75.0%",
                "Missing Values: 0.0%"
            ],
            "risks": [
                "High category consolidation exposes the firm to supply chain or segment-specific shocks.",
                "Operational metrics show slight stagnation over the past 30 days."
            ],
            "opportunities": [
                "Diversify operations to lower-performing categories to capture untapped market shares.",
                "Leverage high-performing segments to upsell secondary offerings."
            ],
            "recommendations": [
                "Conduct a deep-dive segment analysis of the top category to optimize asset allocation.",
                "Establish alert thresholds for operational metrics to detect stagnation early.",
                "Streamline backend data collection to eliminate minor statistical anomalies."
            ]
        }
        
    return json.dumps(data)

def generate_mock_planner_response(dataset_type, slide_count):
    """
    Returns slide structures matching target count and dataset content.
    """
    slides = []
    
    # Slide 1: Title
    slides.append({
        "title": "ExecuDeck Executive Review",
        "purpose": "Introduce the presentation deck scope and strategic coverage.",
        "bullet_points": [
            "Comprehensive review of recent operational and financial metrics",
            "Data-backed analysis powered by Qwen open-source LLM on AMD GPUs",
            "Key strategic recommendations and implementation roadmap"
        ],
        "visual_required": "None",
        "speaker_notes": "Welcome team. Today we are walking through the executive presentation compiled by ExecuDeck AI."
    })
    
    # Slide 2: Executive Summary
    slides.append({
        "title": "Executive Summary & Context",
        "purpose": "Provide high-level takeaways for executive alignment.",
        "bullet_points": [
            "Overall business performance is strong, but operational bottlenecks require immediate focus.",
            "Identified margin compression in core segments and budget variances in R&D.",
            "Actionable recommendations targeting a 15% increase in operational efficiency."
        ],
        "visual_required": "None",
        "speaker_notes": "Let's align on the executive summary. The core message is that growth is stable, but we must address operational inefficiencies immediately."
    })
    
    # Middle Slides (charts/narratives)
    num_middle_slides = slide_count - 3 # minus title, exec summary, recommendations
    if num_middle_slides < 1:
        num_middle_slides = 1
        
    visuals = ["Bar Chart", "Line Chart", "Distribution Chart", "Comparison Chart"]
    
    for i in range(num_middle_slides):
        idx = i + 1
        visual = visuals[i % len(visuals)]
        
        if dataset_type == "sales":
            if visual == "Bar Chart":
                title = "Regional Sales Distribution"
                bullets = [
                    "North region is the primary revenue engine, contributing $85,000.",
                    "East region requires targeted intervention to improve unit velocity.",
                    "SMB and Enterprise segments exhibit distinct purchasing behaviors."
                ]
            elif visual == "Line Chart":
                title = "Sales Trends & Period Growth"
                bullets = [
                    "Sales grew 45% period-over-period, peaking in mid-Q2.",
                    "Enterprise Cloud Suite contracts show high recurring revenue stability.",
                    "Average transaction size expanded by 12% over the last quarter."
                ]
            elif visual == "Comparison Chart":
                title = "Segment Margin Comparison"
                bullets = [
                    "Enterprise accounts operate at 41% profit margin.",
                    "Mid-Market accounts are experiencing compression due to AI Security discounts.",
                    "SMB accounts hold a steady 33% margin with low cost-to-serve profiles."
                ]
            else:
                title = "Performance Metrics Highlight"
                bullets = [
                    "AI Security Agent volume represents 28% of total unit count.",
                    "Customer segments are shifting towards subscription-based offerings.",
                    "Key accounts show higher renewal rates, offsetting acquisition friction."
                ]
        elif dataset_type == "finance":
            if visual == "Bar Chart":
                title = "Cost Center Budget Allocation"
                bullets = [
                    "Sales & Marketing represents the largest cost block at 40.2%.",
                    "R&D spend has accelerated to accommodate hardware prototyping.",
                    "Operations and G&A spends remain highly stable."
                ]
            elif visual == "Line Chart":
                title = "Quarterly Spend Trends"
                bullets = [
                    "Total spend increased from Q1 to Q4 by 14% overall.",
                    "Q3 showed favorable variance due to marketing budget optimizations.",
                    "Q4 expenses spiked due to end-of-year capital acquisitions."
                ]
            elif visual == "Comparison Chart":
                title = "Budget vs Actual Spend Variance"
                bullets = [
                    "R&D holds an unfavorable budget variance of +4.9% ($55,000).",
                    "Customer Support has an overrun of $5,000 due to support agent hiring.",
                    "Sales & Marketing finished the fiscal year with a net positive variance."
                ]
            else:
                title = "Operations Expense Profiles"
                bullets = [
                    "General & Administrative expenses are aligned with forecast models.",
                    "Operational cost control measures prevented runaway inflation.",
                    "IT and Infrastructure spends represent a stable 8% of overhead."
                ]
        else: # hr or generic
            if visual == "Bar Chart":
                title = "Headcount Distribution by Department"
                bullets = [
                    "Engineering represents 47.4% of total corporate headcount.",
                    "Sales holds 25 employees with significant hiring plans in Q3.",
                    "Operations remains lean with only 17 employees overall."
                ]
            elif visual == "Line Chart":
                title = "Compensation & Performance Scaling"
                bullets = [
                    "Average salary is positive correlated with employee performance scores.",
                    "High-performing engineers average $125,000 base compensation.",
                    "Operations averages $76,666 salary, showing stable tenure rates."
                ]
            elif visual == "Comparison Chart":
                title = "Employee Satisfaction Ratings"
                bullets = [
                    "Engineering satisfaction is high at 4.2 out of 5.0.",
                    "Sales satisfaction is a critical risk area, averaging 3.8.",
                    "Operations displays high morale, led by Office Managers at 4.6."
                ]
            else:
                title = "Department Productivity Metrics"
                bullets = [
                    "Engineering performance scores average 85.5% overall.",
                    "Sales performance exhibits wider variance, averaging 78.5%.",
                    "Operations roles show highest stability and lowest churn."
                ]
                
        slides.append({
            "title": title,
            "purpose": f"Analyze business performance using a {visual}.",
            "bullet_points": bullets,
            "visual_required": visual,
            "speaker_notes": f"Turning to Slide {idx + 2}. This slide shows our performance metrics. As you can see, the data points to clear trends."
        })
        
    # Final Slide: Recommendations
    slides.append({
        "title": "Strategic Recommendations & Next Steps",
        "purpose": "Provide concrete strategic actions for implementation.",
        "bullet_points": [
            "Adjust target metrics and reallocate marketing/operational budgets.",
            "Establish strict margin floors and budget caps to protect bottom line.",
            "Review operational plans and implement dashboard alerts to track progress."
        ],
        "visual_required": "None",
        "speaker_notes": "Finally, let's review the strategic next steps. I recommend we implement these changes over the next 90 days."
    })
    
    # Enforce target count by slicing or duplicating the middle slide if needed
    if len(slides) > slide_count:
        # Keep slide 1, slide 2, recommendations slide, and slice the middle
        mid_slides = slides[2:-1]
        keep_count = slide_count - 3
        if keep_count > 0:
            slides = slides[:2] + mid_slides[:keep_count] + [slides[-1]]
        else:
            slides = slides[:slide_count]
            
    return json.dumps({"slides": slides})

def generate_mock_evaluator_response():
    """
    Returns presentation quality evaluation report.
    """
    data = {
        "overall_score": "88/100",
        "clarity": "Strong slide headlines, clear logical hierarchy. Bullet points are concise and read well.",
        "insight_depth": "Excellent use of specific numbers and categories. Captures margins, PoP growth, and overspends clearly.",
        "executive_readiness": "High. The vocabulary is strategic and McKinsey-aligned. Visual suggestions match the data trends.",
        "suggestions": [
            "On the regional distribution slide, emphasize the top region (North) in bold text.",
            "Add a timeline graphic on the recommendations slide to show 30-60-90 day milestones.",
            "In the executive summary, explicitly mention that the AI inference was run locally for data privacy."
        ]
    }
    return json.dumps(data)
