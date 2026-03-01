@echo off
echo ========================================
echo   GitHub Auto-Push Script
echo ========================================
echo.

echo Adding files to Git...
git add .
echo.

echo Enter your commit message:
set /p commit_msg="> "

if "%commit_msg%"=="" (
    echo Commit message cannot be empty!
    pause
    exit /b
)

git commit -m "%commit_msg%"
echo.

echo Pushing to GitHub...
git push origin main
echo.

echo ========================================
echo   Done! Files uploaded to GitHub
echo ========================================
pause
