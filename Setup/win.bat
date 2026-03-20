@echo off
setlocal EnableDelayedExpansion

:: --- Change directory ---
cd /d "%~dp0"

:: --- Administrator Check ---
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo.
    echo ==========================================================
    echo ERROR: Administrator privileges are required.
    echo Please right-click this .bat file and select 'Run as administrator'.
    echo ==========================================================
    echo.
    goto :error_pause
)

:: --- Script Checks ---
if not exist "create_links.py" (
    echo ERROR: Could not find 'create_links.py' in the same directory as this script.
    goto :error_pause
)
if not exist "generate_manifest.py" (
    echo ERROR: Could not find 'generate_manifest.py' in the same directory as this script.
    goto :error_pause
)

:: --- Profile Path ---
set "PROFILE_NAME=h2-dev"
set "PROFILE_PATH=%APPDATA%\r2modmanPlus-local\HadesII\profiles\%PROFILE_NAME%\ReturnOfModding"
set "R2M_DIR=%~dp0"

echo.
echo ==========================================================
echo   adamant modpack - full local deployment
echo   Profile: %PROFILE_NAME%
echo ==========================================================
echo.

:: --- Process each mod directory ---
set "MOD_COUNT=0"
set "ROOT=%~dp0.."

:: Core and Lib (top-level)
for %%d in ("%ROOT%\adamant-modpack-Core" "%ROOT%\adamant-modpack-Lib") do (
    if exist "%%~d\thunderstore.toml" (
        call :setup_mod "%%~d"
    )
)

:: All submodules
for /D %%d in ("%ROOT%\Submodules\adamant-*") do (
    if exist "%%~d\thunderstore.toml" (
        call :setup_mod "%%~d"
    )
)

echo.
echo ==========================================================
echo   Done. %MOD_COUNT% mods deployed.
echo ==========================================================
echo.

pause
goto :eof

:: ####################################################################
:: --- Subroutine: set up a single mod ---
:: ####################################################################
:setup_mod
set "MOD_DIR=%~1"

:: Parse namespace and name from thunderstore.toml
set "TS_NAMESPACE="
set "TS_NAME="

FOR /F "tokens=2 delims== " %%i IN ('findstr /B /C:"namespace =" "%MOD_DIR%\thunderstore.toml"') DO (
    SET "TS_NAMESPACE=%%~i"
)
FOR /F "tokens=2 delims== " %%i IN ('findstr /B /C:"name =" "%MOD_DIR%\thunderstore.toml"') DO (
    SET "TS_NAME=%%~i"
)

if not defined TS_NAMESPACE (
    echo SKIP: Could not parse namespace from %MOD_DIR%\thunderstore.toml
    goto :eof
)
if not defined TS_NAME (
    echo SKIP: Could not parse name from %MOD_DIR%\thunderstore.toml
    goto :eof
)

set "MOD_NAME=%TS_NAMESPACE%-%TS_NAME%"
echo --- Setting up: %MOD_NAME% ---

:: --- Copy icon and LICENSE into src ---
if exist "%R2M_DIR%icon.png" (
    copy /Y "%R2M_DIR%icon.png" "%MOD_DIR%\src\icon.png" >nul
    echo   Copied icon.png
)
if exist "%R2M_DIR%LICENSE" (
    copy /Y "%R2M_DIR%LICENSE" "%MOD_DIR%\src\LICENSE" >nul
    echo   Copied LICENSE
)

:: --- Generate manifest.json from thunderstore.toml ---
python "generate_manifest.py" "%MOD_DIR%\thunderstore.toml" "%MOD_DIR%\src\manifest.json"

:: --- Create symlinks ---
set "FOLDER1=%MOD_DIR%\src"
set "FOLDER2=%MOD_DIR%\data"
set "LINK1=%PROFILE_PATH%\plugins\%MOD_NAME%"
set "LINK2=%PROFILE_PATH%\plugins_data\%MOD_NAME%"

python "create_links.py" "%FOLDER1%" "%FOLDER2%" "%LINK1%" "%LINK2%"

set /a MOD_COUNT+=1
echo.
goto :eof

:error_pause
pause
goto :eof
