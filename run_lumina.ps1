# Lumina launcher — always loads env vars from Windows User environment
# before starting Streamlit, so the API key is always available.
# Usage: Right-click → "Run with PowerShell"  OR  just run:  .\run_lumina.ps1

$key = [System.Environment]::GetEnvironmentVariable("OPENWEBNINJA_API_KEY", "User")
if ($key) {
    $env:OPENWEBNINJA_API_KEY = $key
    Write-Host "✓ OPENWEBNINJA_API_KEY loaded from system environment." -ForegroundColor Green
} else {
    Write-Host "⚠ OPENWEBNINJA_API_KEY not found. Run: setx OPENWEBNINJA_API_KEY `"your-key-here`"" -ForegroundColor Yellow
}

Write-Host "Starting Lumina..." -ForegroundColor Cyan
streamlit run app.py
