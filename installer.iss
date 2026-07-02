; installer.iss
; Inno Setup インストーラ定義（08_デスクトップアプリ化要件定義書.md 12節）
;
; APP_VERSION はCIから環境変数として渡される想定（.github/workflows/release.yml参照）。
; ローカルでビルドする場合は ISCC.exe /DAPP_VERSION=0.0.1 installer.iss のように指定する。

#ifndef APP_VERSION
  #define APP_VERSION "0.0.0-dev"
#endif

#define AppName "Document Sites Crawler for RAG"
#define AppPublisher "fumotto"
#define AppExeName "DocumentSitesCrawlerForRAG.exe"
#define AppURL "https://github.com/fumotto/NotebookLM-Document-Crawler"

[Setup]
AppId={{B7B9E1C4-6B9E-4C4F-9C9E-0A0B7B9E1C40}}
AppName={#AppName}
AppVersion={#APP_VERSION}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; 12節: 管理者権限不要のユーザーインストール（8.3節と一貫させる）
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\DocumentSitesCrawlerForRAG
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

OutputDir=Output
OutputBaseFilename=DocumentSitesCrawlerForRAGSetup
SetupIconFile=web\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}

; 8.4節: アンインストール時にユーザーデータ（%USERPROFILE%配下）は削除対象に含めない。
; インストールディレクトリ配下のファイルのみが自動的にアンインストール対象となる。

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PyInstaller --onedir の出力（dist\DocumentSitesCrawlerForRAG\ 配下一式）をまるごと同梱する。
Source: "dist\DocumentSitesCrawlerForRAG\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
