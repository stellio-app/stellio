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
if not exist "build" mkdir "build"

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
echo  [3] Verifier / installer les dependances
echo  [4] Compiler l'EXE uniquement 
echo  [5] Compiler l'installeur (.exe, via InnoSetup)
echo  [6] Creer le ZIP de patch uniquement
echo  [7] Build complet (dependances + EXE + patch ZIP) [InnoSetup manuel]
echo  [8] Quitter
echo.
set /p "ACTION=Votre choix (1 a 8) : "
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
    call :CHECK_VENV
    call :INSTALL_AND_CHECK_DEPS
    pause
    goto :ACTION_MENU
)
if "%ACTION%"=="4" (
    call :CHECK_VENV
    call :DO_BUILD_EXE
    pause
    goto :ACTION_MENU
)
if "%ACTION%"=="5" (
    call :DO_BUILD_INSTALLER
    pause
    goto :ACTION_MENU
)
if "%ACTION%"=="6" (
    call :DO_BUILD_ZIP
    pause
    goto :ACTION_MENU
)
if "%ACTION%"=="7" (
    call :CHECK_VENV
    call :INSTALL_AND_CHECK_DEPS
    call :DO_BUILD_EXE
    if not exist "dist\!OUT_NAME!\app\main.py" (
        echo.
        echo [X] L'EXE n'a pas ete construit correctement.
        pause
        goto :ACTION_MENU
    )

    call :DO_BUILD_ZIP
    if errorlevel 1 (
        echo.
        echo [X] La creation du ZIP a echoue — voir les messages ci-dessus.
        pause
        goto :ACTION_MENU
    )
    echo.
    echo ============================================
    echo Build EXE + ZIP termine avec succes !
    echo Vous pouvez maintenant compiler l'installeur manuellement avec InnoSetup.
    echo  - EXE       : dist\!OUT_NAME!\!OUT_NAME!.exe
    echo  - Patch ZIP : release\!OUT_NAME!-v!VERSION!-patch.zip
    echo ============================================
    pause
    goto :ACTION_MENU
)
if "%ACTION%"=="8" (
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


:DO_BUILD_EXE

call :CHECK_VENV
if errorlevel 1 exit /b 1
call :INSTALL_AND_CHECK_DEPS
if errorlevel 1 exit /b 1

set "MISSING_SRC=0"
for %%F in (
    "!SRC_DIR!\main.py"
    "!SRC_DIR!\index.html"
    "!SRC_DIR!\script.js"
    "!SRC_DIR!\style.css"
    "check_deps.py"
    "launcher.py"
) do (
    if not exist "%%~F" (
        echo [X] MANQUANT a la racine du projet : %%~F
        set "MISSING_SRC=1"
    )
)
if "!MISSING_SRC!"=="1" (
    echo.
    echo ============================================
    echo [X] Build annule — place les fichiers manquants ci-dessus dans
    echo     !CD! puis relance.
    echo ============================================
    exit /b 1
)

echo ============================================
echo Verification finale du venv (sans correction) avant compilation...
echo ============================================
venv\Scripts\python.exe check_deps.py
if errorlevel 1 (
    echo.
    echo ============================================
    echo [X] Le venv n'est plus dans un etat valide juste avant la
    echo     compilation ^(il l'etait pourtant juste avant^). Build annule.
    echo     Relance l'option [2] pour corriger, puis reessaie.
    echo ============================================
    pause
    exit /b 1
)

echo ============================================
echo Nettoyage des fichiers de build precedents...
echo ============================================
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del "!OUT_NAME!.spec" 2>nul

echo ============================================
echo Lancement de la compilation PyInstaller : !OUT_NAME!
echo (build tout-en-un : launcher.py + TOUTES les dependances de Stellio
echo  sont desormais embarquees directement dans l'EXE — il n'y a plus
echo  de runtime Python separe a telecharger/extraire chez le client.
echo  main.py restent copies en clair a cote, pour rester
echo  patchables par le systeme de mise a jour, mais tournent dans CET
echo  interpreteur embarque.)
echo ============================================

venv\Scripts\python.exe -m PyInstaller ^
    --name "!OUT_NAME!" ^
    --onedir ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --hidden-import sqlite3 ^
    --hidden-import ssl ^
    --hidden-import hashlib ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --collect-all tkinter ^
    --collect-all webview ^
    --collect-all trimesh ^
    --collect-all pyrender ^
    --collect-all imageio ^
    --collect-all OpenGL ^
    --collect-all numpy ^
    --collect-all PIL ^
    --collect-all matplotlib ^
    --collect-all mpl_toolkits ^
    --collect-all fast_simplification ^
    --collect-all pymeshfix ^
    --collect-all shapely ^
    --collect-all rectpack ^
    --collect-all smbprotocol ^
    --collect-all smbclient ^
    --collect-all paho ^
    --collect-all cryptography ^
    --collect-all rarfile ^
    --collect-all py7zr ^
    --collect-all defusedxml ^
    --collect-all qrcode ^
    --collect-all websocket ^
    --collect-all flashforge ^
    --collect-all waitress ^
    --collect-all flask ^
    --collect-all werkzeug ^
    --copy-metadata imageio ^
    --copy-metadata pyrender ^
    --copy-metadata trimesh ^
    --copy-metadata Pillow ^
    --copy-metadata PyOpenGL ^
    --copy-metadata numpy ^
    --icon="assets\logo-nom-stellio.ico" "launcher.py"

if not exist "dist\!OUT_NAME!\!OUT_NAME!.exe" (
    echo.
    echo ============================================
    echo ERREUR : la compilation a echoue, dist\!OUT_NAME!\!OUT_NAME!.exe introuvable.
    echo ============================================
    exit /b 1
)

echo ============================================
echo Copie de main.py / index.html / script.js / style.css /
echo assets / languages / bin dans dist\!OUT_NAME!\app\
echo (ces fichiers restent LIBRES, jamais compiles)
echo ============================================
mkdir "dist\!OUT_NAME!\app" 2>nul
copy /y "!SRC_DIR!\main.py"    "dist\!OUT_NAME!\app\main.py"    >nul
copy /y "check_deps.py"        "dist\!OUT_NAME!\app\check_deps.py" >nul
copy /y "!SRC_DIR!\index.html" "dist\!OUT_NAME!\app\index.html" >nul
copy /y "!SRC_DIR!\script.js"  "dist\!OUT_NAME!\app\script.js"  >nul
copy /y "!SRC_DIR!\style.css"  "dist\!OUT_NAME!\app\style.css"  >nul
xcopy /s /e /y /i "assets"    "dist\!OUT_NAME!\app\assets"    >nul
xcopy /s /e /y /i "languages" "dist\!OUT_NAME!\app\languages" >nul
if exist "bin" xcopy /s /e /y /i "bin" "dist\!OUT_NAME!\app\bin" >nul

set "COPY_FAILED=0"
for %%F in (main.py check_deps.py index.html script.js style.css) do (
    if not exist "dist\!OUT_NAME!\app\%%F" (
        echo [X] ECHEC DE COPIE : dist\!OUT_NAME!\app\%%F
        set "COPY_FAILED=1"
    )
)
if "!COPY_FAILED!"=="1" (
    echo.
    echo ============================================
    echo ERREUR : au moins un fichier requis n'a pas ete copie dans
    echo dist\!OUT_NAME!\app\ — voir le detail ci-dessus.
    echo ============================================
    exit /b 1
)

echo.
echo ============================================
echo Verification finale : demarrage headless de !OUT_NAME!.exe...
echo (controle que tous les modules requis sont bien presents et que le backend demarre)
echo ============================================

set "VERIFY_DATA_DIR=%CD%\build\verify-data-!OUT_NAME!"
rmdir /s /q "!VERIFY_DATA_DIR!" 2>nul
mkdir "!VERIFY_DATA_DIR!" 2>nul

set "VERIFY_LOG=!VERIFY_DATA_DIR!\stellio.log"
set "STELLIO_HEADLESS=1"
set "STELLIO_DATA_DIR=!VERIFY_DATA_DIR!"
set "STELLIO_PORT=58234"
set "STELLIO_SERVER_URL=http://127.0.0.1:58234"

echo. > "!VERIFY_DATA_DIR!\.debug_session_pending"

start "" /D "dist\!OUT_NAME!" "dist\!OUT_NAME!\!OUT_NAME!.exe"

echo Attente du demarrage (jusqu'a 60s)...
set "READY=0"
set "VERIFY_TRIES=0"

:VERIFY_WAIT_LOOP
set /a VERIFY_TRIES+=1
timeout /t 1 /nobreak >nul
if exist "!VERIFY_LOG!" (
    powershell -Command "if (Test-Path '!VERIFY_LOG!') { if (Select-String -Path '!VERIFY_LOG!' -Pattern 'Stellio est pr.t' -Quiet) { exit 0 } else { exit 1 } } else { exit 1 }" >nul 2>&1
    if !errorlevel! EQU 0 set "READY=1"
)
if "!READY!"=="1" goto :VERIFY_WAIT_DONE
if !VERIFY_TRIES! LSS 60 goto :VERIFY_WAIT_LOOP

:VERIFY_WAIT_DONE
timeout /t 1 /nobreak >nul
taskkill /F /IM "!OUT_NAME!.exe" /T >nul 2>&1

set "STELLIO_HEADLESS="
set "STELLIO_DATA_DIR="
set "STELLIO_PORT="
set "STELLIO_SERVER_URL="

set "HAS_MISSING=0"

if not exist "!VERIFY_LOG!" (
    echo [X] Aucun log genere — l'exe n'a probablement pas demarre du tout.
    set "HAS_MISSING=1"
) else (
    if "!READY!"=="0" (
        echo [X] Le backend n'a pas signale etre pret dans le delai imparti.
        set "HAS_MISSING=1"
    )

    findstr /c:"Tous les modules requis sont" "!VERIFY_LOG!" >nul 2>&1
    if errorlevel 1 set "HAS_MISSING=1"

    echo.
    echo ─────────── Rapport des modules ^(extrait du log^) ───────────
    findstr /c:"[MODULES]" "!VERIFY_LOG!"
    echo ───────────────────────────────────────────────────────────

    if "!HAS_MISSING!"=="1" (
        echo.
        echo ─────────── Log complet ^(pour diagnostic^) ───────────
        type "!VERIFY_LOG!"
        echo ───────────────────────────────────────────────────────────
    )
)

echo.
if "!HAS_MISSING!"=="1" (
    echo ============================================
    echo [X] VERIFICATION ECHOUEE — l'installeur risque de ne pas fonctionner chez le client.
    echo     Log complet : !VERIFY_LOG!
    echo ============================================
) else (
    echo ============================================
    echo [OK] Verification reussie : demarrage headless OK, tous les modules requis sont presents.
    echo ============================================
)

echo.
echo ============================================
echo Compilation terminee.
echo Executable  : dist\!OUT_NAME!\!OUT_NAME!.exe
echo Code source : dist\!OUT_NAME!\app\  (patchable par ZIP)
echo ============================================
exit /b 0

:DO_BUILD_INSTALLER

if not exist "dist\!OUT_NAME!\!OUT_NAME!.exe" (
    echo.
    echo [X] dist\!OUT_NAME!\!OUT_NAME!.exe introuvable — lance d'abord
    echo     l'option [3] (Compiler l'EXE) ou [6] (build complet).
    exit /b 1
)

echo.
echo ============================================
echo Recherche du compilateur InnoSetup (ISCC.exe)...
echo ============================================
set "ISCC_EXE="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE for %%I in (ISCC.exe) do if not "%%~$PATH:I"=="" set "ISCC_EXE=%%~$PATH:I"

if not defined ISCC_EXE (
    echo.
    echo [X] ISCC.exe introuvable. Installe Inno Setup 6
    echo     ^(https://jrsoftware.org/isinfo.php^) ou ajoute ISCC.exe au PATH.
    exit /b 1
)
echo Trouve : !ISCC_EXE!

set "ISS_FILE="
for %%F in (*.iss) do if not defined ISS_FILE set "ISS_FILE=%%F"
if not defined ISS_FILE (
    echo.
    echo [X] Aucun fichier .iss trouve a la racine du projet.
    exit /b 1
)
echo Script : !ISS_FILE!

echo.
echo ============================================
echo Compilation de l'installeur — version !VERSION!
echo ^(la version est passee depuis main.py via /DMyAppVersion,
echo  pas besoin de modifier !ISS_FILE! a chaque release^)
echo ============================================
echo.
"!ISCC_EXE!" "/DMyAppVersion=!VERSION!" "!ISS_FILE!"
if errorlevel 1 (
    echo.
    echo [X] La compilation InnoSetup a echoue — voir le detail ci-dessus.
    exit /b 1
)

echo.
echo ============================================
echo [OK] Installeur genere : Stellio-Setup-!VERSION!.exe
echo      ^(dans le dossier OutputDir defini dans !ISS_FILE!^)
echo ============================================
exit /b 0

:DO_BUILD_ZIP

echo.
echo ============================================
echo Preparation du contenu du patch : !OUT_NAME!
echo ============================================

set "PATCH_STAGING=build\patch-staging-!OUT_NAME!"
rmdir /s /q "!PATCH_STAGING!" 2>nul
mkdir "!PATCH_STAGING!" 2>nul

if not exist "!SRC_DIR!\main.py" (
    echo.
    echo [X] ERREUR : !SRC_DIR!\main.py introuvable.
    exit /b 1
)
if not exist "check_deps.py" (
    echo.
    echo [X] ERREUR : check_deps.py introuvable a la racine du projet.
    exit /b 1
)
if not exist "!SRC_DIR!\index.html" (
    echo.
    echo [X] ERREUR : !SRC_DIR!\index.html introuvable.
    exit /b 1
)
if not exist "!SRC_DIR!\script.js" (
    echo.
    echo [X] ERREUR : !SRC_DIR!\script.js introuvable.
    exit /b 1
)
if not exist "!SRC_DIR!\style.css" (
    echo.
    echo [X] ERREUR : !SRC_DIR!\style.css introuvable.
    exit /b 1
)
if not exist "assets" (
    echo.
    echo [X] ERREUR : dossier assets introuvable a la racine du projet.
    exit /b 1
)
if not exist "languages" (
    echo.
    echo [X] ERREUR : dossier languages introuvable a la racine du projet.
    exit /b 1
)

copy /y "!SRC_DIR!\main.py"    "!PATCH_STAGING!\main.py"    >nul
copy /y "check_deps.py"        "!PATCH_STAGING!\check_deps.py" >nul
copy /y "!SRC_DIR!\index.html" "!PATCH_STAGING!\index.html" >nul
copy /y "!SRC_DIR!\script.js"  "!PATCH_STAGING!\script.js"  >nul
copy /y "!SRC_DIR!\style.css"  "!PATCH_STAGING!\style.css"  >nul
xcopy /s /e /y /i "assets"    "!PATCH_STAGING!\assets"    >nul
if errorlevel 1 (
    echo.
    echo [X] ERREUR : la copie du dossier assets a echoue.
    exit /b 1
)
xcopy /s /e /y /i "languages" "!PATCH_STAGING!\languages" >nul
if errorlevel 1 (
    echo.
    echo [X] ERREUR : la copie du dossier languages a echoue.
    exit /b 1
)
if exist "bin" xcopy /s /e /y /i "bin" "!PATCH_STAGING!\bin" >nul

if not exist "!PATCH_STAGING!\main.py" (
    echo.
    echo ============================================
    echo ERREUR : la copie de main.py a echoue — verifie !SRC_DIR!\main.py
    echo ============================================
    exit /b 1
)

if not exist "release" mkdir "release"

set "ZIP_PATH=release\!OUT_NAME!-v!VERSION!-patch.zip"
del /f /q "!ZIP_PATH!" 2>nul

echo Compression vers !ZIP_PATH! ...
powershell -NoProfile -Command "Compress-Archive -Path '!PATCH_STAGING!\*' -DestinationPath '!ZIP_PATH!' -Force"

if not exist "!ZIP_PATH!" (
    echo.
    echo ============================================
    echo ERREUR : la creation du ZIP a echoue.
    echo ============================================
    exit /b 1
)

echo.
echo ============================================
echo ZIP de mise a jour cree : !ZIP_PATH!
echo ============================================
exit /b 0

echo.
echo ============================================
echo Fin inattendue du script — voir les messages ci-dessus.
echo ============================================
pause
exit /b 1