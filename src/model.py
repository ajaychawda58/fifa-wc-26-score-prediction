import numpy as np
from scipy.optimize import minimize
import polars as pl
import json
import os
import math

class BayesianDixonColesModel:
    def __init__(self, team_list, team_ranks, team_formations, prior_sigma=0.3):
        """
        Initialize the model.
        - team_list: List of all 48 team names.
        - team_ranks: Dict mapping team name -> FIFA rank (1 to 50+).
        - team_formations: Dict mapping team name -> preferred tactical formation.
        - prior_sigma: Standard deviation of the log-normal priors for team strengths.
        """
        self.teams = sorted(team_list)
        self.team_to_idx = {team: idx for idx, team in enumerate(self.teams)}
        self.num_teams = len(self.teams)
        
        self.ranks = team_ranks
        self.formations = team_formations
        self.prior_sigma = prior_sigma
        
        # Calculate prior means in log-space
        # A higher rank number (worse team) means lower attack strength and higher defense vulnerability
        self.prior_a = np.zeros(self.num_teams) # log attack strength prior mean
        self.prior_d = np.zeros(self.num_teams) # log defense vulnerability prior mean
        
        for team in self.teams:
            idx = self.team_to_idx[team]
            rank = self.ranks.get(team, 30)
            
            # Simple prior mapping: rank 1 has mean attack = 1.6, rank 50 has mean attack = 0.6
            mean_att = 1.7 * math.exp(-0.018 * rank)
            # Rank 1 has mean def = 0.5, rank 50 has mean def = 1.3
            mean_def = 0.55 * math.exp(0.018 * rank)
            
            self.prior_a[idx] = math.log(mean_att)
            self.prior_d[idx] = math.log(mean_def)
            
        # Fitted parameters (will be filled during fit)
        self.log_attack = np.copy(self.prior_a)
        self.log_defense = np.copy(self.prior_d)
        self.log_home_adv = 0.15 # log home advantage default (HA = ~1.16)
        self.rho = -0.05         # Dixon-Coles adjustment parameter
        
    def _dixon_coles_tau(self, x, y, lmbda, mu, rho):
        """Computes the Dixon-Coles tau adjustment factor for low-scoring matches."""
        if x == 0 and y == 0:
            return 1.0 - rho * lmbda * mu
        elif x == 1 and y == 0:
            return 1.0 + rho * mu
        elif x == 0 and y == 1:
            return 1.0 + rho * lmbda
        elif x == 1 and y == 1:
            return 1.0 - rho
        else:
            return 1.0
            
    def _loss_function(self, params, home_idxs, away_idxs, home_goals, away_goals, weights, is_home_adv):
        """Negative log-posterior function to minimize."""
        # Unpack parameters
        # params: [log_attack (num_teams), log_defense (num_teams), log_home_adv, rho]
        log_att = params[:self.num_teams]
        log_def = params[self.num_teams:2*self.num_teams]
        log_ha = params[2*self.num_teams]
        rho = params[2*self.num_teams + 1]
        
        # 1. Likelihood loss
        # Expected goals lambda and mu
        # lambda = exp(att_home + def_away + ha * is_home_adv)
        # mu = exp(att_away + def_home)
        att_h = log_att[home_idxs]
        def_a = log_def[away_idxs]
        att_a = log_att[away_idxs]
        def_h = log_def[home_idxs]
        
        # Calculate expected goals
        lmbda = np.exp(att_h + def_a + log_ha * is_home_adv)
        mu = np.exp(att_a + def_h)
        
        # Dixon-Coles adjustment tau
        tau = np.ones_like(lmbda)
        # Apply adjustment where home_goals and away_goals are <= 1
        cond_00 = (home_goals == 0) & (away_goals == 0)
        cond_10 = (home_goals == 1) & (away_goals == 0)
        cond_01 = (home_goals == 0) & (away_goals == 1)
        cond_11 = (home_goals == 1) & (away_goals == 1)
        
        tau[cond_00] = 1.0 - rho * lmbda[cond_00] * mu[cond_00]
        tau[cond_10] = 1.0 + rho * mu[cond_10]
        tau[cond_01] = 1.0 + rho * lmbda[cond_01]
        tau[cond_11] = 1.0 - rho
        
        # Clip tau to avoid negative/zero values
        tau = np.clip(tau, 1e-10, None)
        
        # Weighted Negative Log-Likelihood
        # nll = -w * [log(tau) + x*log(lambda) - lambda + y*log(mu) - mu]
        nll = -weights * (np.log(tau) + home_goals * np.log(lmbda) - lmbda + away_goals * np.log(mu) - mu)
        likelihood_loss = np.sum(nll)
        
        # 2. Prior loss (regularization)
        # a_i ~ N(prior_a_i, sigma^2)
        # d_i ~ N(prior_d_i, sigma^2)
        prior_loss_att = np.sum(((log_att - self.prior_a) ** 2) / (2 * self.prior_sigma ** 2))
        prior_loss_def = np.sum(((log_def - self.prior_d) ** 2) / (2 * self.prior_sigma ** 2))
        
        # Prior loss on home advantage: centered around 0.18 (about 20% boost)
        prior_loss_ha = ((log_ha - 0.18) ** 2) / (2 * 0.1 ** 2)
        
        # Prior loss on rho: centered around -0.05
        prior_loss_rho = ((rho - (-0.05)) ** 2) / (2 * 0.05 ** 2)
        
        total_loss = likelihood_loss + prior_loss_att + prior_loss_def + prior_loss_ha + prior_loss_rho
        return total_loss
        
    def fit(self, df_matches):
        """Fits the model parameters to the matches DataFrame using Polars."""
        print("Fitting Bayesian Dixon-Coles model...")
        
        # Convert team names to indexes, skipping matches with teams not in tournament if any
        # But we filter df_matches to only teams that are in our team list
        df_filtered = df_matches.filter(
            (pl.col("home_team").is_in(self.teams)) & 
            (pl.col("away_team").is_in(self.teams))
        )
        
        home_idxs = np.array([self.team_to_idx[name] for name in df_filtered["home_team"]])
        away_idxs = np.array([self.team_to_idx[name] for name in df_filtered["away_team"]])
        home_goals = df_filtered["home_score"].to_numpy().astype(int)
        away_goals = df_filtered["away_score"].to_numpy().astype(int)
        weights = df_filtered["weight"].to_numpy().astype(float)
        
        # Home advantage logic: if not neutral, OR if home team is USA/Canada/Mexico (host team playing at WC)
        neutral_val = df_filtered["neutral"].to_numpy().astype(bool)
        home_names = df_filtered["home_team"].to_numpy()
        is_host = np.array([name in ["USA", "Canada", "Mexico"] for name in home_names])
        is_home_adv = (~neutral_val) | is_host
        is_home_adv = is_home_adv.astype(float)
        
        # Initial parameters: log_attack, log_defense, log_home_adv, rho
        initial_params = np.concatenate([
            self.log_attack,
            self.log_defense,
            [self.log_home_adv],
            [self.rho]
        ])
        
        # Bounds to keep parameters stable:
        # log_attack: no bounds (log space)
        # log_defense: no bounds
        # log_home_adv: -1.0 to 1.0
        # rho: -0.3 to 0.3 (to keep Dixon-Coles adjustment valid)
        bounds = [(None, None)] * (2 * self.num_teams) + [(-1.0, 1.0), (-0.3, 0.3)]
        
        # Run optimization
        res = minimize(
            self._loss_function,
            initial_params,
            args=(home_idxs, away_idxs, home_goals, away_goals, weights, is_home_adv),
            method='L-BFGS-B',
            bounds=bounds
        )
        
        if not res.success:
            print(f"Warning: Optimization did not converge: {res.message}")
        else:
            print("Model optimization successfully converged.")
            
        # Extract fitted parameters
        self.log_attack = res.x[:self.num_teams]
        self.log_defense = res.x[self.num_teams:2*self.num_teams]
        self.log_home_adv = float(res.x[2*self.num_teams])
        self.rho = float(res.x[2*self.num_teams + 1])
        
        # Log summary of fitted model
        print(f"Fitted Home Advantage Multiplier: {math.exp(self.log_home_adv):.3f}")
        print(f"Fitted Dixon-Coles Rho: {self.rho:.4f}")
        
    def predict_match(self, home_team, away_team, max_goals=10):
        """
        Predicts goals probability distribution and win probabilities for a match.
        Returns:
        - expected_goals_home: float
        - expected_goals_away: float
        - win_prob_home: float
        - win_prob_away: float
        - draw_prob: float
        - score_grid: 2D numpy array of probabilities
        """
        home_idx = self.team_to_idx[home_team]
        away_idx = self.team_to_idx[away_team]
        
        # Home advantage multiplier applies if home_team is a co-host (USA, Canada, Mexico)
        is_home_adv = home_team in ["USA", "Canada", "Mexico"]
        ha_mult = math.exp(self.log_home_adv) if is_home_adv else 1.0
        
        lmbda = math.exp(self.log_attack[home_idx] + self.log_defense[away_idx]) * ha_mult
        mu = math.exp(self.log_attack[away_idx] + self.log_defense[home_idx])
        
        # Calculate goal probability distributions
        p_home = np.array([self._poisson_pmf(g, lmbda) for g in range(max_goals + 1)])
        p_away = np.array([self._poisson_pmf(g, mu) for g in range(max_goals + 1)])
        
        # Outer product to get match grid
        score_grid = np.outer(p_home, p_away)
        
        # Apply Dixon-Coles adjustment to the grid
        for x in [0, 1]:
            for y in [0, 1]:
                tau = self._dixon_coles_tau(x, y, lmbda, mu, self.rho)
                score_grid[x, y] *= tau
                
        # Normalize grid to make sure probabilities sum to 1.0
        grid_sum = np.sum(score_grid)
        if grid_sum > 0:
            score_grid /= grid_sum
            
        # Calculate outcome probabilities
        win_home = np.sum(np.tril(score_grid, -1)) # home goals > away goals
        draw = np.sum(np.diag(score_grid))         # home goals == away goals
        win_away = np.sum(np.triu(score_grid, 1))  # away goals > home goals
        
        return {
            "home_xG": lmbda,
            "away_xG": mu,
            "home_win": float(win_home),
            "away_win": float(win_away),
            "draw": float(draw),
            "score_probabilities": score_grid.tolist()
        }
        
    def _poisson_pmf(self, k, lmbda):
        """Poisson PMF."""
        return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)
        
    def export_parameters(self, file_path):
        """Exports team ratings and model parameters to a JSON file."""
        parameters = {
            "rho": self.rho,
            "home_advantage_multiplier": math.exp(self.log_home_adv),
            "teams": {}
        }
        
        for team in self.teams:
            idx = self.team_to_idx[team]
            att = math.exp(self.log_attack[idx])
            dfn = math.exp(self.log_defense[idx])
            parameters["teams"][team] = {
                "attack": att,
                "defense": dfn,
                "formation": self.formations.get(team, "4-3-3"),
                "rank": self.ranks.get(team, 30)
            }
            
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(parameters, f, indent=2)
        print(f"Exported model parameters to {file_path}")
