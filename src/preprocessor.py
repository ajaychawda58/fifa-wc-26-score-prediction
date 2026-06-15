import polars as pl
from datetime import datetime
import json
import os

# Define start date for training data (e.g., last 5 years to keep it relevant to current squads)
TRAINING_START_DATE = "2021-01-01"
CURRENT_DATE_STR = "2026-06-15"
CURRENT_DATE = datetime.strptime(CURRENT_DATE_STR, "%Y-%m-%d")

# Decay factor gamma (half-life of ~3 years: half-life in days = 1095, gamma = ln(2)/1095 ≈ 0.00063)
DECAY_GAMMA = 0.00063

def load_data(results_csv_path, wc_json_path):
    """Loads historical matches from CSV and World Cup matches from JSON, using Polars."""
    
    # 1. Load historical matches using Polars
    # Schema: date, home_team, away_team, home_score, away_score, tournament, city, country, neutral
    print("Loading historical matches with Polars...")
    df_hist = pl.read_csv(
        results_csv_path,
        null_values="NA",
        schema_overrides={
            "home_score": pl.Int64,
            "away_score": pl.Int64
        }
    )
    
    # Filter rows with null scores or invalid dates
    df_hist = df_hist.filter(
        (pl.col("home_score").is_not_null()) &
        (pl.col("away_score").is_not_null()) &
        (pl.col("date") >= TRAINING_START_DATE) &
        (pl.col("date") <= CURRENT_DATE_STR)
    )
    
    # Standardize team names in historical results
    # (Since data collector defined standard names, we map them here)
    # We will rename teams like "United States" to "USA", "Korea Republic" to "South Korea", etc.
    from src.data_collector import NAME_MAP, ALL_TEAMS
    
    def map_team_names_expr(col_name):
        # Build replace expression
        expr = pl.col(col_name)
        for key, val in NAME_MAP.items():
            expr = expr.replace(val, key)
        return expr
        
    df_hist = df_hist.with_columns([
        map_team_names_expr("home_team").alias("home_team"),
        map_team_names_expr("away_team").alias("away_team")
    ])
    
    # 2. Load World Cup 2026 matches played so far
    print("Loading World Cup matches...")
    with open(wc_json_path, "r", encoding="utf-8") as f:
        wc_matches = json.load(f)
        
    # Filter to matches that have scores (actually played)
    wc_played = [m for m in wc_matches if m["home_score"] is not_null_score(m)]
    
    if wc_played:
        # Create a Polars DataFrame for played WC matches
        wc_records = []
        for m in wc_played:
            wc_records.append({
                "date": m["date"],
                "home_team": m["home"],
                "away_team": m["away"],
                "home_score": int(m["home_score"]),
                "away_score": int(m["away_score"]),
                "tournament": "FIFA World Cup",
                "city": "Unknown",
                "country": "Co-hosts",
                "neutral": True
            })
        df_wc = pl.DataFrame(wc_records)
        # Combine historical results and World Cup played matches
        df_all = pl.concat([df_hist, df_wc])
    else:
        df_all = df_hist
        
    return df_all

def not_null_score(match):
    return match.get("home_score") is not None and match.get("away_score") is not None

def preprocess_for_model(df):
    """Adds weights based on time decay and structures data for training."""
    
    # Parse date column to Datetime and compute age in days
    df = df.with_columns(
        pl.col("date").str.to_date("%Y-%m-%d")
    ).with_columns(
        ((pl.lit(CURRENT_DATE.date()) - pl.col("date")).dt.total_days()).alias("days_ago")
    )
    
    # Calculate exponential time decay weight
    # w = exp(-gamma * days_ago)
    # Give World Cup matches a higher weight multiplier (e.g., 5.0) to emphasize current tournament form
    df = df.with_columns(
        (pl.col("days_ago") * -DECAY_GAMMA).exp().alias("weight")
    ).with_columns(
        pl.when(pl.col("tournament") == "FIFA World Cup")
        .then(pl.col("weight") * 5.0)
        .otherwise(pl.col("weight"))
        .alias("weight")
    )
    
    # Select final columns needed for modeling
    df_model = df.select([
        "date", "home_team", "away_team", "home_score", "away_score", "weight", "neutral"
    ])
    
    print(f"Preprocessed {df_model.height} total matches for model training.")
    return df_model

if __name__ == "__main__":
    # Test script
    results_path = "data/results_cache.csv"
    wc_path = "data/wc_2026_matches.json"
    if os.path.exists(results_path) and os.path.exists(wc_path):
        df = load_data(results_path, wc_path)
        df_model = preprocess_for_model(df)
        print(df_model.head())
