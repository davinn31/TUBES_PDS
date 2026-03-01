@echo off
echo ========================================
echo   Switch Branch from Master to Main
echo ========================================
echo.

REM Check if git is initialized
if not exist ".git" (
    echo ERROR: Git not initialized in this folder!
    pause
    exit /b
)

REM Check current branch
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i
echo Current branch: %BRANCH%
echo.

REM Step 1: Rename local branch from master to main
echo Step 1: Renaming local branch from master to main...
git branch -m master main
if errorlevel 1 (
    echo ERROR: Failed to rename branch. Make sure you're on master branch.
    pause
    exit /b
)
echo SUCCESS: Local branch renamed to main
echo.

REM Step 2: Instructions for GitHub
echo Step 2: Change default branch on GitHub
echo ========================================
echo PLEASE DO THE FOLLOWING MANUALLY:
echo 1. Go to: https://github.com/davinn31/TUBES_PDS/settings/branches
echo 2. Click the pencil icon next to "master"
echo 3. Change "Default branch" to "main"
echo 4. Click "Save"
echo ========================================
echo.
set /p gh_done="Press Enter after you've changed the default branch on GitHub..."
echo.

REM Step 3: Fetch latest and handle non-fast-forward error
echo Step 3: Setting upstream to origin/main...
git fetch origin

REM Check if push fails due to non-fast-forward
git push -u origin main --force
if errorlevel 1 (
    echo.
    echo WARNING: Normal push failed. Trying force push...
    echo This is needed because remote has different history.
    git push -u origin main --force
    if errorlevel 1 (
        echo ERROR: Failed to push. Please check your GitHub credentials and permissions.
        pause
        exit /b
    )
)
echo SUCCESS: Pushed to origin/main
echo.

REM Step 4: Delete old master branch (optional)
echo Step 4: Deleting old master branch from remote...
git push origin --delete master
if errorlevel 1 (
    echo Note: Could not delete remote master branch.
    echo This is normal if you don't have permission or branch doesn't exist remotely.
) else (
    echo SUCCESS: Remote master branch deleted
)
echo.

REM Step 5: Verify the setup
echo Step 5: Verifying setup...
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set NEW_BRANCH=%%i
echo Current branch: %NEW_BRANCH%
echo.

echo ========================================
echo   COMPLETE!
echo   Your default branch is now: main
echo ========================================
echo.
echo You can now use quick_push.bat to push to main branch!
pause
