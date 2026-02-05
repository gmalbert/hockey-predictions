"""Custom Streamlit styling."""
import streamlit as st


def apply_custom_css():
    """Apply custom CSS styles to the Streamlit app."""
    st.markdown("""
        <style>
        /* Value bet highlighting */
        .positive-edge {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 10px;
            margin: 5px 0;
        }
        
        .negative-edge {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 10px;
            margin: 5px 0;
        }
        
        /* Metric cards enhancement */
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Team colors */
        .team-tor { color: #00205B; font-weight: bold; }
        .team-mtl { color: #AF1E2D; font-weight: bold; }
        .team-bos { color: #FFB81C; font-weight: bold; }
        .team-nyr { color: #0038A8; font-weight: bold; }
        
        /* Table styling */
        .dataframe {
            font-size: 14px;
        }
        
        /* Header styling */
        h1 {
            color: #1e3a8a;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 10px;
        }
        
        h2 {
            color: #1e40af;
            margin-top: 20px;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #3b82f6;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            border: none;
        }
        
        .stButton>button:hover {
            background-color: #2563eb;
        }
        
        /* Info box styling */
        .element-container .stAlert {
            border-radius: 8px;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f1f5f9;
            border-radius: 8px;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)


def format_odds(odds):
    """
    Format American odds for display.
    
    Args:
        odds: Numeric odds value
        
    Returns:
        Formatted string (e.g., "+150", "-110")
    """
    if odds is None:
        return "N/A"
    
    try:
        odds = float(odds)
        if odds > 0:
            return f"+{int(odds)}"
        else:
            return str(int(odds))
    except:
        return "N/A"


def calculate_implied_probability(american_odds):
    """
    Convert American odds to implied probability.
    
    Args:
        american_odds: American odds value (e.g., -110, +150)
        
    Returns:
        Implied probability as decimal (0-1)
    """
    if american_odds is None:
        return None
    
    try:
        odds = float(american_odds)
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    except:
        return None


def kelly_criterion(win_prob, decimal_odds):
    """
    Calculate Kelly Criterion bet sizing.
    
    Args:
        win_prob: Probability of winning (0-1)
        decimal_odds: Decimal odds (e.g., 2.5)
        
    Returns:
        Kelly percentage (0-1)
    """
    if win_prob is None or decimal_odds is None:
        return None
    
    try:
        # Kelly = (bp - q) / b
        # where b = decimal odds - 1, p = win prob, q = 1 - p
        b = decimal_odds - 1
        q = 1 - win_prob
        kelly = (b * win_prob - q) / b
        
        return max(0, kelly)  # Don't bet if negative
    except:
        return None


def american_to_decimal(american_odds):
    """
    Convert American odds to decimal odds.
    
    Args:
        american_odds: American odds value
        
    Returns:
        Decimal odds
    """
    if american_odds is None:
        return None
    
    try:
        odds = float(american_odds)
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1
    except:
        return None
