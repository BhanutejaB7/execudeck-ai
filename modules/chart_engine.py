import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import uuid
import config

def get_theme_colors(theme):
    """
    Returns primary, secondary, accent, and background colors based on presentation theme.
    """
    t = theme.lower()
    if t == "corporate":
        return {
            "primary": "#1B365D",   # Navy
            "secondary": "#4A777A", # Muted Slate
            "accent": "#D99B26",    # Corporate Gold
            "bg": "#FFFFFF",
            "grid": "#E0E0E0",
            "text": "#333333"
        }
    elif t == "consulting":
        return {
            "primary": "#2D5A27",   # Sage Green
            "secondary": "#4F5D75", # Slate Gray
            "accent": "#D1A153",    # Warm Ochre
            "bg": "#FAF9F6",        # Cream Muted
            "grid": "#E5E3DF",
            "text": "#2C2C2C"
        }
    else: # minimal (default)
        return {
            "primary": "#222222",   # Off-black
            "secondary": "#777777", # Cool Gray
            "accent": "#007ACC",    # Tech Blue
            "bg": "#FFFFFF",
            "grid": "#F0F0F0",
            "text": "#111111"
        }

def create_chart(df, chart_type, theme="minimal"):
    """
    Automatically creates a themed chart based on dataset properties and requested chart type.
    Saves the image to output_charts/ and returns its absolute path.
    """
    colors = get_theme_colors(theme)
    
    # Configure Matplotlib styles globally/locally for this chart
    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.family'] = 'sans-serif'
    
    fig, ax = plt.subplots(figsize=(6.5, 4.5), facecolor=colors["bg"])
    ax.set_facecolor(colors["bg"])
    
    # Identify numerical and categorical columns
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=[object, 'category']).columns.tolist()
    
    # Try to identify date columns
    date_col = None
    for col in df.columns:
        if col not in num_cols:
            try:
                # Test parse
                pd.to_datetime(df[col].dropna().head(3), errors='raise', format='mixed')
                date_col = col
                break
            except Exception:
                pass
                
    chart_type_lower = chart_type.lower()
    success = False
    
    try:
        if "line" in chart_type_lower and len(num_cols) > 0:
            success = _plot_line_chart(df, num_cols, date_col, colors, ax)
        elif "bar" in chart_type_lower and len(cat_cols) > 0 and len(num_cols) > 0:
            success = _plot_bar_chart(df, cat_cols, num_cols, colors, ax)
        elif "distribution" in chart_type_lower and len(num_cols) > 0:
            success = _plot_distribution_chart(df, num_cols, colors, ax)
        elif "comparison" in chart_type_lower and len(num_cols) >= 2:
            success = _plot_comparison_chart(df, cat_cols, num_cols, colors, ax)
            
        if not success:
            # Fallback plot if specific type failed or columns are insufficient
            _plot_fallback(df, num_cols, cat_cols, colors, ax)
            
    except Exception as e:
        # If anything breaks, render fallback
        ax.clear()
        ax.text(0.5, 0.5, f"Visual: {chart_type}\n(Dataset Summary)", 
                ha='center', va='center', fontsize=12, color=colors["text"])
        success = True
        
    # Apply standard styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(colors["secondary"])
    ax.spines['bottom'].set_color(colors["secondary"])
    
    ax.tick_params(axis='both', colors=colors["text"], labelsize=9)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.6, color=colors["grid"])
    
    plt.tight_layout()
    
    # Save chart file
    filename = f"chart_{chart_type_lower.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.png"
    filepath = config.OUTPUT_CHARTS_DIR / filename
    plt.savefig(filepath, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    
    return str(filepath)

def _plot_line_chart(df, num_cols, date_col, colors, ax):
    # Select target numeric column (e.g. Sales, Spend)
    target_num = _select_primary_numeric(num_cols)
    
    if date_col:
        # Sort by date
        temp_df = df.copy()
        temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce', format='mixed')
        temp_df = temp_df.dropna(subset=[date_col]).sort_values(by=date_col)
        
        # Aggregate by date to keep line chart clean
        daily = temp_df.groupby(date_col)[target_num].sum().reset_index()
        ax.plot(daily[date_col], daily[target_num], color=colors["primary"], 
                linewidth=2.5, marker='o', markersize=4, label=target_num)
        ax.set_xlabel(str(date_col), color=colors["text"], fontsize=10)
        # Rotate dates nicely
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    else:
        # Plot raw index
        ax.plot(df[target_num], color=colors["primary"], linewidth=2.5, marker='o', label=target_num)
        ax.set_xlabel("Records Index", color=colors["text"], fontsize=10)
        
    ax.set_ylabel(target_num, color=colors["text"], fontsize=10)
    ax.set_title(f"{target_num} Over Time / Sequence", color=colors["primary"], fontsize=12, fontweight='bold', pad=12)
    return True

def _plot_bar_chart(df, cat_cols, num_cols, colors, ax):
    target_cat = cat_cols[0]
    target_num = _select_primary_numeric(num_cols)
    
    # Group by category, sort values
    grouped = df.groupby(target_cat)[target_num].sum().sort_values(ascending=False).head(8)
    
    bars = ax.bar(grouped.index, grouped.values, color=colors["primary"], width=0.6)
    
    # Highlight top bar with accent color if theme permits
    if len(bars) > 0:
        bars[0].set_color(colors["accent"])
        
    ax.set_ylabel(f"Total {target_num}", color=colors["text"], fontsize=10)
    ax.set_xlabel(target_cat, color=colors["text"], fontsize=10)
    ax.set_title(f"{target_num} by {target_cat}", color=colors["primary"], fontsize=12, fontweight='bold', pad=12)
    plt.setp(ax.get_xticklabels(), rotation=25, ha='right')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}' if height >= 1000 else f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=colors["text"])
                    
    return True

def _plot_distribution_chart(df, num_cols, colors, ax):
    target_num = _select_primary_numeric(num_cols)
    series = df[target_num].dropna()
    
    # Plot histogram
    n, bins, patches = ax.hist(series, bins=min(10, len(series.unique())), 
                               color=colors["primary"], edgecolor=colors["bg"], alpha=0.85)
    
    # Highlight median line
    median_val = series.median()
    ax.axvline(median_val, color=colors["accent"], linestyle='--', linewidth=2, 
               label=f"Median: {median_val:,.1f}")
    
    ax.set_ylabel("Frequency", color=colors["text"], fontsize=10)
    ax.set_xlabel(target_num, color=colors["text"], fontsize=10)
    ax.set_title(f"Distribution of {target_num}", color=colors["primary"], fontsize=12, fontweight='bold', pad=12)
    ax.legend(frameon=False, loc='upper right', labelcolor=colors["text"])
    return True

def _plot_comparison_chart(df, cat_cols, num_cols, colors, ax):
    # Try to find a comparison, e.g. Budget vs Actual Spend
    compare_pairs = []
    
    # Check if budget/actual pair exists
    budget_cols = [c for c in num_cols if "budget" in c.lower()]
    actual_cols = [c for c in num_cols if any(t in c.lower() for t in ["actual", "spend", "sales", "profit"])]
    
    if budget_cols and actual_cols and len(cat_cols) > 0:
        target_cat = cat_cols[0]
        b_col = budget_cols[0]
        a_col = actual_cols[0]
        
        grouped = df.groupby(target_cat)[[b_col, a_col]].sum().head(5)
        x = np.arange(len(grouped))
        width = 0.35
        
        rects1 = ax.bar(x - width/2, grouped[b_col], width, label=b_col, color=colors["secondary"])
        rects2 = ax.bar(x + width/2, grouped[a_col], width, label=a_col, color=colors["primary"])
        
        # Color top performer with accent outline
        ax.set_xticks(x)
        ax.set_xticklabels(grouped.index)
        ax.set_ylabel("Amount", color=colors["text"], fontsize=10)
        ax.set_title(f"Comparison: {b_col} vs {a_col} by {target_cat}", 
                     color=colors["primary"], fontsize=11, fontweight='bold', pad=12)
        ax.legend(frameon=False, loc='upper right', labelcolor=colors["text"])
        plt.setp(ax.get_xticklabels(), rotation=20, ha='right')
        return True
        
    # If no natural comparison fields, scatter plot top 2 numeric metrics
    col1, col2 = num_cols[0], num_cols[1]
    ax.scatter(df[col1], df[col2], color=colors["primary"], edgecolors=colors["bg"], s=60, alpha=0.8)
    ax.set_xlabel(col1, color=colors["text"], fontsize=10)
    ax.set_ylabel(col2, color=colors["text"], fontsize=10)
    ax.set_title(f"Comparison: {col1} vs {col2}", color=colors["primary"], fontsize=12, fontweight='bold', pad=12)
    return True

def _plot_fallback(df, num_cols, cat_cols, colors, ax):
    # Plot simple bar chart of records count by first categorical, or values of first numeric
    if len(num_cols) > 0:
        col = num_cols[0]
        ax.plot(df[col].head(20), color=colors["primary"], linewidth=2)
        ax.set_title(f"Dataset Overview ({col})", color=colors["primary"], fontsize=12)
    else:
        ax.text(0.5, 0.5, "Preview Summary Chart", ha='center', va='center', color=colors["text"])

def _select_primary_numeric(num_cols):
    """
    Selects the most executive-friendly column name to plot (e.g. sales, profit, revenue)
    """
    for col in num_cols:
        col_lower = col.lower()
        if any(term in col_lower for term in ["sales", "revenue", "spend", "profit", "actual_spend"]):
            return col
    return num_cols[0]
