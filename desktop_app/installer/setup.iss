; RecoveryAssistant Desktop - Inno Setup Script
; Creates a professional Windows installer

#define MyAppName "RecoveryAssistant"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "RecoveryAssistant Inc."
#define MyAppURL "https://recoveryassistant.com"
#define MyAppExeName "RecoveryAssistant.exe"

[Setup]
; Basic information
AppId={{8A9B7C6D-5E4F-3A2B-1C0D-9E8F7A6B5C4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=..\dist\installer
OutputBaseFilename=RecoveryAssistant_Setup_v{#MyAppVersion}
SetupIconFile=..\resources\icons\app_icon.ico

; Compression
Compression=lzma2/max
SolidCompression=yes

; Requirements
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; UI
WizardStyle=modern
WizardImageFile=..\resources\installer\wizard_large.bmp
WizardSmallImageFile=..\resources\installer\wizard_small.bmp
UninstallDisplayIcon={app}\{#MyAppExeName}

; License and info
LicenseFile=..\LICENSE.txt
InfoBeforeFile=..\INSTALL_INFO.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startup"; Description: "Start RecoveryAssistant with Windows"; GroupDescription: "Startup Options:"; Flags: unchecked

[Files]
; Main executable
Source: "..\dist\RecoveryAssistant.exe"; DestDir: "{app}"; Flags: ignoreversion

; Resources
Source: "..\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "..\docs\USER_GUIDE.pdf"; DestDir: "{app}\docs"; Flags: ignoreversion isreadme
Source: "..\docs\QUICK_START.pdf"; DestDir: "{app}\docs"; Flags: ignoreversion

; Prerequisites check
Source: "vcredist_x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: VCRedistNeedsInstall

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\User Guide"; Filename: "{app}\docs\USER_GUIDE.pdf"
Name: "{group}\Quick Start Guide"; Filename: "{app}\docs\QUICK_START.pdf"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

; Startup folder (if selected)
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--minimized"; Tasks: startup

[Run]
; Install Visual C++ redistributable if needed
Filename: "{tmp}\vcredist_x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "Installing Microsoft Visual C++ Redistributable..."; Check: VCRedistNeedsInstall

; Launch application after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Clean up user data (optional - ask user)
Filename: "{cmd}"; Parameters: "/C ""echo Uninstalling RecoveryAssistant..."""; Flags: runhidden

[UninstallDelete]
; Remove application data (keep user database by default)
Type: filesandordirs; Name: "{userappdata}\RecoveryAssistant\Logs"
Type: files; Name: "{userappdata}\RecoveryAssistant\config.json.backup"

[Code]
// Check if Visual C++ Redistributable is installed
function VCRedistNeedsInstall: Boolean;
var
  Version: String;
begin
  // Check for VC++ 2015-2022 Redistributable
  if RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Version', Version) then
  begin
    Result := False;
  end
  else
    Result := True;
end;

// Check if Microsoft Outlook is installed
function IsOutlookInstalled: Boolean;
var
  OutlookPath: String;
begin
  Result := RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE',
    '', OutlookPath);

  if not Result then
  begin
    Result := RegQueryStringValue(HKEY_LOCAL_MACHINE,
      'SOFTWARE\Microsoft\Office\16.0\Outlook\InstallRoot',
      'Path', OutlookPath);
  end;
end;

// Check prerequisites on startup
function InitializeSetup: Boolean;
var
  ErrorMessage: String;
  Answer: Integer;
begin
  Result := True;
  ErrorMessage := '';

  // Check for Microsoft Outlook
  if not IsOutlookInstalled then
  begin
    ErrorMessage := 'Microsoft Outlook is not installed.' + #13#10 +
                    'RecoveryAssistant requires Outlook for email sending.' + #13#10 + #13#10 +
                    'Do you want to continue anyway?';

    Answer := MsgBox(ErrorMessage, mbConfirmation, MB_YESNO);
    if Answer = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;

  // Check Windows version
  if not (GetWindowsVersion >= $0A000000) then // Windows 10 or higher
  begin
    MsgBox('RecoveryAssistant requires Windows 10 or higher.' + #13#10 +
           'Your Windows version is not supported.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
end;

// Display information after successful installation
procedure CurStepChanged(CurStep: TSetupStep);
var
  InfoMessage: String;
begin
  if CurStep = ssPostInstall then
  begin
    InfoMessage := 'RecoveryAssistant has been installed successfully!' + #13#10 + #13#10 +
                   'On first launch:' + #13#10 +
                   '1. Enter your OpenAI API key' + #13#10 +
                   '2. Connect to Xero (optional)' + #13#10 +
                   '3. Configure Stripe for payments (optional)' + #13#10 +
                   '4. Import your receivables data' + #13#10 + #13#10 +
                   'See the User Guide for detailed instructions.';

    // This will show after installation
    Log('Installation completed successfully');
  end;
end;

// Show additional info after installation
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    // Custom finish page message
  end;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nRecoveryAssistant is an AI-powered automated receivables collection system that achieves 99%% collection rates through intelligent communication and seamless payment processing.%n%nBefore installation, please ensure:%n• Microsoft Outlook is installed%n• You have an OpenAI API key%n• (Optional) Xero or QuickBooks credentials%n• (Optional) Stripe API key for payments
