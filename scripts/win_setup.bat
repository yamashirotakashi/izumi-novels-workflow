@echo off
echo IzumiNovels-Workflow Windows Setup
echo =====================================

cd /d C:\Users\tky99\DEV\izumi-novels-workflow

echo Creating required directories...
if not exist "reports" mkdir reports
if not exist "logs" mkdir logs

echo Removing existing Windows virtual environment...
if exist "venv_windows" rmdir /s /q venv_windows

echo Creating fresh Windows virtual environment...
python -m venv venv_windows

echo Activating virtual environment...
call venv_windows\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Windows-specific dependencies...
pip install -r requirements_windows.txt

echo Testing basic imports...
python -c "import selenium; print('✅ Selenium: OK')"
python -c "import undetected_chromedriver; print('✅ Undetected Chrome: OK')"
python -c "import bs4; print('✅ BeautifulSoup: OK')"
python -c "import requests; print('✅ Requests: OK')"

echo.
echo Windows setup completed successfully!
echo Next: Run 'venv_windows\Scripts\python.exe phase1_verification_final.py' to test
pause