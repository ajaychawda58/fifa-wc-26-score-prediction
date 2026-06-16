import json
import os
import numpy as np
import polars as pl
from src.data_collector import GROUPS, TEAM_METADATA, ALL_TEAMS
from src.preprocessor import load_data, preprocess_for_model
from src.model import (
    BayesianDixonColesModel,
    BivariatePoissonModel,
    EloModel,
    SoftmaxClassifierModel,
    export_all_models
)

def get_most_likely_score(score_grid):
    """Finds the scoreline with the highest probability from the grid."""
    score_grid = np.array(score_grid)
    flat_idx = np.argmax(score_grid)
    home, away = np.unravel_index(flat_idx, score_grid.shape)
    return int(home), int(away), float(score_grid[home, away])

def ensemble_predictions(dc_pred, bp_pred, elo_pred, cl_pred):
    """Computes the weighted average prediction of the 4 models."""
    w_dc, w_bp, w_elo, w_cl = 0.35, 0.20, 0.30, 0.15
    
    # 1. Expected goals
    home_xG = (w_dc * dc_pred["home_xG"] + 
               w_bp * bp_pred["home_xG"] + 
               w_elo * elo_pred["home_xG"] + 
               w_cl * cl_pred["home_xG"])
               
    away_xG = (w_dc * dc_pred["away_xG"] + 
               w_bp * bp_pred["away_xG"] + 
               w_elo * elo_pred["away_xG"] + 
               w_cl * cl_pred["away_xG"])
               
    # 2. Outcome probabilities
    home_win = (w_dc * dc_pred["home_win"] + 
                w_bp * bp_pred["home_win"] + 
                w_elo * elo_pred["home_win"] + 
                w_cl * cl_pred["home_win"])
                
    away_win = (w_dc * dc_pred["away_win"] + 
                w_bp * bp_pred["away_win"] + 
                w_elo * elo_pred["away_win"] + 
                w_cl * cl_pred["away_win"])
                
    draw = (w_dc * dc_pred["draw"] + 
            w_bp * bp_pred["draw"] + 
            w_elo * elo_pred["draw"] + 
            w_cl * cl_pred["draw"])
            
    # 3. Score probability grid
    grid_dc = np.array(dc_pred["score_probabilities"])
    grid_bp = np.array(bp_pred["score_probabilities"])
    grid_elo = np.array(elo_pred["score_probabilities"])
    grid_cl = np.array(cl_pred["score_probabilities"])
    
    score_probabilities = (w_dc * grid_dc + 
                           w_bp * grid_bp + 
                           w_elo * grid_elo + 
                           w_cl * grid_cl).tolist()
                           
    return {
        "home_xG": home_xG,
        "away_xG": away_xG,
        "home_win": home_win,
        "away_win": away_win,
        "draw": draw,
        "score_probabilities": score_probabilities
    }

def run_prediction_pipeline():
    print("--------------------------------------------------")
    print("Running Multi-Model FIFA WC 2026 Prediction Pipeline")
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
    
    # 2. Extract metadata rankings & formations
    ranks = {team: data["rank"] for team, data in TEAM_METADATA.items()}
    formations = {team: data["formation"] for team, data in TEAM_METADATA.items()}
    
    # 3. Initialize and fit all 4 models
    # A. Elo Model
    elo_model = EloModel(ALL_TEAMS)
    elo_model.fit_elo_history(results_csv)
    elo_model.fit_poisson_regression(df_train)
    
    # B. Dixon-Coles Model
    dc_model = BayesianDixonColesModel(ALL_TEAMS, ranks, formations)
    dc_model.fit(df_train)
    
    # C. Bivariate Poisson Model
    bp_model = BivariatePoissonModel(ALL_TEAMS, ranks)
    bp_model.fit(df_train)
    
    # D. Softmax Classifier Model
    sm_model = SoftmaxClassifierModel(ALL_TEAMS, ranks)
    sm_model.fit(df_train, elo_model.elo_ratings)
    
    # 4. Export all parameters to model_parameters.json
    export_all_models(model_params_json, dc_model, bp_model, elo_model, sm_model)
    
    # 5. Predict all World Cup matches for each model
    with open(wc_matches_json, "r", encoding="utf-8") as f:
        matches = json.load(f)
        
    from src.preprocessor import load_injury_rates
    injury_rates = load_injury_rates("data/player_profiles.md")
    
    print(f"Generating predictions for {len(matches)} World Cup matches across 5 model options...")
    
    # Accuracy counters for statistics logging (using Ensemble model for master stats)
    completed_predictions = 0
    correct_outcomes = 0
    
    for m in matches:
        home = m["home"]
        away = m["away"]
        is_hot = bool(m.get("is_hot", False))
        h_inj = injury_rates.get(home, 0.0)
        a_inj = injury_rates.get(away, 0.0)
        
        # Calculate individual predictions
        dc_p = dc_model.predict_match(home, away, is_hot=is_hot, home_injury_rate=h_inj, away_injury_rate=a_inj)
        bp_p = bp_model.predict_match(home, away, is_hot=is_hot, home_injury_rate=h_inj, away_injury_rate=a_inj)
        elo_p = elo_model.predict_match(home, away, is_hot=is_hot, home_injury_rate=h_inj, away_injury_rate=a_inj)
        cl_p = sm_model.predict_match(home, away, elo_model.elo_ratings, elo_model, is_hot=is_hot, home_injury_rate=h_inj, away_injury_rate=a_inj)
        ens_p = ensemble_predictions(dc_p, bp_p, elo_p, cl_p)
        
        # Helper to structure model outputs
        def format_pred_record(p):
            pred_home, pred_away, pred_prob = get_most_likely_score(p["score_probabilities"])
            return {
                "predicted_home_score": pred_home,
                "predicted_away_score": pred_away,
                "predicted_score_probability": round(pred_prob, 3),
                "home_xG": round(p["home_xG"], 2),
                "away_xG": round(p["away_xG"], 2),
                "home_win_prob": round(p["home_win"], 3),
                "away_win_prob": round(p["away_win"], 3),
                "draw_prob": round(p["draw"], 3)
            }
            
        # Write predictions for all models
        m["predictions"] = {
            "dixon_coles": format_pred_record(dc_p),
            "bivariate": format_pred_record(bp_p),
            "elo": format_pred_record(elo_p),
            "classifier": format_pred_record(cl_p),
            "ensemble": format_pred_record(ens_p)
        }
        
        # Keep legacy columns on the match dict to prevent breaking dashboard backward compatibility
        # We populate these legacy fields with the Ensemble model predictions
        legacy_ref = m["predictions"]["ensemble"]
        m["predicted_home_score"] = legacy_ref["predicted_home_score"]
        m["predicted_away_score"] = legacy_ref["predicted_away_score"]
        m["predicted_score_probability"] = legacy_ref["predicted_score_probability"]
        m["home_xG"] = legacy_ref["home_xG"]
        m["away_xG"] = legacy_ref["away_xG"]
        m["home_win_prob"] = legacy_ref["home_win_prob"]
        m["away_win_prob"] = legacy_ref["away_win_prob"]
        m["draw_prob"] = legacy_ref["draw_prob"]
        
        # Evaluate accuracy of Ensemble model
        if m["home_score"] is not None and m["away_score"] is not None:
            actual_home = int(m["home_score"])
            actual_away = int(m["away_score"])
            completed_predictions += 1
            
            actual_outcome = "H" if actual_home > actual_away else "A" if actual_away > actual_home else "D"
            pred_outcome = "H" if legacy_ref["predicted_home_score"] > legacy_ref["predicted_away_score"] else "A" if legacy_ref["predicted_away_score"] > legacy_ref["predicted_home_score"] else "D"
            
            if actual_outcome == pred_outcome:
                correct_outcomes += 1
                
    # Save matches with predictions back to JSON
    with open(wc_matches_json, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)
        
    print("\n--------------------------------------------------")
    print("Multi-Model Pipeline Completed!")
    print("--------------------------------------------------")
    print(f"Total Matches Predicted: {len(matches)}")
    print(f"Completed Matches Evaluated (Ensemble): {completed_predictions}")
    if completed_predictions > 0:
        print(f"Ensemble Win/Draw/Loss Accuracy: {(correct_outcomes/completed_predictions)*100:.1f}%")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_prediction_pipeline()
