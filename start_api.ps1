Write-Host "Netflix Churn Prediction - Starting Application"
Write-Host ("=" * 60)

# Activate virtual environment
$venv = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    & $venv
}

# Set environment variables
$env:FLASK_APP = "src/api/app.py"
$env:FLASK_ENV = "development"
$env:PORT = "5000"

# Load environment variables from .env if exists
$envFile = ".\.env"
if (Test-Path $envFile) {
    Write-Host "Loading environment variables from .env"
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $env[$matches[1]] = $matches[2]
        }
    }
}

# Create directories if missing
$dirs = @("data", "models")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        Write-Host "Creating directory: $dir"
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

# Generate sample data if missing
$sampleData = "data/netflix_customers_sample.csv"
if (!(Test-Path $sampleData)) {
    Write-Host "Generating sample customer data..."
    python scripts/generate_sample_data.py
}

# Train model if missing
$modelFile = "models/netflix_churn_model.pkl"
if (!(Test-Path $modelFile)) {
    Write-Host "Training ML model..."
    python src/models/train.py
}

# Initialize database
Write-Host "Initializing database..."
python -c "from src.utils.db import init_database; init_database()"

# Start Flask app
Write-Host ""
Write-Host "Starting Flask server on http://localhost:$env:PORT"
Write-Host ("=" * 60)
Write-Host ""
Write-Host "Default credentials:"
Write-Host "   User: user / password123"
Write-Host "   Admin: admin / admin123"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

python -m flask run --host=127.0.0.1 --port=$env:PORT
