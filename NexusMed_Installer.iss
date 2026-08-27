; NexusMed_Installer.iss — Inno Setup 6 script for NexusMed 2077
; Build: ISCC.exe NexusMed_Installer.iss  →  Output\NexusMed_Setup_v5.3.1exe

#define MyAppName "NexusMed 2077"
#define MyAppNameFa "نکسوس ۲۰۷۷ — دستیار هوشمند پزشکی فارسی"
#define MyAppVersion "5.3.1"
#define MyAppPublisher "NexusMed 2077 Project"
#define MyAppExeName "NexusMed2077.exe"

[Setup]
AppId={{8F4B3C2A-2077-4E66-9011-NEXUSMED2077}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\NexusMed2077
DefaultGroupName=NexusMed 2077
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=NexusMed_Setup_v5.3.1
SetupIconFile=
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
LanguageDetectionMethod=none
UninstallDisplayName=NexusMed 2077
DisableProgramGroupPage=yes

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nPersian medical AI assistant (offline brain + optional online AI).%n%nNOTE: This software is NOT a replacement for a doctor. Emergency: IR 115 / EU 112.

[CustomMessages]
LaunchProgram=Launch NexusMed 2077

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
Name: "weblaunch"; Description: "Also create shortcut for &Web version (localhost:2077)"; GroupDescription: "Additional icons:"

[Files]
; باینری‌ها و داده‌های برنامه (ناموجود بودن txt پیام خطای کامل می‌دهد)
Source: "dist\NexusMed2077\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "clinic_2077.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "diseases_extra.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "diseases_offline.db"; DestDir: "{app}"; Flags: ignoreversion
Source: "medical_ml_test_dataset.csv"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
; فایل‌های شخصی کاربر (.env و *_profile.json و ...) هرگز داخل Setup قرار نمی‌گیرند

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall NexusMed 2077"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\NexusMed 2077 Web"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--web"; Tasks: weblaunch

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\__pycache__"
