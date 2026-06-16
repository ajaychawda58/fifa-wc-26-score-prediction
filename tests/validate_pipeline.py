import os
import json
import numpy as np
import polars as pl
from src.model import (
    BayesianDixonColesModel,
    BivariatePoissonModel,
    EloModel,
    SoftmaxClassifierModel
)
from src.run_pipeline import ensemble_predictions
from src.data_collector import ALL_TEAMS, TEAM_METADATA

def test_model_math():
    """Verify that all 4 models and their ensemble sum to 1.0 and follow proper constraints."""
    print("Testing mathematical consistency across all models...")
    ranks = {team: data["rank"] for team, data in TEAM_METADATA.items()}
    formations = {team: data["formation"] for team, data in TEAM_METADATA.items()}
    
    # 1. Dixon-Coles
    dc_model = BayesianDixonColesModel(ALL_TEAMS, ranks, formations)
    pred_dc = dc_model.predict_match("Argentina", "France")
    assert pred_dc["home_xG"] > 0, "Dixon-Coles home_xG must be positive"
    assert pred_dc["away_xG"] > 0, "Dixon-Coles away_xG must be positive"
    prob_dc = pred_dc["home_win"] + pred_dc["away_win"] + pred_dc["draw"]
    assert np.isclose(prob_dc, 1.0, atol=1e-4), f"DC outcome probabilities must sum to 1.0, got {prob_dc}"
    grid_dc = np.sum(pred_dc["score_probabilities"])
    assert np.isclose(grid_dc, 1.0, atol=1e-4), f"DC grid probabilities must sum to 1.0, got {grid_dc}"

    # 2. Bivariate Poisson
    bp_model = BivariatePoissonModel(ALL_TEAMS, ranks)
    pred_bp = bp_model.predict_match("Argentina", "France")
    assert pred_bp["home_xG"] > 0, "Bivariate Poisson home_xG must be positive"
    assert pred_bp["away_xG"] > 0, "Bivariate Poisson away_xG must be positive"
    prob_bp = pred_bp["home_win"] + pred_bp["away_win"] + pred_bp["draw"]
    assert np.isclose(prob_bp, 1.0, atol=1e-4), f"BP outcome probabilities must sum to 1.0, got {prob_bp}"
    grid_bp = np.sum(pred_bp["score_probabilities"])
    assert np.isclose(grid_bp, 1.0, atol=1e-4), f"BP grid probabilities must sum to 1.0, got {grid_bp}"

    # 3. Elo-Poisson
    elo_model = EloModel(ALL_TEAMS)
    # Give them dummy ratings to test
    elo_model.elo_ratings["Argentina"] = 1850.0
    elo_model.elo_ratings["France"] = 1820.0
    pred_elo = elo_model.predict_match("Argentina", "France")
    assert pred_elo["home_xG"] > 0, "Elo-Poisson home_xG must be positive"
    assert pred_elo["away_xG"] > 0, "Elo-Poisson away_xG must be positive"
    prob_elo = pred_elo["home_win"] + pred_elo["away_win"] + pred_elo["draw"]
    assert np.isclose(prob_elo, 1.0, atol=1e-4), f"Elo outcome probabilities must sum to 1.0, got {prob_elo}"
    grid_elo = np.sum(pred_elo["score_probabilities"])
    assert np.isclose(grid_elo, 1.0, atol=1e-4), f"Elo grid probabilities must sum to 1.0, got {grid_elo}"

    # 4. Softmax Classifier
    sm_model = SoftmaxClassifierModel(ALL_TEAMS, ranks)
    pred_cl = sm_model.predict_match("Argentina", "France", elo_model.elo_ratings, elo_model)
    assert pred_cl["home_xG"] > 0, "Classifier home_xG must be positive"
    assert pred_cl["away_xG"] > 0, "Classifier away_xG must be positive"
    prob_cl = pred_cl["home_win"] + pred_cl["away_win"] + pred_cl["draw"]
    assert np.isclose(prob_cl, 1.0, atol=1e-4), f"Classifier outcome probabilities must sum to 1.0, got {prob_cl}"
    grid_cl = np.sum(pred_cl["score_probabilities"])
    assert np.isclose(grid_cl, 1.0, atol=1e-4), f"Classifier grid probabilities must sum to 1.0, got {grid_cl}"

    # 5. Ensemble
    pred_ens = ensemble_predictions(pred_dc, pred_bp, pred_elo, pred_cl)
    assert pred_ens["home_xG"] > 0, "Ensemble home_xG must be positive"
    assert pred_ens["away_xG"] > 0, "Ensemble away_xG must be positive"
    prob_ens = pred_ens["home_win"] + pred_ens["away_win"] + pred_ens["draw"]
    assert np.isclose(prob_ens, 1.0, atol=1e-4), f"Ensemble outcome probabilities must sum to 1.0, got {prob_ens}"
    grid_ens = np.sum(pred_ens["score_probabilities"])
    assert np.isclose(grid_ens, 1.0, atol=1e-4), f"Ensemble grid probabilities must sum to 1.0, got {grid_ens}"

    print("✓ Model mathematical consistency tests passed!")

def test_file_outputs():
    """Verify that output data files exist and have valid JSON structures matching the multi-model schema."""
    print("Testing pipeline file outputs...")
    wc_matches_json = "data/wc_2026_matches.json"
    model_params_json = "data/model_parameters.json"
    
    assert os.path.exists(wc_matches_json), f"{wc_matches_json} does not exist"
    assert os.path.exists(model_params_json), f"{model_params_json} does not exist"
    
    with open(wc_matches_json, "r", encoding="utf-8") as f:
        matches = json.load(f)
    assert len(matches) == 72, f"Expected 72 group stage matches, got {len(matches)}"
    
    # Check that predictions columns and sub-model records were added
    first_match = matches[0]
    expected_keys = [
        "predicted_home_score", "predicted_away_score", 
        "home_win_prob", "away_win_prob", "draw_prob", 
        "home_xG", "away_xG", "predictions",
        "temperature_c", "is_hot"
    ]
    for key in expected_keys:
        assert key in first_match, f"Expected key {key} in match record"
        
    # Check predictions contains all 5 model choices
    sub_preds = first_match["predictions"]
    expected_models = ["dixon_coles", "bivariate", "elo", "classifier", "ensemble"]
    for model_key in expected_models:
        assert model_key in sub_preds, f"Expected sub-model prediction for '{model_key}'"
        assert "predicted_home_score" in sub_preds[model_key]
        assert "predicted_away_score" in sub_preds[model_key]
        assert "home_win_prob" in sub_preds[model_key]
        assert "away_win_prob" in sub_preds[model_key]
        assert "draw_prob" in sub_preds[model_key]
        assert "home_xG" in sub_preds[model_key]
        assert "away_xG" in sub_preds[model_key]
        
    with open(model_params_json, "r", encoding="utf-8") as f:
        params = json.load(f)
        
    # Check new multi-model parameter structure
    for model_key in ["dixon_coles", "bivariate", "elo", "classifier"]:
        assert model_key in params, f"Model parameters must contain ratings/weights for model '{model_key}'"
        
    assert "beta_hot" in params["dixon_coles"], "Expected beta_hot in Dixon-Coles params"
    assert "beta_hot" in params["bivariate"], "Expected beta_hot in Bivariate params"
    assert "beta_hot" in params["elo"], "Expected beta_hot in Elo params"
    assert "beta_injury" in params["dixon_coles"], "Expected beta_injury in Dixon-Coles params"
    assert "beta_injury" in params["bivariate"], "Expected beta_injury in Bivariate params"
    assert "beta_injury" in params["elo"], "Expected beta_injury in Elo params"
        
    assert len(params["dixon_coles"]["teams"]) == 48, "Expected 48 teams in Dixon-Coles parameters"
    assert len(params["bivariate"]["teams"]) == 48, "Expected 48 teams in Bivariate parameters"
    assert len(params["elo"]["teams"]) == 48, "Expected 48 teams in Elo parameters"
    assert "w_home" in params["classifier"], "Expected w_home weights in Softmax Classifier"
    assert "w_draw" in params["classifier"], "Expected w_draw weights in Softmax Classifier"
    assert len(params["classifier"]["w_home"]) == 6, "Expected w_home to have length 6"
    assert len(params["classifier"]["w_draw"]) == 6, "Expected w_draw to have length 6"
    
    # Check Argentina ratings in Dixon-Coles
    arg_ratings = params["dixon_coles"]["teams"]["Argentina"]
    assert "attack" in arg_ratings
    assert "defense" in arg_ratings
    assert "formation" in arg_ratings
    assert "rank" in arg_ratings
    assert "injury_rate" in arg_ratings, "Expected injury_rate in team ratings"
    
    print("✓ Pipeline file outputs validation passed!")

def run_all_tests():
    test_model_math()
    try:
        test_file_outputs()
    except AssertionError as e:
        print(f"✗ File outputs validation failed: {e}")
        print("Note: Run the pipeline first to generate outputs before validating files.")
        return False
    print("--------------------------------------------------")
    print("All automated verification tests passed!")
    print("--------------------------------------------------")
    return True

if __name__ == "__main__":
    run_all_tests()
