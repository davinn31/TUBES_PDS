@echo off
echo ========================================
echo   First Time GitHub Setup
echo ========================================
echo.

REM Step 1: Configure Git
echo Step 1: Configuring Git...
echo Enter your GitHub username:
set /p GH_USER="> "
echo Enter your GitHub email:
set /p GH_EMAIL="> "

git config --global user.name "%GH_USER%"
git config --global user.email "%GH_EMAIL%"

echo.
echo Step 2: Initializing Git...
git init

echo.
echo Step 3: Adding files...
git add .
git commit -m "First commit"

echo.
echo Step 4: Setting up remote...
git remote add origin https://github.com/davinn31/TUBES_PDS.git

echo.
echo Step 5: Checking branch name...
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i
echo Your branch is: %BRANCH%

echo.
echo ========================================
echo   Ready to push!
echo ========================================
echo.
echo Run quick_push.bat to upload your files!
echo.
pause
