import numpy as np
from scipy.optimize import minimize
import polars as pl
import json
import os
import math

# --- 1. Bayesian Dixon-Coles Model ---
class BayesianDixonColesModel:
    def __init__(self, team_list, team_ranks, team_formations, prior_sigma=0.3):
        self.teams = sorted(team_list)
        self.team_to_idx = {team: idx for idx, team in enumerate(self.teams)}
        self.num_teams = len(self.teams)
        self.ranks = team_ranks
        self.formations = team_formations
        self.prior_sigma = prior_sigma
        
        self.prior_a = np.zeros(self.num_teams)
        self.prior_d = np.zeros(self.num_teams)
        
        for team in self.teams:
            idx = self.team_to_idx[team]
            rank = self.ranks.get(team, 30)
            mean_att = 1.7 * math.exp(-0.018 * rank)
            mean_def = 0.55 * math.exp(0.018 * rank)
            self.prior_a[idx] = math.log(mean_att)
            self.prior_d[idx] = math.log(mean_def)
            
        self.log_attack = np.copy(self.prior_a)
        self.log_defense = np.copy(self.prior_d)
        self.log_home_adv = 0.15
        self.rho = -0.05
        self.beta_hot = 0.0
        self.beta_injury = 0.0
        
    def _dixon_coles_tau(self, x, y, lmbda, mu, rho):
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
            
    def _loss_function(self, params, home_idxs, away_idxs, home_goals, away_goals, weights, is_home_adv, is_hot, home_injury, away_injury):
        log_att = params[:self.num_teams]
        log_def = params[self.num_teams:2*self.num_teams]
        log_ha = params[2*self.num_teams]
        rho = params[2*self.num_teams + 1]
        beta_hot = params[2*self.num_teams + 2]
        beta_injury = params[2*self.num_teams + 3]
        
        att_h = log_att[home_idxs]
        def_a = log_def[away_idxs]
        att_a = log_att[away_idxs]
        def_h = log_def[home_idxs]
        
        lmbda = np.exp(att_h + def_a + log_ha * is_home_adv + beta_hot * is_hot + beta_injury * home_injury)
        mu = np.exp(att_a + def_h + beta_hot * is_hot + beta_injury * away_injury)
        
        tau = np.ones_like(lmbda)
        cond_00 = (home_goals == 0) & (away_goals == 0)
        cond_10 = (home_goals == 1) & (away_goals == 0)
        cond_01 = (home_goals == 0) & (away_goals == 1)
        cond_11 = (home_goals == 1) & (away_goals == 1)
        
        tau[cond_00] = 1.0 - rho * lmbda[cond_00] * mu[cond_00]
        tau[cond_10] = 1.0 + rho * mu[cond_10]
        tau[cond_01] = 1.0 + rho * lmbda[cond_01]
        tau[cond_11] = 1.0 - rho
        
        tau = np.clip(tau, 1e-10, None)
        nll = -weights * (np.log(tau) + home_goals * np.log(lmbda) - lmbda + away_goals * np.log(mu) - mu)
        likelihood_loss = np.sum(nll)
        
        prior_loss_att = np.sum(((log_att - self.prior_a) ** 2) / (2 * self.prior_sigma ** 2))
        prior_loss_def = np.sum(((log_def - self.prior_d) ** 2) / (2 * self.prior_sigma ** 2))
        prior_loss_ha = ((log_ha - 0.18) ** 2) / (2 * 0.1 ** 2)
        prior_loss_rho = ((rho - (-0.05)) ** 2) / (2 * 0.05 ** 2)
        prior_loss_hot = (beta_hot ** 2) / (2 * 0.2 ** 2)
        prior_loss_injury = (beta_injury ** 2) / (2 * 0.2 ** 2)
        
        return likelihood_loss + prior_loss_att + prior_loss_def + prior_loss_ha + prior_loss_rho + prior_loss_hot + prior_loss_injury
        
    def fit(self, df_matches):
        df_filtered = df_matches.filter(
            (pl.col("home_team").is_in(self.teams)) & 
            (pl.col("away_team").is_in(self.teams))
        )
        home_idxs = np.array([self.team_to_idx[name] for name in df_filtered["home_team"]])
        away_idxs = np.array([self.team_to_idx[name] for name in df_filtered["away_team"]])
        home_goals = df_filtered["home_score"].to_numpy().astype(int)
        away_goals = df_filtered["away_score"].to_numpy().astype(int)
        weights = df_filtered["weight"].to_numpy().astype(float)
        is_hot = df_filtered["is_hot"].to_numpy().astype(float)
        
        neutral_val = df_filtered["neutral"].to_numpy().astype(bool)
        home_names = df_filtered["home_team"].to_numpy()
        is_host = np.array([name in ["USA", "Canada", "Mexico"] for name in home_names])
        is_home_adv = (~neutral_val) | is_host
        is_home_adv = is_home_adv.astype(float)
        
        initial_params = np.concatenate([self.log_attack, self.log_defense, [self.log_home_adv], [self.rho], [self.beta_hot], [self.beta_injury]])
        bounds = [(None, None)] * (2 * self.num_teams) + [(-1.0, 1.0), (-0.3, 0.3), (-1.0, 1.0), (-1.0, 1.0)]
        
        home_injury = df_filtered["home_injury_rate"].to_numpy().astype(float)
        away_injury = df_filtered["away_injury_rate"].to_numpy().astype(float)
        
        res = minimize(self._loss_function, initial_params, args=(home_idxs, away_idxs, home_goals, away_goals, weights, is_home_adv, is_hot, home_injury, away_injury), method='L-BFGS-B', bounds=bounds)
        if res.success:
            self.log_attack = res.x[:self.num_teams]
            self.log_defense = res.x[self.num_teams:2*self.num_teams]
            self.log_home_adv = float(res.x[2*self.num_teams])
            self.rho = float(res.x[2*self.num_teams + 1])
            self.beta_hot = float(res.x[2*self.num_teams + 2])
            self.beta_injury = float(res.x[2*self.num_teams + 3])
            
    def predict_match(self, home_team, away_team, is_hot=False, home_injury_rate=0.0, away_injury_rate=0.0, max_goals=5):
        home_idx = self.team_to_idx[home_team]
        away_idx = self.team_to_idx[away_team]
        is_home_adv = home_team in ["USA", "Canada", "Mexico"]
        ha_mult = math.exp(self.log_home_adv) if is_home_adv else 1.0
        hot_mult = math.exp(self.beta_hot) if is_hot else 1.0
        injury_mult_h = math.exp(self.beta_injury * home_injury_rate)
        injury_mult_a = math.exp(self.beta_injury * away_injury_rate)
        
        lmbda = math.exp(self.log_attack[home_idx] + self.log_defense[away_idx]) * ha_mult * hot_mult * injury_mult_h
        mu = math.exp(self.log_attack[away_idx] + self.log_defense[home_idx]) * hot_mult * injury_mult_a
        
        p_home = np.array([self._poisson_pmf(g, lmbda) for g in range(max_goals + 1)])
        p_away = np.array([self._poisson_pmf(g, mu) for g in range(max_goals + 1)])
        score_grid = np.outer(p_home, p_away)
        
        for x in [0, 1]:
            for y in [0, 1]:
                score_grid[x, y] *= self._dixon_coles_tau(x, y, lmbda, mu, self.rho)
                
        grid_sum = np.sum(score_grid)
        if grid_sum > 0:
            score_grid /= grid_sum
            
        win_home = np.sum(np.tril(score_grid, -1))
        draw = np.sum(np.diag(score_grid))
        win_away = np.sum(np.triu(score_grid, 1))
        
        return {
            "home_xG": lmbda,
            "away_xG": mu,
            "home_win": float(win_home),
            "away_win": float(win_away),
            "draw": float(draw),
            "score_probabilities": score_grid.tolist()
        }
        
    def _poisson_pmf(self, k, lmbda):
        return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


# --- 2. Bivariate Poisson Model ---
class BivariatePoissonModel:
    def __init__(self, team_list, team_ranks, prior_sigma=0.3):
        self.teams = sorted(team_list)
        self.team_to_idx = {team: idx for idx, team in enumerate(self.teams)}
        self.num_teams = len(self.teams)
        self.ranks = team_ranks
        self.prior_sigma = prior_sigma
        
        self.prior_a = np.zeros(self.num_teams)
        self.prior_d = np.zeros(self.num_teams)
        for team in self.teams:
            idx = self.team_to_idx[team]
            rank = self.ranks.get(team, 30)
            self.prior_a[idx] = math.log(1.7 * math.exp(-0.018 * rank))
            self.prior_d[idx] = math.log(0.55 * math.exp(0.018 * rank))
            
        self.log_attack = np.copy(self.prior_a)
        self.log_defense = np.copy(self.prior_d)
        self.log_home_adv = 0.15
        self.log_covariance = math.log(0.05) # Shared covariance parameter lambda_3
        self.beta_hot = 0.0
        self.beta_injury = 0.0
        
    def _bivariate_poisson_pmf(self, x, y, l1, l2, l3):
        ans = 0.0
        for k in range(min(x, y) + 1):
            term = (l1 ** (x - k)) * (l2 ** (y - k)) * (l3 ** k) / (math.factorial(x - k) * math.factorial(y - k) * math.factorial(k))
            ans += term
        return ans * math.exp(-(l1 + l2 + l3))
        
    def _loss_function(self, params, home_idxs, away_idxs, home_goals, away_goals, weights, is_home_adv, is_hot, home_injury, away_injury):
        log_att = params[:self.num_teams]
        log_def = params[self.num_teams:2*self.num_teams]
        log_ha = params[2*self.num_teams]
        log_l3 = params[2*self.num_teams + 1]
        beta_hot = params[2*self.num_teams + 2]
        beta_injury = params[2*self.num_teams + 3]
        
        l1 = np.exp(log_att[home_idxs] + log_def[away_idxs] + log_ha * is_home_adv + beta_hot * is_hot + beta_injury * home_injury)
        l2 = np.exp(log_att[away_idxs] + log_def[home_idxs] + beta_hot * is_hot + beta_injury * away_injury)
        l3 = np.exp(log_l3)
        
        # Calculate pmf for each match
        pmfs = []
        for i in range(len(home_goals)):
            pmf = self._bivariate_poisson_pmf(home_goals[i], away_goals[i], l1[i], l2[i], l3)
            pmfs.append(max(1e-10, pmf))
            
        likelihood_loss = -np.sum(weights * np.log(pmfs))
        prior_loss_att = np.sum(((log_att - self.prior_a) ** 2) / (2 * self.prior_sigma ** 2))
        prior_loss_def = np.sum(((log_def - self.prior_d) ** 2) / (2 * self.prior_sigma ** 2))
        prior_loss_ha = ((log_ha - 0.18) ** 2) / (2 * 0.1 ** 2)
        prior_loss_l3 = ((log_l3 - math.log(0.05)) ** 2) / (2 * 0.5 ** 2)
        prior_loss_hot = (beta_hot ** 2) / (2 * 0.2 ** 2)
        prior_loss_injury = (beta_injury ** 2) / (2 * 0.2 ** 2)
        
        return likelihood_loss + prior_loss_att + prior_loss_def + prior_loss_ha + prior_loss_l3 + prior_loss_hot + prior_loss_injury
        
    def fit(self, df_matches):
        df_filtered = df_matches.filter((pl.col("home_team").is_in(self.teams)) & (pl.col("away_team").is_in(self.teams)))
        home_idxs = np.array([self.team_to_idx[name] for name in df_filtered["home_team"]])
        away_idxs = np.array([self.team_to_idx[name] for name in df_filtered["away_team"]])
        home_goals = df_filtered["home_score"].to_numpy().astype(int)
        away_goals = df_filtered["away_score"].to_numpy().astype(int)
        weights = df_filtered["weight"].to_numpy().astype(float)
        is_hot = df_filtered["is_hot"].to_numpy().astype(float)
        
        neutral_val = df_filtered["neutral"].to_numpy().astype(bool)
        home_names = df_filtered["home_team"].to_numpy()
        is_host = np.array([name in ["USA", "Canada", "Mexico"] for name in home_names])
        is_home_adv = ((~neutral_val) | is_host).astype(float)
        
        initial_params = np.concatenate([self.log_attack, self.log_defense, [self.log_home_adv], [self.log_covariance], [self.beta_hot], [self.beta_injury]])
        bounds = [(None, None)] * (2 * self.num_teams) + [(-1.0, 1.0), (-4.0, -1.0), (-1.0, 1.0), (-1.0, 1.0)]
        
        home_injury = df_filtered["home_injury_rate"].to_numpy().astype(float)
        away_injury = df_filtered["away_injury_rate"].to_numpy().astype(float)
        
        res = minimize(self._loss_function, initial_params, args=(home_idxs, away_idxs, home_goals, away_goals, weights, is_home_adv, is_hot, home_injury, away_injury), method='L-BFGS-B', bounds=bounds)
        if res.success:
            self.log_attack = res.x[:self.num_teams]
            self.log_defense = res.x[self.num_teams:2*self.num_teams]
            self.log_home_adv = float(res.x[2*self.num_teams])
            self.log_covariance = float(res.x[2*self.num_teams + 1])
            self.beta_hot = float(res.x[2*self.num_teams + 2])
            self.beta_injury = float(res.x[2*self.num_teams + 3])
            
    def predict_match(self, home_team, away_team, is_hot=False, home_injury_rate=0.0, away_injury_rate=0.0, max_goals=5):
        home_idx = self.team_to_idx[home_team]
        away_idx = self.team_to_idx[away_team]
        is_home_adv = home_team in ["USA", "Canada", "Mexico"]
        ha_mult = math.exp(self.log_home_adv) if is_home_adv else 1.0
        hot_mult = math.exp(self.beta_hot) if is_hot else 1.0
        injury_mult_h = math.exp(self.beta_injury * home_injury_rate)
        injury_mult_a = math.exp(self.beta_injury * away_injury_rate)
        
        l1 = math.exp(self.log_attack[home_idx] + self.log_defense[away_idx]) * ha_mult * hot_mult * injury_mult_h
        l2 = math.exp(self.log_attack[away_idx] + self.log_defense[home_idx]) * hot_mult * injury_mult_a
        l3 = math.exp(self.log_covariance)
        
        grid = np.zeros((max_goals + 1, max_goals + 1))
        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                grid[x, y] = self._bivariate_poisson_pmf(x, y, l1, l2, l3)
                
        grid_sum = np.sum(grid)
        if grid_sum > 0:
            grid /= grid_sum
            
        win_home = np.sum(np.tril(grid, -1))
        draw = np.sum(np.diag(grid))
        win_away = np.sum(np.triu(grid, 1))
        
        return {
            "home_xG": l1 + l3,
            "away_xG": l2 + l3,
            "home_win": float(win_home),
            "away_win": float(win_away),
            "draw": float(draw),
            "score_probabilities": grid.tolist()
        }


# --- 3. Elo Rating and Elo-Poisson Model ---
class EloModel:
    def __init__(self, team_list):
        self.teams = sorted(team_list)
        self.elo_ratings = {team: 1500.0 for team in self.teams}
        
        # Regression coefficients for Expected Goals
        self.beta_0 = -0.15
        self.beta_1 = 0.0012
        self.beta_ha = 0.18
        self.beta_hot = 0.0
        self.beta_injury = 0.0
        
    def fit_elo_history(self, results_csv_path):
        """Walks matches chronologically to estimate Elo ratings."""
        print("Calculating historical Elo ratings...")
        
        # Read historical results sorted by date ascending
        df_hist = pl.read_csv(results_csv_path, null_values="NA").sort("date")
        
        # Clean team mappings
        from src.data_collector import NAME_MAP
        
        for row in df_hist.iter_rows(named=True):
            home_raw = row['home_team']
            away_raw = row['away_team']
            
            # Standardize names
            home = NAME_MAP.get(home_raw, home_raw)
            away = NAME_MAP.get(away_raw, away_raw)
            
            # Skip if either team is not tracked
            if home not in self.elo_ratings or away not in self.elo_ratings:
                continue
                
            h_score = row['home_score']
            a_score = row['away_score']
            if h_score is None or a_score is None:
                continue
                
            # Compute match outcome
            h_goals = int(h_score)
            a_goals = int(a_score)
            
            w_h = 1.0 if h_goals > a_goals else 0.5 if h_goals == a_goals else 0.0
            
            # Standard Elo update
            r_h = self.elo_ratings[home]
            r_a = self.elo_ratings[away]
            
            e_h = 1.0 / (1.0 + 10.0 ** ((r_a - r_h) / 400.0))
            
            # K-factor scaling based on goal difference and match weight
            gd = abs(h_goals - a_goals)
            k_mult = 1.0
            if gd > 1:
                k_mult = 1.5 + (gd - 2) * 0.25
                
            k = 30.0 * k_mult
            
            self.elo_ratings[home] += k * (w_h - e_h)
            self.elo_ratings[away] += k * ((1.0 - w_h) - (1.0 - e_h))
            
        print("Finished calculating Elo ratings.")
        
    def _loss_function(self, params, elo_diffs, home_goals, away_goals, weights, is_home_adv, is_hot, home_injury, away_injury):
        b0, b1, bha, beta_hot, beta_injury = params
        l1 = np.exp(b0 + b1 * elo_diffs + bha * is_home_adv + beta_hot * is_hot + beta_injury * home_injury)
        l2 = np.exp(b0 - b1 * elo_diffs + beta_hot * is_hot + beta_injury * away_injury)
        
        nll_h = -weights * (home_goals * np.log(l1) - l1)
        nll_a = -weights * (away_goals * np.log(l2) - l2)
        
        return np.sum(nll_h) + np.sum(nll_a)
        
    def fit_poisson_regression(self, df_matches):
        """Fits Poisson parameters relating Elo difference to expected goals."""
        print("Fitting Elo-Poisson goal regression parameters...")
        df_filtered = df_matches.filter((pl.col("home_team").is_in(self.teams)) & (pl.col("away_team").is_in(self.teams)))
        
        elo_h = np.array([self.elo_ratings[name] for name in df_filtered["home_team"]])
        elo_a = np.array([self.elo_ratings[name] for name in df_filtered["away_team"]])
        elo_diffs = elo_h - elo_a
        
        home_goals = df_filtered["home_score"].to_numpy().astype(int)
        away_goals = df_filtered["away_score"].to_numpy().astype(int)
        weights = df_filtered["weight"].to_numpy().astype(float)
        is_hot = df_filtered["is_hot"].to_numpy().astype(float)
        home_injury = df_filtered["home_injury_rate"].to_numpy().astype(float)
        away_injury = df_filtered["away_injury_rate"].to_numpy().astype(float)
        
        neutral_val = df_filtered["neutral"].to_numpy().astype(bool)
        home_names = df_filtered["home_team"].to_numpy()
        is_host = np.array([name in ["USA", "Canada", "Mexico"] for name in home_names])
        is_home_adv = ((~neutral_val) | is_host).astype(float)
        
        initial_params = [self.beta_0, self.beta_1, self.beta_ha, self.beta_hot, self.beta_injury]
        bounds = [(-2.0, 1.0), (0.0, 0.01), (-1.0, 1.0), (-1.0, 1.0), (-1.0, 1.0)]
        
        res = minimize(self._loss_function, initial_params, args=(elo_diffs, home_goals, away_goals, weights, is_home_adv, is_hot, home_injury, away_injury), method='L-BFGS-B', bounds=bounds)
        if res.success:
            self.beta_0, self.beta_1, self.beta_ha, self.beta_hot, self.beta_injury = res.x
            print(f"Fitted Elo-Poisson: beta_0={self.beta_0:.4f}, beta_1={self.beta_1:.6f}, beta_ha={self.beta_ha:.4f}, beta_hot={self.beta_hot:.4f}, beta_injury={self.beta_injury:.4f}")
            
    def predict_match(self, home_team, away_team, is_hot=False, home_injury_rate=0.0, away_injury_rate=0.0, max_goals=5):
        r_h = self.elo_ratings[home_team]
        r_a = self.elo_ratings[away_team]
        elo_diff = r_h - r_a
        
        is_home_adv = home_team in ["USA", "Canada", "Mexico"]
        ha_val = 1.0 if is_home_adv else 0.0
        hot_val = 1.0 if is_hot else 0.0
        
        lmbda = math.exp(self.beta_0 + self.beta_1 * elo_diff + self.beta_ha * ha_val + self.beta_hot * hot_val + self.beta_injury * home_injury_rate)
        mu = math.exp(self.beta_0 - self.beta_1 * elo_diff + self.beta_hot * hot_val + self.beta_injury * away_injury_rate)
        
        # Predict Poisson scores
        p_home = np.array([(lmbda ** g) * math.exp(-lmbda) / math.factorial(g) for g in range(max_goals + 1)])
        p_away = np.array([(mu ** g) * math.exp(-mu) / math.factorial(g) for g in range(max_goals + 1)])
        grid = np.outer(p_home, p_away)
        
        grid_sum = np.sum(grid)
        if grid_sum > 0:
            grid /= grid_sum
            
        win_home = np.sum(np.tril(grid, -1))
        draw = np.sum(np.diag(grid))
        win_away = np.sum(np.triu(grid, 1))
        
        return {
            "home_xG": lmbda,
            "away_xG": mu,
            "home_win": float(win_home),
            "away_win": float(win_away),
            "draw": float(draw),
            "score_probabilities": grid.tolist()
        }


# --- 4. Softmax Classifier Model ---
class SoftmaxClassifierModel:
    def __init__(self, team_list, team_ranks):
        self.teams = sorted(team_list)
        self.ranks = team_ranks
        
        # Softmax coefficients: [Intercept, Elo difference, Rank difference, Home Advantage, Hot, Injury Difference]
        self.w_home = np.array([0.10, 0.0015, 0.015, 0.20, 0.0, 0.0]) # Logits for home win
        self.w_draw = np.array([-0.80, -0.0002, -0.005, -0.05, 0.0, 0.0]) # Logits for draw
        # baseline: w_away = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
    def _softmax(self, zh, zd):
        # baseline za = 0
        exp_h = np.exp(zh)
        exp_d = np.exp(zd)
        denom = exp_h + exp_d + 1.0
        return exp_h / denom, exp_d / denom, 1.0 / denom
        
    def _loss_function(self, params, X, outcomes, weights):
        # params: [w_home (6), w_draw (6)]
        w_h = params[:6]
        w_d = params[6:]
        
        zh = X.dot(w_h)
        zd = X.dot(w_d)
        
        # Softmax probabilities
        exp_h = np.exp(zh)
        exp_d = np.exp(zd)
        denom = exp_h + exp_d + 1.0
        
        p_h = exp_h / denom
        p_d = exp_d / denom
        p_a = 1.0 / denom
        
        # Compute loss
        loss = 0.0
        for i in range(len(outcomes)):
            actual = outcomes[i]
            if actual == 0: # Home Win
                p = p_h[i]
            elif actual == 1: # Draw
                p = p_d[i]
            else: # Away Win
                p = p_a[i]
            loss += -weights[i] * math.log(max(1e-15, p))
            
        # Add regularization (L2)
        l2 = 0.01 * (np.sum(w_h ** 2) + np.sum(w_d ** 2))
        return loss + l2
        
    def fit(self, df_matches, elo_ratings):
        """Fits multinomial logit coefficients using Elo and Rank features."""
        print("Fitting Softmax Classifier coefficients...")
        df_filtered = df_matches.filter((pl.col("home_team").is_in(self.teams)) & (pl.col("away_team").is_in(self.teams)))
        
        elo_h = np.array([elo_ratings[name] for name in df_filtered["home_team"]])
        elo_a = np.array([elo_ratings[name] for name in df_filtered["away_team"]])
        elo_diffs = elo_h - elo_a
        
        rank_h = np.array([self.ranks.get(name, 30) for name in df_filtered["home_team"]])
        rank_a = np.array([self.ranks.get(name, 30) for name in df_filtered["away_team"]])
        rank_diffs = rank_a - rank_h # positive means home has a better rank (lower rank index)
        
        neutral_val = df_filtered["neutral"].to_numpy().astype(bool)
        home_names = df_filtered["home_team"].to_numpy()
        is_host = np.array([name in ["USA", "Canada", "Mexico"] for name in home_names])
        is_home_adv = ((~neutral_val) | is_host).astype(float)
        is_hot = df_filtered["is_hot"].to_numpy().astype(float)
        home_injury = df_filtered["home_injury_rate"].to_numpy().astype(float)
        away_injury = df_filtered["away_injury_rate"].to_numpy().astype(float)
        injury_diffs = home_injury - away_injury
        
        # Design matrix X: [Intercept, Elo difference, Rank difference, Home Advantage, Is Hot, Injury Difference]
        N = len(df_filtered)
        X = np.column_stack([
            np.ones(N),
            elo_diffs,
            rank_diffs,
            is_home_adv,
            is_hot,
            injury_diffs
        ])
        
        # Outcomes: 0=Home Win, 1=Draw, 2=Away Win
        home_goals = df_filtered["home_score"].to_numpy().astype(int)
        away_goals = df_filtered["away_score"].to_numpy().astype(int)
        
        outcomes = []
        for i in range(N):
            if home_goals[i] > away_goals[i]:
                outcomes.append(0)
            elif home_goals[i] == away_goals[i]:
                outcomes.append(1)
            else:
                outcomes.append(2)
        outcomes = np.array(outcomes)
        weights = df_filtered["weight"].to_numpy().astype(float)
        
        initial_params = np.concatenate([self.w_home, self.w_draw])
        
        res = minimize(self._loss_function, initial_params, args=(X, outcomes, weights), method='BFGS')
        if res.success:
            self.w_home = res.x[:6]
            self.w_draw = res.x[6:]
            print(f"Fitted Softmax Classifier coefficients successfully.")
            
    def predict_match(self, home_team, away_team, elo_ratings, elo_poisson_model, is_hot=False, home_injury_rate=0.0, away_injury_rate=0.0):
        """Predicts probabilities and generates score grid mapping outcome probs to Elo expected goals."""
        r_h = elo_ratings[home_team]
        r_a = elo_ratings[away_team]
        elo_diff = r_h - r_a
        
        rank_h = self.ranks.get(home_team, 30)
        rank_a = self.ranks.get(away_team, 30)
        rank_diff = rank_a - rank_h
        
        is_home_adv = 1.0 if home_team in ["USA", "Canada", "Mexico"] else 0.0
        hot_val = 1.0 if is_hot else 0.0
        injury_diff = home_injury_rate - away_injury_rate
        
        x_vec = np.array([1.0, elo_diff, rank_diff, is_home_adv, hot_val, injury_diff])
        
        zh = x_vec.dot(self.w_home)
        zd = x_vec.dot(self.w_draw)
        
        p_h, p_d, p_a = self._softmax(zh, zd)
        
        # For the goals projection, we borrow expected goals from the Elo-Poisson model
        pred_goals = elo_poisson_model.predict_match(home_team, away_team, is_hot=is_hot, home_injury_rate=home_injury_rate, away_injury_rate=away_injury_rate)
        lmbda = pred_goals["home_xG"]
        mu = pred_goals["away_xG"]
        
        # Build raw Poisson grid
        max_goals = 5
        grid = np.zeros((max_goals + 1, max_goals + 1))
        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                grid[x, y] = ((lmbda ** x) * math.exp(-lmbda) / math.factorial(x)) * ((mu ** y) * math.exp(-mu) / math.factorial(y))
                
        # Split grid into Home, Draw, Away components and adjust their sums to match predicted Softmax probabilities
        win_mask = np.tril(np.ones_like(grid), -1).astype(bool)
        draw_mask = np.diag(np.ones(max_goals + 1)).astype(bool)
        loss_mask = np.triu(np.ones_like(grid), 1).astype(bool)
        
        sum_w = np.sum(grid[win_mask])
        sum_d = np.sum(grid[draw_mask])
        sum_l = np.sum(grid[loss_mask])
        
        if sum_w > 0: grid[win_mask] *= (p_h / sum_w)
        if sum_d > 0: grid[draw_mask] *= (p_d / sum_d)
        if sum_l > 0: grid[loss_mask] *= (p_a / sum_l)
        
        grid_sum = np.sum(grid)
        if grid_sum > 0:
            grid /= grid_sum
            
        return {
            "home_xG": lmbda,
            "away_xG": mu,
            "home_win": float(p_h),
            "away_win": float(p_a),
            "draw": float(p_d),
            "score_probabilities": grid.tolist()
        }


# --- Unified Parameters Exporter ---
def export_all_models(file_path, dc_model, bp_model, elo_model, sm_model):
    """Exports all model weights and ratings into a single JSON parameter file."""
    from src.preprocessor import load_injury_rates
    injury_rates = load_injury_rates("data/player_profiles.md")
    
    parameters = {
        "dixon_coles": {
            "rho": dc_model.rho,
            "home_advantage_multiplier": math.exp(dc_model.log_home_adv),
            "beta_hot": dc_model.beta_hot,
            "beta_injury": dc_model.beta_injury,
            "teams": {}
        },
        "bivariate": {
            "log_covariance": bp_model.log_covariance,
            "home_advantage_multiplier": math.exp(bp_model.log_home_adv),
            "beta_hot": bp_model.beta_hot,
            "beta_injury": bp_model.beta_injury,
            "teams": {}
        },
        "elo": {
            "beta_0": elo_model.beta_0,
            "beta_1": elo_model.beta_1,
            "beta_ha": elo_model.beta_ha,
            "beta_hot": elo_model.beta_hot,
            "beta_injury": elo_model.beta_injury,
            "teams": {}
        },
        "classifier": {
            "w_home": sm_model.w_home.tolist(),
            "w_draw": sm_model.w_draw.tolist()
        }
    }
    
    # Save per-team parameters
    for team in dc_model.teams:
        # 1. Dixon-Coles team ratings
        dc_idx = dc_model.team_to_idx[team]
        dc_att = math.exp(dc_model.log_attack[dc_idx])
        dc_dfn = math.exp(dc_model.log_defense[dc_idx])
        injury_rate = injury_rates.get(team, 0.0)
        parameters["dixon_coles"]["teams"][team] = {
            "attack": dc_att,
            "defense": dc_dfn,
            "formation": dc_model.formations.get(team, "4-3-3"),
            "rank": dc_model.ranks.get(team, 30),
            "injury_rate": injury_rate
        }
        
        # 2. Bivariate Poisson team ratings
        bp_idx = bp_model.team_to_idx[team]
        bp_att = math.exp(bp_model.log_attack[bp_idx])
        bp_dfn = math.exp(bp_model.log_defense[bp_idx])
        parameters["bivariate"]["teams"][team] = {
            "attack": bp_att,
            "defense": bp_dfn
        }
        
        # 3. Elo ratings
        parameters["elo"]["teams"][team] = {
            "rating": elo_model.elo_ratings[team]
        }
        
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(parameters, f, indent=2)
    print(f"Exported all model parameters to {file_path}")
