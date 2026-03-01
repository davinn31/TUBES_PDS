@echo off
echo ========================================
echo   Git Setup for This Project
echo ========================================
echo.

echo Configuring Git...
git config --global user.name "YOUR_GITHUB_USERNAME"
git config --global user.email "your-email@example.com"

echo.
echo Initializing Git repository...
git init

echo.
echo Adding all files...
git add .

echo.
echo Creating initial commit...
git commit -m "Initial commit - PPDB Jawa Barat Dashboard"

echo.
echo ========================================
echo   SETUP INSTRUCTIONS:
echo ========================================
echo.
echo 1. Create a new repository on GitHub.com
echo    (Go to: https://github.com/new)
echo.
echo 2. Copy your repository URL
echo    Example: https://github.com/username/repo-name.git
echo.
echo 3. Run this command (replace with your URL):
echo    git remote add origin https://github.com/username/repo-name.git
echo.
echo 4. Then push to GitHub with:
echo    git push -u origin main
echo.
echo ========================================
echo.
echo After completing step 3 above, you can
echo use push.bat to upload changes!
echo.
pause
