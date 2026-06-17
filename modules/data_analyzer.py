import pandas as pd
import numpy as np

def load_dataset(file_path):
    """
    Loads CSV or Excel datasets safely.
    Returns:
        pd.DataFrame: Loaded dataframe
    """
    file_path_str = str(file_path)
    if file_path_str.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path_str.endswith(('.xls', '.xlsx')):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

def analyze_dataset(df):
    """
    Performs comprehensive numerical, categorical, KPI, trend, and anomaly analysis.
    Returns:
        dict: Detailed statistics profile of the dataset
    """
    profile = {}
    
    # 1. Dataset Dimensions and Missing Values
    rows, cols = df.shape
    profile["dimensions"] = {"rows": rows, "columns": cols}
    
    missing_analysis = {}
    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        missing_pct = float((missing_count / rows) * 100)
        missing_analysis[col] = {
            "missing_count": missing_count,
            "missing_percentage": round(missing_pct, 2),
            "dtype": str(df[col].dtype)
        }
    profile["column_profiles"] = missing_analysis

    # Separate numerical and categorical columns
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=[object, 'category']).columns.tolist()
    
    # Try to identify potential Date/Time columns
    date_cols = []
    for col in df.columns:
        if col not in num_cols:
            try:
                # If it's a string, see if it can be converted to datetime
                sample = df[col].dropna().head(10)
                if not sample.empty:
                    # format='mixed' avoids warnings in modern pandas versions
                    parsed = pd.to_datetime(sample, errors='coerce', format='mixed')
                    if parsed.notnull().sum() / len(sample) > 0.7: # 70% or more parsed
                        date_cols.append(col)
            except Exception:
                pass
                
    # Remove dates from standard categoricals if they were classified there
    for d_col in date_cols:
        if d_col in cat_cols:
            cat_cols.remove(d_col)
            
    profile["metadata"] = {
        "numeric_columns": num_cols,
        "categorical_columns": cat_cols,
        "date_columns": date_cols
    }

    # 2. Numerical Summary & Anomaly Detection (IQR method)
    numerical_summary = {}
    anomalies = {}
    for col in num_cols:
        series = df[col].dropna()
        if series.empty:
            continue
            
        desc = series.describe()
        q1 = float(desc.get("25%", 0))
        q3 = float(desc.get("75%", 0))
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Outliers
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col].tolist()
        
        numerical_summary[col] = {
            "mean": round(float(desc["mean"]), 2),
            "std": round(float(desc["std"]), 2) if not pd.isna(desc["std"]) else 0.0,
            "min": float(desc["min"]),
            "max": float(desc["max"]),
            "median": float(desc["50%"]),
            "q1": q1,
            "q3": q3
        }
        
        if len(outliers) > 0:
            anomalies[col] = {
                "outlier_count": len(outliers),
                "outlier_percentage": round((len(outliers) / len(series)) * 100, 2),
                "bounds": [round(lower_bound, 2), round(upper_bound, 2)]
            }
            
    profile["numerical_summaries"] = numerical_summary
    profile["anomalies"] = anomalies

    # 3. Categorical Summaries
    categorical_summary = {}
    for col in cat_cols:
        series = df[col].dropna()
        if series.empty:
            continue
            
        value_counts = series.value_counts()
        cardinality = len(value_counts)
        top_cats = value_counts.head(5).to_dict()
        top_cats_pct = {k: round((v / len(series)) * 100, 2) for k, v in top_cats.items()}
        
        categorical_summary[col] = {
            "cardinality": cardinality,
            "top_categories_count": top_cats,
            "top_categories_percentage": top_cats_pct,
            "mode": str(series.mode().iloc[0]) if not series.mode().empty else "None"
        }
    profile["categorical_summaries"] = categorical_summary

    # 4. KPIs Auto-calculation
    kpis = {}
    # Common KPI detection
    for col in num_cols:
        col_lower = col.lower()
        if any(term in col_lower for term in ["sales", "revenue", "turnover", "budget"]):
            kpis[f"Total_{col}"] = round(float(df[col].sum()), 2)
            kpis[f"Average_{col}"] = round(float(df[col].mean()), 2)
        elif any(term in col_lower for term in ["profit", "earnings", "net_income"]):
            kpis[f"Total_{col}"] = round(float(df[col].sum()), 2)
            kpis[f"Average_{col}"] = round(float(df[col].mean()), 2)
        elif any(term in col_lower for term in ["margin", "roi", "satisfaction", "score", "rate"]):
            kpis[f"Average_{col}"] = round(float(df[col].mean()), 2)
            
    profile["kpis"] = kpis

    # 5. Top & Bottom Performers
    performers = {}
    # Group numerical metrics by categories to find top/bottom performers
    for cat in cat_cols[:3]: # Limit to top 3 categorical columns to keep profile compact
        for num in num_cols[:3]: # Limit to top 3 numerical columns
            # Group and find top and bottom
            grouped = df.groupby(cat)[num].sum().sort_values(ascending=False)
            if len(grouped) >= 2:
                performers[f"{num}_by_{cat}"] = {
                    "top": {"category": str(grouped.index[0]), "value": round(float(grouped.iloc[0]), 2)},
                    "bottom": {"category": str(grouped.index[-1]), "value": round(float(grouped.iloc[-1]), 2)}
                }
    profile["performers"] = performers

    # 6. Trends & Growth
    growth = {}
    if len(date_cols) > 0:
        date_col = date_cols[0]
        # Make a copy of df with parsed date
        temp_df = df.copy()
        # format='mixed' silences warnings in modern pandas
        temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce', format='mixed')
        temp_df = temp_df.dropna(subset=[date_col]).sort_values(by=date_col)
        
        if not temp_df.empty:
            # Pick a representative numeric metric, e.g., Sales, Profit, Spend, or the first numeric col
            target_metric = None
            for col in num_cols:
                if any(term in col.lower() for term in ["sales", "revenue", "spend", "actual_spend", "profit"]):
                    target_metric = col
                    break
            if not target_metric and len(num_cols) > 0:
                target_metric = num_cols[0]
                
            if target_metric:
                # Split in half to see PoP growth
                mid_point = len(temp_df) // 2
                first_half = temp_df.iloc[:mid_point][target_metric].sum()
                second_half = temp_df.iloc[mid_point:][target_metric].sum()
                
                growth_val = 0.0
                if first_half > 0:
                    growth_val = round(((second_half - first_half) / first_half) * 100, 2)
                    
                growth[target_metric] = {
                    "first_half_sum": round(float(first_half), 2),
                    "second_half_sum": round(float(second_half), 2),
                    "growth_percentage": growth_val,
                    "date_range": [str(temp_df[date_col].min().date()), str(temp_df[date_col].max().date())]
                }
    profile["growth_patterns"] = growth

    # 7. Correlation Analysis
    correlations = {}
    if len(num_cols) >= 2:
        corr_matrix = df[num_cols].corr().round(3).fillna(0.0)
        # Find high correlations
        for i in range(len(num_cols)):
            for j in range(i+1, len(num_cols)):
                col1 = num_cols[i]
                col2 = num_cols[j]
                val = float(corr_matrix.loc[col1, col2])
                if abs(val) > 0.3: # moderate to high correlation
                    correlations[f"{col1}_vs_{col2}"] = val
                    
    profile["correlations"] = correlations
    
    return profile
