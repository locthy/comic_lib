@echo off
echo Checking required Python libraries...

set MISSING=0

pip show requests >nul 2>&1 || set MISSING=1
pip show beautifulsoup4 >nul 2>&1 || set MISSING=1
pip show colorama >nul 2>&1 || set MISSING=1
pip show flask >nul 2>&1 || set MISSING=1
pip show python-dotenv >nul 2>&1 || set MISSING=1

if %MISSING%==1 (
    echo Some packages are missing. Installing from requirements.txt...
    pip install -r requirements.txt
) else (
    echo All required packages are already installed.
)

echo.
echo Done!
pause