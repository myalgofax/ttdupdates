@echo off
echo "== Initializing repo =="
echo "# myalgoapp" > README.md

REM Init git only if not already initialized
IF NOT EXIST ".git" git init

REM Stage and commit
git add .
git commit -m "first commit"

REM Set branch
git branch -M main

REM Add remote only if not already added
git remote remove origin 2>nul
git remote add origin https://github.com/myalgofax/ttdupdates.git

REM Push to GitHub
git push -u origin main

echo === Commit Complete ===

REM Deploy (this assumes deploy script is correctly set up in package.json)
echo === Deploying the app ===
REM call npm run deploy

echo === Deployment Complete ===
pause
