import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path

# Set Streamlit Page Config first
st.set_page_config(
    page_title="ExecuDeck AI — AMD GPU Accelerated Deck Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import module functions
import config
from modules.data_analyzer import load_dataset, analyze_dataset
from modules.context_builder import build_dataset_context
from modules.presentation_agent import run_business_analyst, run_presentation_planner
from modules.chart_engine import create_chart
from modules.ppt_builder import build_presentation
from modules.quality_evaluator import evaluate_presentation_quality
from modules.metrics import TelemetryTracker, get_rocm_gpu_stats, get_system_telemetry

# Custom CSS for executive look and feel
st.markdown("""
<style>
    /* Styling Main App */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Title Styling */
    .app-header {
        background: linear-gradient(135deg, #1B365D 0%, #007ACC 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 6px solid #D99B26;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .app-title {
        color: #ffffff !important;
        font-family: 'Georgia', serif;
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
    }
    
    .app-subtitle {
        color: #e1e1e1 !important;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Card/Div Styling */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 1.25rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #D99B26;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #8b949e;
        margin-bottom: 0.2rem;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161b22;
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
        color: #c9d1d9;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #21262d;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1f6feb !important;
        color: white !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #1B365D 0%, #0D2646 100%) !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #007ACC 0%, #1B365D 100%) !important;
        border-color: #58a6ff !important;
        box-shadow: 0 0 10px rgba(88,166,255,0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "tracker" not in st.session_state:
    st.session_state.tracker = TelemetryTracker()
if "df" not in st.session_state:
    st.session_state.df = None
if "df_profile" not in st.session_state:
    st.session_state.df_profile = None
if "dataset_context" not in st.session_state:
    st.session_state.dataset_context = None
if "insights" not in st.session_state:
    st.session_state.insights = None
if "outline" not in st.session_state:
    st.session_state.outline = None
if "chart_paths" not in st.session_state:
    st.session_state.chart_paths = {}
if "presentation_path" not in st.session_state:
    st.session_state.presentation_path = None
if "quality_report" not in st.session_state:
    st.session_state.quality_report = None
if "evaluation_metrics" not in st.session_state:
    st.session_state.evaluation_metrics = None

# Sidebar Configuration Panel
st.sidebar.image("https://img.icons8.com/color/96/powerpoint.png", width=64)
st.sidebar.markdown("### ExecuDeck AI Settings")

# Connection Indicator
if config.VLLM_ACTIVE:
    st.sidebar.success("🟢 vLLM GPU Server Active")
else:
    st.sidebar.warning("🟠 Local Fallback Mode Active")

# Audience Selector
audience = st.sidebar.selectbox(
    "Target Presentation Audience",
    ["CEO", "CFO", "Manager", "Technical"],
    index=0,
    help="Styles McKinsey prompt analysis and slide terminology for the reader."
)

# Theme Selector
theme = st.sidebar.selectbox(
    "Visual Theme Style",
    ["Corporate", "Minimal", "Consulting"],
    index=0,
    help="Applies distinct color palettes, typography, and structure to slides & charts."
)

# Slide Count
slide_count = st.sidebar.slider(
    "Number of Slides",
    min_value=3,
    max_value=15,
    value=6,
    step=1,
    help="Target total slide count (including Title and Recommendations slides)."
)

# Environment variables overrides (Accordion style)
with st.sidebar.expander("Telemetry & Endpoint Config"):
    env_mode = st.selectbox("Execution Mode Override", ["local", "amd_gpu"], index=0 if config.EXECUTION_MODE == "local" else 1)
    base_url = st.text_input("vLLM Base URL", value=config.VLLM_BASE_URL)
    model_name = st.text_input("Model Name", value=config.MODEL_NAME)
    
    if st.button("Apply Config Changes"):
        os.environ["EXECUTION_MODE"] = env_mode
        os.environ["VLLM_BASE_URL"] = base_url
        os.environ["MODEL_NAME"] = model_name
        config.EXECUTION_MODE = env_mode.lower()
        config.VLLM_BASE_URL = base_url
        config.MODEL_NAME = model_name
        # Re-check vLLM
        config.VLLM_ACTIVE = config.check_vllm_connection()
        st.session_state.tracker.reset()
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(
    "**Enterprise Data Privacy Guarantee:**\n\n"
    "All business data remain locally stored on your secure AMD ROCm node. "
    "LLM Inference runs locally through vLLM on target AMD GPUs. "
    "No data is sent to external APIs."
)

# Header Section
st.markdown("""
<div class="app-header">
    <h1 class="app-title">ExecuDeck AI</h1>
    <div class="app-subtitle">AMD GPU Accelerated Executive Presentation Generator</div>
</div>
""", unsafe_allow_html=True)

# Main Application Layout Tabs
tabs = st.tabs([
    "📂 Upload & Profile", 
    "📈 Data Intelligence", 
    "💼 Analyst Insights", 
    "🖥️ Presentation Deck", 
    "🎯 Presentation Quality",
    "⚡ AMD Telemetry Hub"
])

# ---- TAB 1: UPLOAD & PROFILER ----
with tabs[0]:
    st.markdown("### Upload Business Dataset")
    st.markdown("Select a sample dataset or upload your own CSV/Excel file.")
    
    # Pre-packaged demo selector
    demo_choice = st.selectbox(
        "Load Demo Dataset",
        ["-- None --", "Sales Transaction Ledger (sales_demo.csv)", "Departmental Budgets (finance_demo.csv)", "Employee Headcount & Morale (hr_demo.csv)"],
        index=0
    )
    
    uploaded_file = st.file_uploader("Upload CSV or Excel dataset file", type=["csv", "xlsx", "xls"])
    
    selected_df_path = None
    if demo_choice != "-- None --":
        if "sales_demo.csv" in demo_choice:
            selected_df_path = config.SAMPLE_DATA_DIR / "sales_demo.csv"
        elif "finance_demo.csv" in demo_choice:
            selected_df_path = config.SAMPLE_DATA_DIR / "finance_demo.csv"
        elif "hr_demo.csv" in demo_choice:
            selected_df_path = config.SAMPLE_DATA_DIR / "hr_demo.csv"
            
    # Load dataset
    df = None
    if uploaded_file:
        try:
            df = load_dataset(uploaded_file)
            st.session_state.df = df
        except Exception as e:
            st.error(f"Error loading uploaded file: {e}")
    elif selected_df_path:
        try:
            df = load_dataset(selected_df_path)
            st.session_state.df = df
        except Exception as e:
            st.error(f"Error loading demo file: {e}")
            
    if st.session_state.df is not None:
        current_df = st.session_state.df
        
        # Analyze data
        with st.spinner("Analyzing dataset structure..."):
            st.session_state.df_profile = analyze_dataset(current_df)
            st.session_state.dataset_context = build_dataset_context(current_df, st.session_state.df_profile)
            
        profile = st.session_state.df_profile
        
        # Grid preview
        st.markdown("#### Dataset Preview")
        st.dataframe(current_df.head(6), use_container_width=True)
        
        # Grid layout for summary metrics
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Records (Rows)</div>
                <div class="metric-value">{profile['dimensions']['rows']:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Dimensions (Columns)</div>
                <div class="metric-value">{profile['dimensions']['columns']}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            numeric_count = len(profile['metadata']['numeric_columns'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Numeric Columns</div>
                <div class="metric-value">{numeric_count}</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            categorical_count = len(profile['metadata']['categorical_columns'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Categorical Columns</div>
                <div class="metric-value">{categorical_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Data types and columns table
        st.markdown("#### Columns Analysis & Data Quality")
        col_summary_data = []
        for col, info in profile["column_profiles"].items():
            col_summary_data.append({
                "Column Name": col,
                "Data Type": info["dtype"],
                "Missing Records": info["missing_count"],
                "Missing Percentage": f"{info['missing_percentage']}%"
            })
        st.table(pd.DataFrame(col_summary_data))
    else:
        st.info("Please upload a file or load one of the pre-packaged demo datasets to begin.")

# ---- TAB 2: DATA INTELLIGENCE ----
with tabs[1]:
    if st.session_state.df_profile is not None:
        profile = st.session_state.df_profile
        
        st.markdown("### Data Intelligence Diagnostics")
        st.markdown("Pandas-engineered summaries reflecting core KPIs, correlations, outliers, and top performers.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Key Performance Indicators (KPIs)")
            if profile.get("kpis"):
                for kpi_name, val in profile["kpis"].items():
                    # Format nicely
                    display_name = kpi_name.replace("_", " ")
                    st.metric(label=display_name, value=f"{val:,.2f}" if isinstance(val, (int, float)) else str(val))
            else:
                st.write("No standard numeric KPIs detected in dataset.")
                
            st.markdown("#### Statistical Outliers & Anomalies")
            if profile.get("anomalies"):
                for col_name, info in profile["anomalies"].items():
                    st.error(
                        f"**{col_name}**: Outliers found: **{info['outlier_count']}** "
                        f"({info['outlier_percentage']}% of records). "
                        f"Expected bounds: [{info['bounds'][0]}, {info['bounds'][1]}]."
                    )
            else:
                st.success("No significant outliers detected using standard IQR boundary check.")
                
        with col2:
            st.markdown("#### Segment Performance Highlights")
            if profile.get("performers"):
                for performance_key, perf_data in profile["performers"].items():
                    metric_grouped = performance_key.replace("_by_", " grouped by ")
                    st.markdown(f"**{metric_grouped}**:")
                    st.markdown(f"- 🏆 **Top**: `{perf_data['top']['category']}` — **{perf_data['top']['value']:,.2f}**")
                    st.markdown(f"- 📉 **Bottom**: `{perf_data['bottom']['category']}` — **{perf_data['bottom']['value']:,.2f}**")
                    st.markdown("---")
            else:
                st.write("Insufficient categories/numerical columns to perform performer audits.")
                
            st.markdown("#### Time Trends & Period Growth")
            if profile.get("growth_patterns"):
                for metric_col, growth_info in profile["growth_patterns"].items():
                    st.markdown(f"**{metric_col} Trend:**")
                    st.markdown(f"- Range: `{growth_info['date_range'][0]}` to `{growth_info['date_range'][1]}`")
                    st.markdown(f"- Growth: **{growth_info['growth_percentage']}%** PoP")
            else:
                st.write("No date columns identified to map temporal growth patterns.")
                
            st.markdown("#### Notable Correlations")
            if profile.get("correlations"):
                for pair, score in profile["correlations"].items():
                    st.warning(f"🔗 **{pair.replace('_vs_', ' and ')}** correlate at **{score}**.")
            else:
                st.write("No significant correlation offsets discovered between numerical columns.")
    else:
        st.info("Dataset profile not loaded. Please upload a dataset in Tab 1.")

# ---- TAB 3: ANALYST INSIGHTS ----
with tabs[2]:
    if st.session_state.dataset_context is not None:
        st.markdown("### AI Business Analyst Insights")
        st.markdown("Generating strategic observations matching McKinsey consulting logic.")
        
        # Trigger Analyst
        if st.button("Generate Consulting Analysis"):
            with st.spinner("Executing McKinsey analyst inference (Local vLLM / fallback)..."):
                insights, metrics = run_business_analyst(st.session_state.dataset_context, audience)
                st.session_state.insights = insights
                st.session_state.tracker.add_call(metrics)
                
        if st.session_state.insights is not None:
            ins = st.session_state.insights
            
            # Show summary
            st.markdown("#### Executive Summary")
            st.info(ins.get("business_summary", ""))
            
            # Columns layout
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Key Findings")
                for finding in ins.get("key_findings", []):
                    st.markdown(f"📊 {finding}")
                    
                st.markdown("#### Metrics Highlighted")
                for metric in ins.get("important_metrics", []):
                    st.markdown(f"📈 **{metric}**")
                    
            with col2:
                st.markdown("#### Identified Risks")
                for risk in ins.get("risks", []):
                    st.markdown(f"⚠️ {risk}")
                    
                st.markdown("#### Strategic Opportunities")
                for opp in ins.get("opportunities", []):
                    st.markdown(f"💡 {opp}")
            
            st.markdown("---")
            st.markdown("#### Actionable Recommendations")
            for rec in ins.get("recommendations", []):
                st.markdown(f"👉 **{rec}**")
        else:
            st.info("Click the button above to run the AI Business Analyst Agent.")
    else:
        st.info("Dataset profile not loaded. Please upload a dataset in Tab 1.")

# ---- TAB 4: DECK GENERATOR ----
with tabs[3]:
    if st.session_state.insights is not None:
        st.markdown("### AI Widescreen Slide Deck Generator")
        st.markdown("Translates analysis findings into slide deck presentation structures and embeds generated charts.")
        
        # Trigger Presentation Outline
        if st.button("Generate Presentation Layout"):
            # Clear previous slide visual caches
            st.session_state.chart_paths = {}
            st.session_state.presentation_path = None
            st.session_state.quality_report = None
            
            with st.spinner("Structuring slide sequences..."):
                outline, metrics = run_presentation_planner(st.session_state.insights, slide_count, theme, audience)
                st.session_state.outline = outline
                st.session_state.tracker.add_call(metrics)
                
            # Create charts for slides that require visual elements
            if st.session_state.outline is not None:
                outline_slides = st.session_state.outline.get("slides", [])
                
                with st.spinner("Generating themed data charts..."):
                    for idx, slide_info in enumerate(outline_slides):
                        req_visual = slide_info.get("visual_required", "None")
                        if req_visual != "None":
                            chart_path = create_chart(st.session_state.df, req_visual, theme)
                            st.session_state.chart_paths[idx] = chart_path
                            
                # Compile slides into PowerPoint
                with st.spinner("Compiling PowerPoint presentation..."):
                    path = build_presentation(
                        slides_outline=st.session_state.outline,
                        df=st.session_state.df,
                        chart_paths=st.session_state.chart_paths,
                        theme=theme,
                        target_audience=audience
                    )
                    st.session_state.presentation_path = path
                    
        # Render presentation outline & files if ready
        if st.session_state.outline is not None:
            st.markdown("#### Widescreen Slide Layout Preview")
            
            slides = st.session_state.outline.get("slides", [])
            for idx, s in enumerate(slides):
                # Render each slide panel
                with st.expander(f"Slide {idx + 1}: {s.get('title', 'Untitled Slide')} (Visual: {s.get('visual_required', 'None')})"):
                    col_s1, col_s2 = st.columns([1.5, 1])
                    with col_s1:
                        st.markdown(f"**Purpose:** *{s.get('purpose', '')}*")
                        st.markdown("**Bullet Points:**")
                        for bp in s.get("bullet_points", []):
                            st.markdown(f"- {bp}")
                        st.markdown(f"**Presenter Notes:**\n`{s.get('speaker_notes', '')}`")
                    with col_s2:
                        # Display chart if generated
                        chart_file = st.session_state.chart_paths.get(idx)
                        if chart_file and os.path.exists(chart_file):
                            st.image(chart_file, caption=f"Generated visual: {s.get('visual_required')}")
                        else:
                            st.info("Text-only slide layout")
                            
            if st.session_state.presentation_path:
                st.success("PowerPoint generated successfully!")
                
                # Setup download button
                with open(st.session_state.presentation_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Widescreen PowerPoint Presentation",
                        data=file,
                        file_name=os.path.basename(st.session_state.presentation_path),
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )
        else:
            st.info("Click the button above to generate the PowerPoint outline.")
    else:
        st.info("Please generate AI Consultant Insights in Tab 3 first.")

# ---- TAB 5: PRESENTATION QUALITY ----
with tabs[4]:
    if st.session_state.outline is not None:
        st.markdown("### AI Presentation Quality Evaluator")
        st.markdown("Constructive audit rating slide metrics against McKinsey presentation guidelines.")
        
        # Explict evaluation trigger to save GPU
        if st.button("Evaluate Presentation Quality"):
            with st.spinner("Reviewing slide outline structures (Local vLLM / fallback)..."):
                report, metrics = evaluate_presentation_quality(st.session_state.outline, st.session_state.insights)
                st.session_state.quality_report = report
                st.session_state.tracker.add_call(metrics)
                
        if st.session_state.quality_report is not None:
            rep = st.session_state.quality_report
            
            # Show score in card style
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <div class="metric-label" style="font-size: 1.2rem;">McKinsey Executive Readiness Score</div>
                <div class="metric-value" style="font-size: 4rem; color: #D99B26;">{rep.get('overall_score', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Qualitative Metrics Analysis")
            st.markdown(f"✍️ **Slide Clarity:** {rep.get('clarity', '')}")
            st.markdown(f"🔍 **Insight Depth:** {rep.get('insight_depth', '')}")
            st.markdown(f"💼 **Executive Readiness:** {rep.get('executive_readiness', '')}")
            
            st.markdown("---")
            st.markdown("#### Improvement Suggestions")
            for sug in rep.get("suggestions", []):
                st.markdown(f"💡 {sug}")
        else:
            st.info("Click the button above to evaluate presentation quality. This checks narrative alignment and clarity.")
    else:
        st.info("Please generate the presentation slide layout in Tab 4 first.")

# ---- TAB 6: AMD TELEMETRY HUB ----
with tabs[5]:
    st.markdown("### AMD GPU Accelerated GenAI Telemetry Dashboard")
    st.markdown("Live execution performance profiles. Evaluators can track real-time AMD ROCm benchmarks here.")
    
    # Session summary
    sum_data = st.session_state.tracker.get_session_summary()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Model Inference Calls</div>
            <div class="metric-value">{sum_data['calls_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Token Footprint</div>
            <div class="metric-value">{sum_data['total_prompt_tokens'] + sum_data['total_completion_tokens']:,}</div>
            <div class="metric-label">Prompt: {sum_data['total_prompt_tokens']:,} | Gen: {sum_data['total_completion_tokens']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Average Inference Throughput</div>
            <div class="metric-value">{sum_data['avg_tokens_per_second']} t/s</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("#### Model Environment Status")
    
    # Display config stats
    st.markdown(f"🖥️ **Execution Mode:** `{config.EXECUTION_MODE.upper()}`")
    st.markdown(f"🏷️ **Active Model Name:** `{config.MODEL_NAME}`")
    st.markdown(f"🔗 **vLLM Endpoint URL:** `{config.VLLM_BASE_URL}`")
    
    st.markdown("---")
    st.markdown("#### AMD ROCm GPU Telemetry Status")
    
    # Live ROCm GPU query
    with st.spinner("Querying AMD ROCm device profile..."):
        gpu_stats = get_rocm_gpu_stats()
        
    if gpu_stats.get("status") == "Local Development Mode - GPU unavailable":
        st.warning("⚠️ **Local Development Mode Active - GPU unavailable**")
        st.info("System falls back to local simulation because `rocm-smi` is not detected in the local path.")
        
        # Display system CPU/RAM parameters
        sys_telemetry = get_system_telemetry()
        st.markdown("**Local Host Telemetry:**")
        st.markdown(f"- Host CPU Usage: **{sys_telemetry['cpu_usage_percentage']}%**")
        st.markdown(f"- Host RAM Usage: **{sys_telemetry['ram_usage_percentage']}%** ({sys_telemetry['ram_used_gb']} GB / {sys_telemetry['ram_total_gb']} GB)")
    else:
        st.success(f"🟢 **{gpu_stats.get('status')}**")
        if "total_vram" in gpu_stats:
            st.markdown(f"- Total GPU VRAM: **{gpu_stats['total_vram']}**")
            st.markdown(f"- Used GPU VRAM: **{gpu_stats['used_vram']}**")
        if "raw_data" in gpu_stats:
            st.json(gpu_stats["raw_data"])
