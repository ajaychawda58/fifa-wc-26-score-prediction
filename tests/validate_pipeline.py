import os
import json
import numpy as np
import polars as pl
from src.model import BayesianDixonColesModel
from src.data_collector import ALL_TEAMS, TEAM_METADATA

def test_model_math():
    """Verify that predictions sum to 1.0 and follow proper constraints."""
    print("Testing model mathematical consistency...")
    ranks = {team: data["rank"] for team, data in TEAM_METADATA.items()}
    formations = {team: data["formation"] for team, data in TEAM_METADATA.items()}
    
    model = BayesianDixonColesModel(ALL_TEAMS, ranks, formations)
    
    # Test a match prediction
    pred = model.predict_match("Argentina", "France")
    
    # Expected goals must be positive
    assert pred["home_xG"] > 0, "xG must be positive"
    assert pred["away_xG"] > 0, "xG must be positive"
    
    # Win, loss, draw probabilities must sum to approximately 1.0
    total_prob = pred["home_win"] + pred["away_win"] + pred["draw"]
    assert np.isclose(total_prob, 1.0, atol=1e-4), f"Outcome probabilities must sum to 1.0, got {total_prob}"
    
    # Score grid probabilities must sum to 1.0
    grid_sum = np.sum(pred["score_probabilities"])
    assert np.isclose(grid_sum, 1.0, atol=1e-4), f"Grid probabilities must sum to 1.0, got {grid_sum}"
    
    print("✓ Model mathematical consistency tests passed!")

def test_file_outputs():
    """Verify that output data files exist and have valid JSON structures."""
    print("Testing pipeline file outputs...")
    wc_matches_json = "data/wc_2026_matches.json"
    model_params_json = "data/model_parameters.json"
    
    assert os.path.exists(wc_matches_json), f"{wc_matches_json} does not exist"
    assert os.path.exists(model_params_json), f"{model_params_json} does not exist"
    
    with open(wc_matches_json, "r", encoding="utf-8") as f:
        matches = json.load(f)
    assert len(matches) == 72, f"Expected 72 group stage matches, got {len(matches)}"
    
    # Check that predictions columns were added
    first_match = matches[0]
    expected_keys = [
        "predicted_home_score", "predicted_away_score", 
        "home_win_prob", "away_win_prob", "draw_prob", 
        "home_xG", "away_xG"
    ]
    for key in expected_keys:
        assert key in first_match, f"Expected key {key} in match record"
        
    with open(model_params_json, "r", encoding="utf-8") as f:
        params = json.load(f)
        
    assert "teams" in params, "Model parameters must contain team ratings"
    assert len(params["teams"]) == 48, f"Expected 48 teams in parameters, got {len(params['teams'])}"
    
    # Check Argentina ratings
    arg_ratings = params["teams"]["Argentina"]
    assert "attack" in arg_ratings
    assert "defense" in arg_ratings
    assert "formation" in arg_ratings
    
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
