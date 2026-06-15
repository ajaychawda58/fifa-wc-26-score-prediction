#!/bin/bash
# Exit immediately if any command fails
set -e

echo "========================================================"
echo "  FIFA WC 2026 Prediction Dashboard Daily Updater       "
echo "========================================================"

# 1. Pull latest changes from origin to avoid conflicts
echo "1. Pulling latest code changes from origin..."
git pull origin main

# 2. Run data collector to update matches and schedule
echo "2. Re-generating tournament match schedules and profile data..."
python3 src/data_collector.py

# 3. Fit models and calculate predictions
echo "3. Training prediction models and regenerating forecasts..."
PYTHONPATH=. python3 src/run_pipeline.py

# 4. Run automated tests to verify math
echo "4. Running mathematical consistency and file output tests..."
PYTHONPATH=. python3 tests/validate_pipeline.py

# 5. Git commit and push updated data files
echo "5. Checking for modifications to commit..."
git add data/model_parameters.json data/wc_2026_matches.json src/data_collector.py

if ! git diff-index --quiet HEAD --; then
  echo "   Modifications detected. Committing changes..."
  git commit -m "data: Daily match results update and model retraining"
  echo "6. Pushing updates to GitHub..."
  git push origin main
  echo "========================================================"
  echo "  Dashboard successfully updated and deployed to GitHub! "
  echo "========================================================"
else
  echo "   No data changes detected. Repository is already up to date."
  echo "========================================================"
fi
