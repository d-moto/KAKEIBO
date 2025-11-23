[Setup]
AppName=KAKEIBO
AppVersion=1.0
DefaultDirName={autopf}\KAKEIBO
DefaultGroupName=KAKEIBO
UninstallDisplayIcon={app}\Kakeibo.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=KakeiboSetup

[Files]
Source: "dist\Kakeibo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\KAKEIBO"; Filename: "{app}\Kakeibo.exe"
Name: "{commondesktop}\KAKEIBO"; Filename: "{app}\Kakeibo.exe"

[Run]
Filename: "{app}\Kakeibo.exe"; Description: "Launch KAKEIBO"; Flags: nowait postinstall skipifsilent
