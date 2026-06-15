import json
import os
import numpy as np
import polars as pl
from src.data_collector import GROUPS, TEAM_METADATA, ALL_TEAMS
from src.preprocessor import load_data, preprocess_for_model
from src.model import BayesianDixonColesModel

def get_most_likely_score(score_grid):
    """Finds the scoreline with the highest probability from the grid."""
    score_grid = np.array(score_grid)
    flat_idx = np.argmax(score_grid)
    home, away = np.unravel_index(flat_idx, score_grid.shape)
    return int(home), int(away), float(score_grid[home, away])

def run_prediction_pipeline():
    print("--------------------------------------------------")
    print("Running FIFA WC 2026 Prediction Pipeline")
    print("--------------------------------------------------")
    
    results_csv = "data/results_cache.csv"
    wc_matches_json = "data/wc_2026_matches.json"
    model_params_json = "data/model_parameters.json"
    
    if not os.path.exists(results_csv) or not os.path.exists(wc_matches_json):
        print("Data files not found. Please run src/data_collector.py first.")
        return
        
    # 1. Preprocess data using Polars
    df_raw = load_data(results_csv, wc_matches_json)
    df_train = preprocess_for_model(df_raw)
    
    # 2. Extract mappings for initialization
    ranks = {team: data["rank"] for team, data in TEAM_METADATA.items()}
    formations = {team: data["formation"] for team, data in TEAM_METADATA.items()}
    
    # 3. Initialize and fit Bayesian Dixon-Coles model
    model = BayesianDixonColesModel(ALL_TEAMS, ranks, formations)
    model.fit(df_train)
    
    # 4. Export model parameters to model_parameters.json
    model.export_parameters(model_params_json)
    
    # 5. Predict all World Cup matches
    with open(wc_matches_json, "r", encoding="utf-8") as f:
        matches = json.load(f)
        
    print(f"Generating predictions for {len(matches)} World Cup matches...")
    
    completed_predictions = 0
    correct_outcomes = 0
    correct_scores = 0
    
    # Track metrics
    for m in matches:
        home = m["home"]
        away = m["away"]
        
        # Run prediction
        pred = model.predict_match(home, away)
        pred_home, pred_away, pred_prob = get_most_likely_score(pred["score_probabilities"])
        
        # Attach prediction details to match record
        m["predicted_home_score"] = pred_home
        m["predicted_away_score"] = pred_away
        m["predicted_score_probability"] = pred_prob
        m["home_xG"] = round(pred["home_xG"], 2)
        m["away_xG"] = round(pred["away_xG"], 2)
        m["home_win_prob"] = round(pred["home_win"], 3)
        m["away_win_prob"] = round(pred["away_win"], 3)
        m["draw_prob"] = round(pred["draw"], 3)
        
        # Evaluate accuracy if match is already played
        if m["home_score"] is not None and m["away_score"] is not None:
            actual_home = int(m["home_score"])
            actual_away = int(m["away_score"])
            completed_predictions += 1
            
            # Outcome check
            actual_outcome = "H" if actual_home > actual_away else "A" if actual_away > actual_home else "D"
            pred_outcome = "H" if pred_home > pred_away else "A" if pred_away > pred_home else "D"
            
            if actual_outcome == pred_outcome:
                correct_outcomes += 1
            if actual_home == pred_home and actual_away == pred_away:
                correct_scores += 1
                
    # Save matches with prediction records
    with open(wc_matches_json, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)
        
    print("\n--------------------------------------------------")
    print("Pipeline Execution Summary")
    print("--------------------------------------------------")
    print(f"Total Matches Predicted: {len(matches)}")
    print(f"Completed Matches Evaluated: {completed_predictions}")
    
    if completed_predictions > 0:
        outcome_acc = (correct_outcomes / completed_predictions) * 100
        score_acc = (correct_scores / completed_predictions) * 100
        print(f"Outcome Prediction Accuracy (Win/Draw/Loss): {outcome_acc:.1f}% ({correct_outcomes}/{completed_predictions})")
        print(f"Exact Score Prediction Accuracy: {score_acc:.1f}% ({correct_scores}/{completed_predictions})")
    else:
        print("No completed matches to evaluate yet.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_prediction_pipeline()
