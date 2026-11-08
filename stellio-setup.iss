#define MyAppName      "Stellio-app"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppPublisher "Stellio"
#define MyAppURL       "https://stellio-app.com"
#define MyAppExeName   "Stellio.exe"

#define UrlVCRedist    "https://aka.ms/vs/17/release/vc_redist.x64.exe"
#define UrlWebView2    "https://go.microsoft.com/fwlink/p/?LinkId=2124703"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={commonappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir={#SourcePath}output
OutputBaseFilename=Stellio-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile={#SourcePath}assets\logo-nom-stellio.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
UsePreviousLanguage=no

[Languages]
; Langue détectée automatiquement d'après la langue d'affichage de Windows (ShowLanguageDialog=no).
; Si elle n'est pas prise en charge (ex. chinois : pas de fichier officiel), l'anglais (1re ligne) est utilisé.
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[CustomMessages]
english.LangCode=en
french.LangCode=fr
german.LangCode=de
spanish.LangCode=es
italian.LangCode=it
brazilianportuguese.LangCode=pt
japanese.LangCode=ja

english.ExistTitle=Existing installation detected
french.ExistTitle=Installation existante détectée
german.ExistTitle=Vorhandene Installation erkannt
spanish.ExistTitle=Instalación existente detectada
italian.ExistTitle=Installazione esistente rilevata
brazilianportuguese.ExistTitle=Instalação existente detectada
japanese.ExistTitle=既存のインストールが見つかりました

english.ExistDesc={#MyAppName} is already installed on your computer.
french.ExistDesc={#MyAppName} est déjà installé sur votre ordinateur.
german.ExistDesc={#MyAppName} ist bereits auf Ihrem Computer installiert.
spanish.ExistDesc={#MyAppName} ya está instalado en su equipo.
italian.ExistDesc={#MyAppName} è già installato sul computer.
brazilianportuguese.ExistDesc={#MyAppName} já está instalado no seu computador.
japanese.ExistDesc={#MyAppName} はすでにインストールされています。

english.ExistVersion=Version %1 detected. What would you like to do?
french.ExistVersion=Version %1 détectée. Que souhaitez-vous faire ?
german.ExistVersion=Version %1 erkannt. Was möchten Sie tun?
spanish.ExistVersion=Versión %1 detectada. ¿Qué desea hacer?
italian.ExistVersion=Versione %1 rilevata. Cosa desidera fare?
brazilianportuguese.ExistVersion=Versão %1 detectada. O que deseja fazer?
japanese.ExistVersion=バージョン %1 が見つかりました。どうしますか？

english.OptRepair=Repair / Update (overwrites existing files)
french.OptRepair=Réparer / Mettre à jour (écrase les fichiers existants)
german.OptRepair=Reparieren / Aktualisieren (überschreibt vorhandene Dateien)
spanish.OptRepair=Reparar / Actualizar (sobrescribe los archivos existentes)
italian.OptRepair=Ripara / Aggiorna (sovrascrive i file esistenti)
brazilianportuguese.OptRepair=Reparar / Atualizar (substitui os arquivos existentes)
japanese.OptRepair=修復 / 更新（既存のファイルを上書き）

english.OptUninstall=Uninstall the current version, then reinstall
french.OptUninstall=Désinstaller la version actuelle puis réinstaller
german.OptUninstall=Aktuelle Version deinstallieren und neu installieren
spanish.OptUninstall=Desinstalar la versión actual y volver a instalar
italian.OptUninstall=Disinstalla la versione attuale e reinstalla
brazilianportuguese.OptUninstall=Desinstalar a versão atual e reinstalar
japanese.OptUninstall=現在のバージョンをアンインストールして再インストール

english.OptCancel=Cancel
french.OptCancel=Annuler
german.OptCancel=Abbrechen
spanish.OptCancel=Cancelar
italian.OptCancel=Annulla
brazilianportuguese.OptCancel=Cancelar
japanese.OptCancel=キャンセル

english.UninstallError=Error during uninstallation (code %1).
french.UninstallError=Erreur lors de la désinstallation (code %1).
german.UninstallError=Fehler bei der Deinstallation (Code %1).
spanish.UninstallError=Error durante la desinstalación (código %1).
italian.UninstallError=Errore durante la disinstallazione (codice %1).
brazilianportuguese.UninstallError=Erro durante a desinstalação (código %1).
japanese.UninstallError=アンインストール中にエラーが発生しました（コード %1）。

english.DlVC=Downloading Visual C++ Redistributable...
french.DlVC=Téléchargement de Visual C++ Redistributable...
german.DlVC=Visual C++ Redistributable wird heruntergeladen...
spanish.DlVC=Descargando Visual C++ Redistributable...
italian.DlVC=Download di Visual C++ Redistributable...
brazilianportuguese.DlVC=Baixando o Visual C++ Redistributable...
japanese.DlVC=Visual C++ Redistributable をダウンロードしています...

english.InstVC=Installing Visual C++ Redistributable...
french.InstVC=Installation de Visual C++ Redistributable...
german.InstVC=Visual C++ Redistributable wird installiert...
spanish.InstVC=Instalando Visual C++ Redistributable...
italian.InstVC=Installazione di Visual C++ Redistributable...
brazilianportuguese.InstVC=Instalando o Visual C++ Redistributable...
japanese.InstVC=Visual C++ Redistributable をインストールしています...

english.FailVC=Unable to download Visual C++ Redistributable.%nCheck your internet connection.
french.FailVC=Impossible de télécharger Visual C++ Redistributable.%nVérifiez votre connexion internet.
german.FailVC=Visual C++ Redistributable konnte nicht heruntergeladen werden.%nÜberprüfen Sie Ihre Internetverbindung.
spanish.FailVC=No se pudo descargar Visual C++ Redistributable.%nCompruebe su conexión a Internet.
italian.FailVC=Impossibile scaricare Visual C++ Redistributable.%nControllare la connessione a Internet.
brazilianportuguese.FailVC=Não foi possível baixar o Visual C++ Redistributable.%nVerifique sua conexão com a Internet.
japanese.FailVC=Visual C++ Redistributable をダウンロードできませんでした。%nインターネット接続を確認してください。

english.DlWV2=Downloading Microsoft Edge WebView2...
french.DlWV2=Téléchargement de Microsoft Edge WebView2...
german.DlWV2=Microsoft Edge WebView2 wird heruntergeladen...
spanish.DlWV2=Descargando Microsoft Edge WebView2...
italian.DlWV2=Download di Microsoft Edge WebView2...
brazilianportuguese.DlWV2=Baixando o Microsoft Edge WebView2...
japanese.DlWV2=Microsoft Edge WebView2 をダウンロードしています...

english.InstWV2=Installing Microsoft Edge WebView2...
french.InstWV2=Installation de Microsoft Edge WebView2...
german.InstWV2=Microsoft Edge WebView2 wird installiert...
spanish.InstWV2=Instalando Microsoft Edge WebView2...
italian.InstWV2=Installazione di Microsoft Edge WebView2...
brazilianportuguese.InstWV2=Instalando o Microsoft Edge WebView2...
japanese.InstWV2=Microsoft Edge WebView2 をインストールしています...

english.FailWV2=Unable to download WebView2.%nStellio will run in default browser mode.
french.FailWV2=Impossible de télécharger WebView2.%nStellio fonctionnera en mode navigateur par défaut.
german.FailWV2=WebView2 konnte nicht heruntergeladen werden.%nStellio wird im Standardbrowser ausgeführt.
spanish.FailWV2=No se pudo descargar WebView2.%nStellio se ejecutará en el navegador predeterminado.
italian.FailWV2=Impossibile scaricare WebView2.%nStellio verrà eseguito nel browser predefinito.
brazilianportuguese.FailWV2=Não foi possível baixar o WebView2.%nO Stellio será executado no navegador padrão.
japanese.FailWV2=WebView2 をダウンロードできませんでした。%nStellio は既定のブラウザーで動作します。

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}"; Permissions: users-full

[Files]
Source: "{#SourcePath}dist\Stellio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{commonprograms}\{#MyAppName}";             Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{commonprograms}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}";              Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
var
  ChoicePage:     TInputOptionWizardPage;
  ExistingInstall: Boolean;
  UninstallString: String;

// ── Déclaration API Windows ────────────────────────────────────────────────
function SendMessageTimeout(hWnd, Msg, wParam: Integer; lParam: String;
  fuFlags, uTimeout: Integer; var lpdwResult: Integer): Boolean;
  external 'SendMessageTimeoutA@user32.dll stdcall';

// ── Détection VC++ Redistributable ──────────────────────────────────────────
function IsVCRedistInstalled: Boolean;
var
  Major, Minor: Cardinal;
begin
  Result := False;
  if RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64', 'Major', Major) then
    if RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64', 'Minor', Minor) then
      Result := (Major >= 14) and (Minor >= 40);
  if not Result then Log('VC++ 14.40+ non détecté — téléchargement requis.');
end;

// ── Détection WebView2 ───────────────────────────────────────────────────────
function IsWebView2Installed: Boolean;
begin
  Result :=
    RegKeyExists(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}') OR
    RegKeyExists(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}') OR
    RegKeyExists(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}');
  if Result then Log('WebView2 déjà installé.')
  else Log('WebView2 non détecté — téléchargement requis.');
end;

// ── Détection version installée ──────────────────────────────────────────────
function IsAlreadyInstalled: Boolean;
var
  Key, Str: String;
begin
  Key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}_is1';
  Result := RegQueryStringValue(HKLM, Key, 'UninstallString', Str) or
            RegQueryStringValue(HKCU, Key, 'UninstallString', Str);
  if Result then UninstallString := Str;
end;

function GetInstalledVersion: String;
var
  Key: String;
begin
  Key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}_is1';
  if not RegQueryStringValue(HKLM, Key, 'DisplayVersion', Result) then
    RegQueryStringValue(HKCU, Key, 'DisplayVersion', Result);
end;

// ── Téléchargement générique ─────────────────────────────────────────────────
function DownloadFile(Url, Dest, Description: String): Boolean;
var
  Res: Integer;
begin
  Log('Téléchargement : ' + Url + ' → ' + Dest);
  Result := True;
  if not FileExists(Dest) then
  begin
    Exec(
      ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -NonInteractive -Command ' +
        '"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ' +
        'Invoke-WebRequest -Uri ''' + Url + ''' -OutFile ''' + Dest + ''' -UseBasicParsing"',
      '', SW_HIDE, ewWaitUntilTerminated, Res
    );
    Result := FileExists(Dest);
    if Result then
      Log(Description + ' téléchargé avec succès.')
    else
      Log('ERREUR : échec du téléchargement de ' + Description + ' (code ' + IntToStr(Res) + ')');
  end
  else
    Log(Description + ' déjà présent dans {tmp}.');
end;

// ── Wizard ───────────────────────────────────────────────────────────────────
procedure InitializeWizard;
begin
  ExistingInstall := IsAlreadyInstalled;
  if ExistingInstall then
  begin
    ChoicePage := CreateInputOptionPage(wpWelcome,
      CustomMessage('ExistTitle'),
      CustomMessage('ExistDesc'),
      FmtMessage(CustomMessage('ExistVersion'), [GetInstalledVersion]),
      True, False);
    ChoicePage.Add(CustomMessage('OptRepair'));
    ChoicePage.Add(CustomMessage('OptUninstall'));
    ChoicePage.Add(CustomMessage('OptCancel'));
    ChoicePage.Values[0] := True;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Code: Integer;
  Cmd:  String;
begin
  Result := True;
  if ExistingInstall and (CurPageID = ChoicePage.ID) then
  begin
    if ChoicePage.Values[1] then
    begin
      Cmd := UninstallString;
      if Pos('"', Cmd) > 0 then
        Cmd := Copy(Cmd, 2, Length(Cmd) - 2);
      if Exec(Cmd, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, Code) then
        Sleep(2000)
      else
      begin
        MsgBox(FmtMessage(CustomMessage('UninstallError'), [IntToStr(Code)]), mbError, MB_OK);
        Result := False;
      end;
    end
    else if ChoicePage.Values[2] then
    begin
      WizardForm.Close;
      Result := False;
    end;
  end;
end;

// ── Étape principale : téléchargement + installation des dépendances ─────────
procedure CurStepChanged(CurStep: TSetupStep);
var
  TmpVCRedist, TmpWebView2: String;
  Code: Integer;
  Res:  Integer;
begin
  if CurStep = ssInstall then
  begin
    TmpVCRedist  := ExpandConstant('{tmp}\vc_redist.x64.exe');
    TmpWebView2  := ExpandConstant('{tmp}\MicrosoftEdgeWebView2RuntimeInstallerX64.exe');

    // ── 1. Visual C++ Redistributable ────────────────────────────────────
    if not IsVCRedistInstalled then
    begin
      WizardForm.StatusLabel.Caption := CustomMessage('DlVC');
      if DownloadFile('{#UrlVCRedist}', TmpVCRedist, 'VC++ Redist') then
      begin
        WizardForm.StatusLabel.Caption := CustomMessage('InstVC');
        Exec(TmpVCRedist, '/install /quiet /norestart', '', SW_HIDE, ewWaitUntilTerminated, Code);
        Log('VC++ installé, code = ' + IntToStr(Code));
      end
      else
        MsgBox(CustomMessage('FailVC'), mbError, MB_OK);
    end;

    // ── 2. Microsoft Edge WebView2 ────────────────────────────────────────
    if not IsWebView2Installed then
    begin
      WizardForm.StatusLabel.Caption := CustomMessage('DlWV2');
      if DownloadFile('{#UrlWebView2}', TmpWebView2, 'WebView2') then
      begin
        WizardForm.StatusLabel.Caption := CustomMessage('InstWV2');
        Exec(TmpWebView2, '/install /norestart', '', SW_HIDE, ewWaitUntilTerminated, Code);
        Log('WebView2 installé, code = ' + IntToStr(Code));
      end
      else
        MsgBox(CustomMessage('FailWV2'), mbInformation, MB_OK);
    end;
  end;

  if CurStep = ssPostInstall then
  begin
    SendMessageTimeout($FFFF, $001A, 0, 'Environment', $0002, 1000, Res);
    // Mémorise la langue de l'installateur : Stellio démarre dans la même langue (modifiable dans ses paramètres).
    SaveStringToFile(ExpandConstant('{app}\install-lang.txt'), CustomMessage('LangCode'), False);
  end;
end;

function ShouldLaunchApp: Boolean;
begin
  if WizardSilent then
    Result := (ExpandConstant('{param:LAUNCH|0}') = '1')
  else
    Result := True;
end;

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchApp