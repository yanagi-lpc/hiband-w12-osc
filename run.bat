@echo off
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 以上が見つかりません。
  pause
  exit /b 1
)

if not exist ".venv\Scripts\hiband-w12-osc.exe" (
  echo 初回セットアップをしています。
  python -m venv .venv
  if errorlevel 1 (
    echo 仮想環境を作れませんでした。
    pause
    exit /b 1
  )
  .venv\Scripts\python.exe -m pip install -e .
  if errorlevel 1 (
    echo インストールに失敗しました。
    pause
    exit /b 1
  )
)

.venv\Scripts\hiband-w12-osc.exe %*
echo.
pause
