@echo off
setlocal EnableDelayedExpansion

if not defined STELLIO_MANAGER_RELAUNCHED (
    set "STELLIO_MANAGER_RELAUNCHED=1"
    cmd /k "%~f0"
    exit /b
)

chcp 65001 >nul
cd /d "%~dp0"


cls
echo ╔═══════════════════╗
echo ║  STELLIO MANAGER  ║
echo ╚═══════════════════╝
echo.

set "SRC_DIR=."
set "OUT_NAME=Stellio"

set "VERSION="

if exist "!SRC_DIR!\main.py" (
    for /f "tokens=2 delims==" %%a in ('findstr /R "^CURRENT_VERSION *" "!SRC_DIR!\main.py"') do (
        if not defined VERSION (
            set "VERSION=%%a"
            set "VERSION=!VERSION:"=!"
            set "VERSION=!VERSION: =!"
        )
    )
)
:VERSION_FOUND
if "!VERSION!"=="" (
    echo [!] Impossible de lire CURRENT_VERSION dans !SRC_DIR!\main.py.
    set "VERSION=0.0.0"
)

:ACTION_MENU
cls
echo ============================================
echo  !OUT_NAME!  —  version detectee : !VERSION!
echo ============================================
echo  [1] Lancer en mode test 
echo  [2] Lancer en mode test (DEBUG - logs detailles)
echo  [3] Lancer le dossier "test" (nouvelles fonctionnalites)
echo  [4] Verifier / installer les dependances
echo  [5] Quitter
echo.
set /p "ACTION=Votre choix (1 a 5) : "
set "ACTION=%ACTION: =%"

if "%ACTION%"=="1" (
    call :DO_LAUNCH_TEST
    goto :ACTION_MENU
)
if "%ACTION%"=="2" (
    call :DO_LAUNCH_TEST_DEBUG
    goto :ACTION_MENU
)
if "%ACTION%"=="3" (
    call :DO_LAUNCH_TEST_FOLDER
    goto :ACTION_MENU
)
if "%ACTION%"=="4" (
    call :CHECK_VENV
    call :INSTALL_AND_CHECK_DEPS
    pause
    goto :ACTION_MENU
)
if "%ACTION%"=="5" (
    echo.
    echo ============================================
    echo A bientot !
    echo ============================================
    pause
    exit /b
)

echo Choix invalide.
pause
goto :ACTION_MENU

:CHECK_VENV
if exist "venv\Scripts\python.exe" exit /b 0

echo.
echo ============================================
echo [*] venv introuvable — creation en cours...
echo ============================================
if exist "python\python.exe" (
    "python\python.exe" -m venv "venv"
    if exist "venv\Scripts\python.exe" (
        echo [OK] venv cree avec python\python.exe embarque.
        exit /b 0
    )
)

echo.
echo ============================================
echo [X] ERREUR : impossible de creer venv\Scripts\python.exe.
echo Cree-le manuellement avec :  python -m venv venv
echo ============================================
pause
exit /b 1

:INSTALL_AND_CHECK_DEPS
echo.
echo ============================================
echo Mise a jour de pip et installation des dependances
echo (venv\Scripts\python.exe -m pip install -r requirements.txt)
echo ============================================
if not exist "requirements.txt" (
    echo.
    echo [X] ERREUR : requirements.txt introuvable a la racine du projet.
    pause
    exit /b 1
)

venv\Scripts\python.exe -m pip install --upgrade pip >nul
venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
if errorlevel 1 (
    echo.
    echo [X] ERREUR : l'installation d'une ou plusieurs dependances a echoue.
    echo Regarde le message pip ci-dessus pour savoir laquelle.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Verification EN PROFONDEUR des dependances (import reel + attribut
echo attendu, pas juste "le module s'importe") + correction automatique
echo si un module est manquant ou remplace par le mauvais paquet
echo (ex : "websocket" installe a la place de "websocket-client").
echo ============================================
if not exist "check_deps.py" (
    echo.
    echo [X] ERREUR : check_deps.py introuvable a la racine du projet.
    echo Ce fichier est la source de verite partagee avec main.py — sans
    echo lui la verification des dependances retombe sur un simple "import"
    echo qui ne detecte pas les collisions de paquets type websocket.
    pause
    exit /b 1
)

venv\Scripts\python.exe check_deps.py --fix
if errorlevel 1 (
    echo.
    echo ============================================
    echo [X] Au moins une dependance manque ou ne fonctionne pas correctement,
    echo     meme apres tentative de correction automatique.
    echo La compilation risque de produire un EXE casse.
    echo ============================================
    pause
    exit /b 1
)

echo.
echo ============================================
echo Toutes les dependances sont installees et fonctionnelles.
echo ============================================
exit /b 0

:DO_LAUNCH_TEST_FOLDER
setlocal
set "TEST_DIR=%~dp0test"

if not exist "!TEST_DIR!" (
    echo.
    echo ============================================
    echo [X] ERREUR : dossier "test" introuvable a la racine du projet.
    echo Chemin attendu : !TEST_DIR!
    echo ============================================
    pause
    endlocal & exit /b 1
)

set "TEST_MISSING="
for %%F in (main.py script.js style.css index.html) do (
    if not exist "!TEST_DIR!\%%F" set "TEST_MISSING=!TEST_MISSING! %%F"
)
if not exist "!TEST_DIR!\assets" set "TEST_MISSING=!TEST_MISSING! assets\"

if defined TEST_MISSING (
    echo.
    echo ============================================
    echo [X] ERREUR : fichier(s^)/dossier(s^) manquant(s^) dans !TEST_DIR! :
    echo !TEST_MISSING!
    echo ============================================
    pause
    endlocal & exit /b 1
)

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

call :CHECK_VENV
if errorlevel 1 (endlocal & exit /b 1)
call :INSTALL_AND_CHECK_DEPS
if errorlevel 1 (endlocal & exit /b 1)

set "STELLIO_DATA_DIR=%~dp0stellio-data-test"
if not exist "!STELLIO_DATA_DIR!" mkdir "!STELLIO_DATA_DIR!"
if not exist "!STELLIO_DATA_DIR!\uploads" mkdir "!STELLIO_DATA_DIR!\uploads"

cls
echo ================================
echo   STELLIO  (dossier test^)
echo ================================
echo.
echo [*] Lancement depuis : !TEST_DIR!
echo [*] Donnees isolees dans : !STELLIO_DATA_DIR!
echo.

pushd "!TEST_DIR!"
"%~dp0venv\Scripts\python.exe" main.py
popd

echo.
echo [INFO] L'application s'est arretee.
pause
endlocal
exit /b 0

:DO_LAUNCH_TEST_DEBUG
set "REAL_DATA_DIR=%STELLIO_DATA_DIR%"
if not defined REAL_DATA_DIR set "REAL_DATA_DIR=%APPDATA%\Stellio"
if not exist "!REAL_DATA_DIR!" mkdir "!REAL_DATA_DIR!" 2>nul
echo. > "!REAL_DATA_DIR!\.debug_session_pending"
echo.
echo ============================================
echo [DEBUG] Mode debug active pour ce lancement de test.
echo Logs au maximum (niveau DEBUG), fichier stellio.log dans :
echo !REAL_DATA_DIR!
echo ============================================
call :DO_LAUNCH_TEST DEBUG
exit /b 0

:DO_LAUNCH_TEST
set "TEST_MODE_SUFFIX="
if /i "%~1"=="DEBUG" set "TEST_MODE_SUFFIX= (DEBUG)"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

call :CHECK_VENV
if errorlevel 1 exit /b 1
call :INSTALL_AND_CHECK_DEPS
if errorlevel 1 exit /b 1

set "DATA_DIR=%~dp0stellio-data"
if not exist "!DATA_DIR!" mkdir "!DATA_DIR!"
if not exist "!DATA_DIR!\uploads" mkdir "!DATA_DIR!\uploads"

if not exist "!SRC_DIR!\main.py" (
    echo.
    echo [X] ERREUR : !SRC_DIR!\main.py introuvable.
    pause
    exit /b 1
)

cls
echo ╔═══════════════╗
echo ║    STELLIO    ║
echo ╚═══════════════╝
echo.
echo [*] Lancement en mode test!TEST_MODE_SUFFIX! : !OUT_NAME!...
echo.

pushd "!SRC_DIR!"
"%~dp0venv\Scripts\python.exe" main.py
popd

echo.
echo [INFO] L'application s'est arretee.
pause
exit /b 0

echo.
echo ============================================
echo Fin inattendue du script — voir les messages ci-dessus.
echo ============================================
pause
exit /b 1