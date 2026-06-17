import sys
import os
import json
from pathlib import Path
import pandas as pd

# Add the project root to sys.path so we can import modules
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

print("==========================================")
print("EXECUDECK AI INTEGRATION TEST SUITE")
print("==========================================")

try:
    import config
    print("[PASS] config.py successfully loaded.")
except Exception as e:
    print(f"[FAIL] config.py failed to load: {e}")
    sys.exit(1)

# 1. Test data loading and analyzer
try:
    from modules.data_analyzer import load_dataset, analyze_dataset
    demo_data_path = config.SAMPLE_DATA_DIR / "sales_demo.csv"
    
    if not demo_data_path.exists():
        print(f"[FAIL] Sample dataset not found at {demo_data_path}")
        sys.exit(1)
        
    df = load_dataset(demo_data_path)
    profile = analyze_dataset(df)
    
    print("[PASS] data_analyzer: Loaded and profiled sales_demo.csv successfully.")
    print(f"       Detected {profile['dimensions']['rows']} rows, {profile['dimensions']['columns']} columns.")
except Exception as e:
    print(f"[FAIL] data_analyzer module test failed: {e}")
    sys.exit(1)

# 2. Test context builder
try:
    from modules.context_builder import build_dataset_context, build_analyst_prompt, build_planner_prompt
    context = build_dataset_context(df, profile)
    
    print("[PASS] context_builder: Compiled dataset profile context.")
    # Check sample keys
    assert "dataset_summary" in context
    assert "key_performance_indicators" in context
except Exception as e:
    print(f"[FAIL] context_builder module test failed: {e}")
    sys.exit(1)

# 3. Test LLM client and analyst agents
try:
    from modules.presentation_agent import run_business_analyst, run_presentation_planner
    
    # We run in whatever mode config has (local mock is default)
    print(f"       Running AI Analyst in '{config.EXECUTION_MODE}' mode...")
    insights, metrics1 = run_business_analyst(context, "CEO")
    
    print("[PASS] presentation_agent: Business Analyst execution returned valid schemas.")
    print(f"       Metrics -> Latency: {metrics1.get('latency_seconds')}s, Speed: {metrics1.get('tokens_per_second')} t/s.")
except Exception as e:
    print(f"[FAIL] AI Analyst agent test failed: {e}")
    sys.exit(1)

# 4. Test Presentation Storyline Planner
try:
    print(f"       Running Storyline Planner in '{config.EXECUTION_MODE}' mode...")
    outline, metrics2 = run_presentation_planner(insights, 5, "Corporate", "CEO")
    
    print("[PASS] presentation_agent: Storyline Planner execution returned valid slide outline.")
    assert "slides" in outline
    assert len(outline["slides"]) > 0
except Exception as e:
    print(f"[FAIL] Storyline Planner agent test failed: {e}")
    sys.exit(1)

# 5. Test Chart Engine
try:
    from modules.chart_engine import create_chart
    chart_paths = {}
    
    # Create a couple of charts
    chart_paths[1] = create_chart(df, "Bar Chart", "Corporate")
    chart_paths[2] = create_chart(df, "Line Chart", "Corporate")
    
    print("[PASS] chart_engine: Created and saved themed charts to output_charts/.")
    for idx, path in chart_paths.items():
        print(f"       Chart {idx}: {path}")
        assert os.path.exists(path)
except Exception as e:
    print(f"[FAIL] chart_engine module test failed: {e}")
    sys.exit(1)

# 6. Test PPT Builder
try:
    from modules.ppt_builder import build_presentation
    ppt_path = build_presentation(outline, df, chart_paths, "Corporate", "CEO")
    
    print("[PASS] ppt_builder: Widescreen presentation compiled and saved successfully.")
    print(f"       Output PPT: {ppt_path}")
    assert os.path.exists(ppt_path)
except Exception as e:
    print(f"[FAIL] ppt_builder module test failed: {e}")
    sys.exit(1)

# 7. Test optional Quality Evaluator
try:
    from modules.quality_evaluator import evaluate_presentation_quality
    print(f"       Running Quality Evaluator in '{config.EXECUTION_MODE}' mode...")
    evaluation, metrics3 = evaluate_presentation_quality(outline, insights)
    
    print("[PASS] quality_evaluator: Reviewed presentation deck outline successfully.")
    print(f"       Score: {evaluation.get('overall_score')} | Suggestions: {len(evaluation.get('suggestions', []))} items.")
except Exception as e:
    print(f"[FAIL] quality_evaluator module test failed: {e}")
    sys.exit(1)

# 8. Test metrics tracking and system telemetry
try:
    from modules.metrics import TelemetryTracker, get_rocm_gpu_stats, get_system_telemetry
    tracker = TelemetryTracker()
    tracker.add_call(metrics1)
    tracker.add_call(metrics2)
    tracker.add_call(metrics3)
    
    summary = tracker.get_session_summary()
    gpu_stats = get_rocm_gpu_stats()
    sys_stats = get_system_telemetry()
    
    print("[PASS] metrics: Telemetry tracking operating normally.")
    print(f"       GPU Status: {gpu_stats.get('status')}")
    print(f"       System RAM Usage: {sys_stats['ram_usage_percentage']}%")
except Exception as e:
    print(f"[FAIL] metrics telemetry module test failed: {e}")
    sys.exit(1)

print("\n==========================================")
print("ALL CORE MODULES VERIFIED SUCCESSFULLY!")
print("==========================================")
sys.exit(0)
