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
; Installation globale dans ProgramData
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

[Languages]
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
; Autorise tous les utilisateurs à modifier/écrire dans ce dossier pour permettre les patchs .zip
Name: "{app}"; Permissions: users-full

[Files]
Source: "{#SourcePath}dist\Stellio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{commonprograms}\{#MyAppName}";             Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{commonprograms}\Désinstaller {#MyAppName}"; Filename: "{uninstallexe}"
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
      'Installation existante détectée',
      'Une version de {#MyAppName} est déjà installée sur votre ordinateur.',
      'Version ' + GetInstalledVersion + ' détectée. Que souhaitez-vous faire ?',
      True, False);
    ChoicePage.Add('Réparer / Mettre à jour (écrase les fichiers existants)');
    ChoicePage.Add('Désinstaller la version actuelle puis réinstaller');
    ChoicePage.Add('Annuler');
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
        MsgBox('Erreur lors de la désinstallation (code ' + IntToStr(Code) + ').', mbError, MB_OK);
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
      WizardForm.StatusLabel.Caption := 'Téléchargement de Visual C++ Redistributable...';
      if DownloadFile('{#UrlVCRedist}', TmpVCRedist, 'VC++ Redist') then
      begin
        WizardForm.StatusLabel.Caption := 'Installation de Visual C++ Redistributable...';
        Exec(TmpVCRedist, '/install /quiet /norestart', '', SW_HIDE, ewWaitUntilTerminated, Code);
        Log('VC++ installé, code = ' + IntToStr(Code));
      end
      else
        MsgBox('Impossible de télécharger Visual C++ Redistributable.' + #13#10 +
               'Vérifiez votre connexion internet.', mbError, MB_OK);
    end;

    // ── 2. Microsoft Edge WebView2 ────────────────────────────────────────
    if not IsWebView2Installed then
    begin
      WizardForm.StatusLabel.Caption := 'Téléchargement de Microsoft Edge WebView2...';
      if DownloadFile('{#UrlWebView2}', TmpWebView2, 'WebView2') then
      begin
        WizardForm.StatusLabel.Caption := 'Installation de Microsoft Edge WebView2...';
        Exec(TmpWebView2, '/install /norestart', '', SW_HIDE, ewWaitUntilTerminated, Code);
        Log('WebView2 installé, code = ' + IntToStr(Code));
      end
      else
        MsgBox('Impossible de télécharger WebView2.' + #13#10 +
               'Stellio fonctionnera en mode navigateur par défaut.', mbInformation, MB_OK);
    end;
  end;

  if CurStep = ssPostInstall then
  begin
    SendMessageTimeout($FFFF, $001A, 0, 'Environment', $0002, 1000, Res);
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
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchApp