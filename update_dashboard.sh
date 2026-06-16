#!/bin/bash
# Exit immediately if any command fails
set -e

echo "========================================================"
echo "  FIFA WC 2026 Prediction Dashboard Daily Updater       "
echo "========================================================"

# Detect Python interpreter (prefer Miniconda if available)
PYTHON_CMD="python3"
if [ -f "/Users/ajaychawda/miniconda3/bin/python3" ]; then
  PYTHON_CMD="/Users/ajaychawda/miniconda3/bin/python3"
  echo "Using Conda Python interpreter: $PYTHON_CMD"
else
  echo "Using system Python interpreter: $PYTHON_CMD"
fi

# 1. Pull latest changes from origin to avoid conflicts
echo "1. Pulling latest code changes from origin..."
git pull origin main

# 2. Run data collector to update matches and schedule
echo "2. Re-generating tournament match schedules and profile data..."
$PYTHON_CMD src/data_collector.py

# 3. Fit models and calculate predictions
echo "3. Training prediction models and regenerating forecasts..."
PYTHONPATH=. $PYTHON_CMD src/run_pipeline.py

# 4. Run automated tests to verify math
echo "4. Running mathematical consistency and file output tests..."
PYTHONPATH=. $PYTHON_CMD tests/validate_pipeline.py

# 5. Git commit and push updated data files
echo "5. Checking for modifications to commit..."
git add data/model_parameters.json data/wc_2026_matches.json src/data_collector.py

if ! git diff --cached --quiet; then
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
