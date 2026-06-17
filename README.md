# ExecuDeck AI — AMD GPU Accelerated Executive Presentation Generator

ExecuDeck AI is an enterprise-grade GenAI application designed to automate the conversion of raw business datasets (CSV/Excel) into professional, widescreen (16:9) executive presentations. 

By utilizing **Qwen2.5-7B-Instruct** served via **vLLM** and accelerated on **AMD Instinct™ / Radeon™ GPUs using ROCm**, ExecuDeck AI provides rapid business analysis and slide outline generation with complete data privacy—your datasets never leave the secure AMD GPU environment.

---

## Technical Architecture

```
Dataset ➔ Data Profiler ➔ Dataset Context Builder ➔ Qwen Business Analyst Agent ➔ Presentation Storyline Planner ➔ Chart Generator (Matplotlib) ➔ PowerPoint Renderer (python-pptx)
```

---

## 1. Local Windows Setup Instructions

Develop, test, and preview the full application layout locally on your Windows machine using the high-fidelity mock fallback mode:

1. **Clone or Extract the Repository**:
   ```powershell
   git clone <your-repository-url>
   cd "ppt generator"
   ```

2. **Create and Activate a Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables**:
   Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```
   By default, `.env` configures `EXECUTION_MODE=local`, enabling local mock development fallback if no active vLLM server is detected.

5. **Run the Streamlit Application**:
   ```powershell
   streamlit run app.py
   ```

6. **Run the Verification Test Suite**:
   Test using the default small dataset:
   ```powershell
   python verify_setup.py
   ```
   Or verify using the large enterprise-grade dataset (~6,000 rows):
   ```powershell
   python verify_setup.py --large
   ```

---

## 2. GitHub Workflow

To sync code changes from your local development environment to the AMD ROCm GPU Notebook:

1. **Commit and Push changes locally**:
   ```powershell
   git add .
   git commit -m "feat: implement data intelligence profiling and McKinsey agents"
   git push origin main
   ```

2. **Pull changes inside the AMD ROCm Notebook**:
   ```bash
   git pull origin main
   ```

---

## 3. AMD Notebook Deployment Commands

When deploying inside the AMD Hackathon Notebook environment, apply these storage practices to avoid filling up the temporary notebook storage:

1. **Navigate to the Shared/Persistent workspace folder**:
   ```bash
   cd /workspace/shared
   ```

2. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd execudeck-ai
   ```

3. **Create your `.env` config file**:
   ```bash
   cat <<EOF > .env
   EXECUTION_MODE=amd_gpu
   VLLM_BASE_URL=http://localhost:8000/v1
   MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
   EOF
   ```

4. **Install ROCm-compatible PyTorch and standard dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 4. vLLM Startup Commands (AMD ROCm)

To serve the `Qwen/Qwen2.5-7B-Instruct` model efficiently on AMD hardware:

1. **Create the shared model cache directory**:
   Ensure you store HuggingFace weight downloads inside `/workspace/shared/model_cache` to keep root storage free:
   ```bash
   mkdir -p /workspace/shared/model_cache
   export HF_HOME=/workspace/shared/model_cache
   ```

2. **Start vLLM Server targeting AMD GPU (ROCm)**:
   ```bash
   python -m vllm.entrypoints.openai.api_server \
       --model Qwen/Qwen2.5-7B-Instruct \
       --port 8000 \
       --host 0.0.0.0 \
       --dtype float16 \
       --max-model-len 8192 \
       --gpu-memory-utilization 0.90 \
       --download-dir /workspace/shared/model_cache
   ```
   *Note: For multi-GPU Instinct nodes, configure tensor parallelism (e.g. `--tensor-parallel-size 2` or `4`).*

---

## 5. Demo Execution Steps

Showcase ExecuDeck AI end-to-end:

1. **Access the Streamlit Dashboard**: Open the local/forwarded port of your Streamlit server in your browser.
2. **Review Environment Settings**: In the sidebar, check that the status indicator shows **🟢 vLLM GPU Server Active** (or falls back to orange simulation mode if testing offline).
3. **Data Profiling**:
   - Go to the **Upload & Profile** tab.
   - Choose one of the pre-loaded datasets from `sample_data/` (or upload a custom CSV).
   - Review dimensions, data types, and missing values.
4. **Data Diagnostics**:
   - Go to the **Data Intelligence** tab.
   - Audit outlier flags, categorical top/bottom performers, and temporal growth metrics.
5. **AI Consultant Insights**:
   - Go to the **Analyst Insights** tab.
   - Select the target presentation audience (e.g., CEO or CFO).
   - Click **Generate Consulting Analysis** to run Qwen's strategic audit.
6. **Deck Generator**:
   - Go to the **Presentation Deck** tab.
   - Select your slide count (3-15) and visual theme (Corporate, Minimal, Consulting).
   - Click **Generate Presentation Layout**.
   - Review the generated slide previews and embedded Matplotlib charts.
   - Click **Download Widescreen PowerPoint Presentation** to save the `.pptx` file.
7. **Quality Audit (Optional)**:
   - Go to the **Presentation Quality** tab.
   - Click **Evaluate Presentation Quality** to receive a McKinsey-style readiness scorecard and editorial suggestions.
8. **AMD Telemetry**:
   - Review inference logs, latency, token count, generation speed, and live ROCm GPU metrics on the **AMD Telemetry Hub** tab.

---

## 6. Sample Datasets Information

The repository pre-packages datasets inside the [sample_data/](file:///c:/Users/Bhanuteja/Documents/ppt%20generator/sample_data) directory for instant execution and evaluation:

- **★ RECOMMENDED: `enterprise_sales_demo.csv`**: A robust, widescreen-formatted transactional sales ledger containing **6,000+ records** covering 2024 to 2026.
  - **Features**: Includes Transaction_ID, Date, Region, Country, Business_Unit, Product_Category, Product_Name, Customer_Segment, Sales_Channel, Units_Sold, Unit_Price, Revenue, Cost, Profit, Profit_Margin, Discount_Percentage, Customer_Rating, Quarter, and Year.
  - **Data Design & Strategic Insights**:
    - *Regional Performance*: North America drives the largest revenue share, Europe is stable, Asia-Pacific exhibits the fastest growth rates (high volume of GPU accelerators/API packages), while Latin America struggles with low volume and low margins.
    - *Seasonality*: Q4 exhibits sales surges (1.35x budget flushes), while Q1 experiences post-holiday contractions (0.80x).
    - *Outlier Anomaly*: ~1.2% of bulk Enterprise orders feature extreme discounts (55% - 75%), which trigger negative profit margins on expensive hardware items—intended for the Qwen Analyst to discover and address as a key margin risk.
    - *Underperforming Product*: `Smart Assistant Pro` exhibits poor rating averages (~3.2), suggesting a strategic quality-assurance or market-repositioning issue.
- `sales_demo.csv`: A smaller (20-row) sales ledger for quick system tests.
- `finance_demo.csv`: Departmental budgets tracking quarterly actual vs projected expenditures across R&D, G&A, and Sales.
- `hr_demo.csv`: Headcount rosters mapping employee average compensation, morale levels, and department scores.

*These datasets contain synthetic records and are intended for demonstration purposes only.*
