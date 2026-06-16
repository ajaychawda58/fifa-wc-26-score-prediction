# FIFA World Cup 2026 Score Prediction Engine

This project is an advanced, end-to-end match score prediction engine for the FIFA World Cup 2026. It fits parameters on over 50,000 international matches using a combination of Bayesian inference, Poisson processes, Elo ratings, and multinomial logistic classification. 

All predictions and simulation systems run completely client-side in the browser using static parameters exported from the Python pipeline, making it lightweight and suitable for zero-server deployment (e.g. GitHub Pages).

*This project is built for educational/experimental purposes and is not intended to be used for betting or gambling.*

---

## 📊 Data Sources

The prediction engine pulls and synthesizes data from several different directories to feed the modeling pipeline:

1. **Historical International Matches (1872–Present)**: 
   * **Source**: [Mart Jürisoo's International Football Results Dataset](https://github.com/martj42/international_results).
   * **Usage**: Over 50,000 historical international matches are loaded and processed using Polars to build team Elo ratings chronologically and train model regression coefficients.
2. **FIFA World Cup 2026 Group Fixtures**:
   * **Source**: Parsed from the scheduled tournament entries in the international results database.
   * **Usage**: Defines the real match pairings, dates, and venues for all 72 group stage matches.
3. **Squad Rosters & Player Metadata**:
   * **Source**: Scraped from the Wikipedia page [2026 FIFA World Cup squads](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads).
   * **Usage**: Loaded dynamically to retrieve player listings, ages, caps, goals, and club details for all 48 qualified countries.
4. **Squad Fitness & Injury Rates**:
   * **Source**: Deterministic hash-based player injury generator (simulating time since last injury between 0.5 and 35 months).
   * **Usage**: Used to aggregate squad-level injury percentages (players injured in the last 6 months) to fit the $\beta_{\text{injury}}$ regression parameters.
5. **Match Temperature & Weather**:
   * **Source**: Deterministic climate simulation (generating match temperature values between 15°C and 36°C).
   * **Usage**: Used to fit weather parameters ($\beta_{\text{hot}}$) and simulate temperature conditions in real time using the front-end slider.
6. **Rankings & Tactical Meta**:
   * **Source**: Structured metadata defining confederations, World Rankings, and preferred team formations.
   * **Usage**: Sets the Bayesian priors for the Dixon-Coles model and features for the Softmax logit regression.

---

## 🧠 How the Models Predict the Score

The system utilizes four distinct statistical/ML models, alongside a weighted ensemble that combines them:

### 1. Bayesian Dixon-Coles Model
The Dixon-Coles model is a classic framework in football analytics that models home and away goals as independent Poisson distributions, with an adjustment for low-scoring games:
* **Attack & Defense Parameters:** Each team has a latent attack rating ($\alpha$) and defense rating ($\beta$).
* **Bayesian Priors:** We define log-normal priors on team attack and defense ratings derived from their official FIFA World Rankings.
* **Low-Scoring Dependency Adjustment ($\rho$):** Traditional Poisson models underestimate the occurrence of low-scoring draws and clean-sheet wins. Dixon-Coles introduces a correction factor ($\tau$) that adjusts the joint probabilities for scorelines $(0,0)$, $(1,0)$, $(0,1)$, and $(1,1)$ based on a correlation parameter ($\rho$).
* **Home Advantage:** A global parameter ($\gamma$) is fitted to account for the goal boost of host countries (USA, Canada, Mexico).

### 2. Bivariate Poisson Model
Instead of assuming home and away goals are completely independent, the Bivariate Poisson model allows for dependency by using three Poisson variables:
* Goals scored by Home team: $X = Y_1 + Y_3$
* Goals scored by Away team: $Y = Y_2 + Y_3$
* $Y_1$, $Y_2$, and $Y_3$ are independent Poisson distributions with rates $\lambda_1, \lambda_2$, and $\lambda_3$.
* **Shared Covariance ($\lambda_3$):** Represents match-specific correlation factors (such as overall game tempo, weather, or refereeing style) that affect both teams equally. The covariance forces the goal counts to move together, predicting draw-heavy outcomes and cohesive high-scoring matches.

### 3. Elo-Poisson Model
This model leverages Elo ratings, which measure relative team strength dynamically:
* **Chronological Rating Updates:** The model walks through over 50,000 historical matches sequentially, adjusting team Elo ratings dynamically based on match importance, goal differences, and expectation values.
* **Poisson Regression:** We fit a exponential regression model mapping the difference in Elo rating ($R_{\text{home}} - R_{\text{away}}$) and home advantage to expected goals:
  $$\lambda_{\text{home}} = \exp(\beta_0 + \beta_1 \cdot \Delta\text{Elo} + \beta_{\text{HA}} \cdot \text{is\_host})$$
  $$\mu_{\text{away}} = \exp(\beta_0 - \beta_1 \cdot \Delta\text{Elo})$$
* These expected goals ($\lambda, \mu$) are then used to build standard Poisson probability distributions for the home and away teams.

### 4. ML Softmax Classifier (Multinomial Logistic Regression)
Instead of predicting goal counts first, this model directly predicts the probability of the match outcome (Home Win, Draw, Away Win) using machine learning classification:
* **Features:** Design matrix uses intercept, Elo rating difference, FIFA rank difference, and home advantage.
* **Softmax Logits:** Computes logits for Home Win ($z_H$) and Draw ($z_D$), setting Away Win as the baseline ($z_A = 0$):
  $$P(\text{Outcome}_k) = \frac{\exp(z_k)}{\sum_j \exp(z_j)}$$
* **Goal Grid Mapping:** To translate these win/draw/loss outcome probabilities back into scorelines on the dashboard, we generate a baseline Poisson goal grid (using Elo-Poisson expected goals) and scale the parts of the grid (Home Win cells, Draw cells, Away Win cells) so they sum precisely to the probabilities outputted by the Softmax Classifier.

### 5. Weighted Ensemble Model (Default)
The ensemble model combines all of the individual models to produce a robust, stabilized prediction:
* **Weights:** Dixon-Coles ($35\%$), Elo-Poisson ($30\%$), Bivariate Poisson ($20\%$), and Softmax Classifier ($15\%$).
* The ensemble averages the Expected Goals (xG) and outcomes of the 4 models, and computes a weighted average of the probability grids to yield a unified score projection.

---

## 🛠️ Usage Instructions

### 1. Daily Score Updates
To update the dashboard with daily match scores:
1. Open `src/data_collector.py` and navigate to `COMPLETED_MATCHES`.
2. Replace `None` in the `home_score` and `away_score` keys with the official final scores.
3. Save the file and run the automated updater:
   ```bash
   ./update_dashboard.sh
   ```
   This script will pull code updates, retrain the models, run mathematical validation tests, commit the changes, and deploy the new data to GitHub Pages.

### 2. Manual Execution
If you prefer running the pipeline components manually:
```bash
# 1. Update schedule and squad profile rosters
python3 src/data_collector.py

# 2. Re-fit prediction models and export parameters
PYTHONPATH=. python3 src/run_pipeline.py

# 3. Run automated mathematical tests
PYTHONPATH=. python3 tests/validate_pipeline.py
```

### 3. Local Dashboard Viewer
To view the glassmorphic interactive web dashboard locally:
```bash
python3 -m http.server 8000
```
Then visit **[http://localhost:8000](http://localhost:8000)** in your browser.
