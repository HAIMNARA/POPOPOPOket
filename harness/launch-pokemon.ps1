<#
.SYNOPSIS
  원클릭 포켓몬 레드 자동화 런처
  mGBA 실행 → Lua 소켓 서버 GUI 자동 로드 → mGBA-http 실행 → 체인 검증

.DESCRIPTION
  에이전트가 이 스크립트 하나만 실행하면 수동 개입 없이 전체 연결 체인이 구성된다.
  Lua 스크립트는 CLI(--script)가 아닌 GUI 자동화로 로드한다 (mGBA 0.10.x 호환).

  [금지 사항]
  - --script CLI 옵션 사용 금지 (mGBA 0.10.x에 존재하지 않음, 즉시 종료)
  - Lua 스크립트 2회 이상 로드 금지 (use-after-free 크래시)
  - dofile() 사용 금지 (관리되지 않는 콜백 생성)

.PARAMETER Rom
  포켓몬 레드 ROM 파일 경로. 기본값: C:\Users\하미\Downloads\Pokemon - Red Version.gb

.PARAMETER MgbaExe
  mGBA 실행 파일 경로. 기본값: C:\Program Files\mGBA\mGBA.exe

.PARAMETER LuaScript
  Lua 소켓 서버 스크립트 경로. 기본값: 자동 탐색

.PARAMETER MgbaHttpExe
  mGBA-http 실행 파일 경로. 기본값: 자동 탐색

.EXAMPLE
  pwsh .\launch-pokemon.ps1
  pwsh .\launch-pokemon.ps1 -Rom "D:\roms\Pokemon - Red Version.gb"
#>
param(
  [string]$Rom = "C:\Users\$env:USERNAME\Downloads\Pokemon - Red Version.gb",
  [string]$MgbaExe = "C:\Program Files\mGBA\mGBA.exe",
  [string]$LuaScript = "",
  [string]$MgbaHttpExe = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms,System.Drawing

# ============================================================
# 0. 경로 탐색
# ============================================================
if (-not $LuaScript) {
  $candidates = @(
    (Join-Path $env:USERPROFILE "pss-mgba\.local-tools\mgba-http\mGBASocketServer.lua"),
    (Join-Path $env:USERPROFILE "POPOPOPOket\harness\mgba-http\mGBASocketServer.lua")
  )
  foreach ($c in $candidates) { if (Test-Path -LiteralPath $c) { $LuaScript = $c; break } }
  if (-not $LuaScript) { Write-Error "Lua 소켓 서버 스크립트를 찾을 수 없습니다. -LuaScript 파라미터를 지정하세요."; exit 1 }
}
if (-not $MgbaHttpExe) {
  $candidates = @(
    (Join-Path $env:USERPROFILE "pss-mgba\.local-tools\mgba-http\mGBA-http.exe"),
    (Join-Path $env:USERPROFILE "POPOPOPOket\harness\mgba-http\mGBA-http.exe")
  )
  foreach ($c in $candidates) { if (Test-Path -LiteralPath $c) { $MgbaHttpExe = $c; break } }
  if (-not $MgbaHttpExe) { Write-Error "mGBA-http.exe를 찾을 수 없습니다. -MgbaHttpExe 파라미터를 지정하세요."; exit 1 }
}

Write-Host "=== Pokemon Red Automation Launcher ===" -ForegroundColor Cyan
Write-Host "ROM:        $Rom"
Write-Host "mGBA:       $MgbaExe"
Write-Host "Lua:        $LuaScript"
Write-Host "mGBA-http:  $MgbaHttpExe"
Write-Host ""

# 사전 검증
if (-not (Test-Path -LiteralPath $Rom))          { Write-Error "ROM 파일이 없습니다: $Rom"; exit 1 }
if (-not (Test-Path -LiteralPath $MgbaExe))      { Write-Error "mGBA.exe가 없습니다: $MgbaExe"; exit 1 }
if (-not (Test-Path -LiteralPath $LuaScript))    { Write-Error "Lua 스크립트가 없습니다: $LuaScript"; exit 1 }
if (-not (Test-Path -LiteralPath $MgbaHttpExe))  { Write-Error "mGBA-http.exe가 없습니다: $MgbaHttpExe"; exit 1 }

# ============================================================
# 1. 기존 프로세스 정리
# ============================================================
Write-Host "[1/6] 기존 프로세스 정리..." -ForegroundColor Yellow
Stop-Process -Name "mGBA-http" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "mGBA" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# ============================================================
# 2. mGBA 실행
# ============================================================
Write-Host "[2/6] mGBA 실행 (ROM 로드)..." -ForegroundColor Yellow
Start-Process -FilePath $MgbaExe -ArgumentList "`"$Rom`""
Start-Sleep -Seconds 3

$mgba = Get-Process -Name "mGBA" -ErrorAction SilentlyContinue
if (-not $mgba) { Write-Error "mGBA가 실행되지 않았습니다."; exit 1 }
Write-Host "  OK: mGBA PID=$($mgba.Id), Title=$($mgba.MainWindowTitle)" -ForegroundColor Green

# ============================================================
# 3. Lua 소켓 서버 GUI 자동 로드 (dofile 사용하지 않음!)
# ============================================================
Write-Host "[3/6] Lua 소켓 서버 GUI 로드 (File->Load script)..." -ForegroundColor Yellow

# Lua 파일을 ASCII 경로로 복사 (한글 경로 파일 다이얼로그 문제 방지)
$asciiLua = "C:\Users\Public\mgba-socket.lua"
Copy-Item -LiteralPath $LuaScript -Destination $asciiLua -Force
Set-Clipboard -Value $asciiLua

# P/Invoke 정의
$sig = @"
using System;using System.Runtime.InteropServices;using System.Text;
public class LP {
  public delegate bool E(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(E cb, IntPtr p);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
  [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool c);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, IntPtr extra);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,IntPtr e);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
  public static IntPtr FindMainW(uint pid){ IntPtr f=IntPtr.Zero; EnumWindows((h,p)=>{ if(!IsWindowVisible(h))return true; uint wp; GetWindowThreadProcessId(h,out wp); if(wp!=pid)return true; var sb=new StringBuilder(256); GetWindowText(h,sb,256); if(sb.ToString().IndexOf("POKEMON",StringComparison.OrdinalIgnoreCase)>=0){f=h;return false;} return true; },IntPtr.Zero); return f; }
  public static IntPtr FindScriptW(uint pid){ IntPtr f=IntPtr.Zero; EnumWindows((h,p)=>{ if(!IsWindowVisible(h))return true; uint wp; GetWindowThreadProcessId(h,out wp); if(wp!=pid)return true; var sb=new StringBuilder(256); GetWindowText(h,sb,256); var t=sb.ToString(); if(t.Length>0 && t.IndexOf("POKEMON",StringComparison.OrdinalIgnoreCase)<0){f=h;return false;} return true; },IntPtr.Zero); return f; }
  public static void Foc(IntPtr h){ IntPtr fg=GetForegroundWindow(); uint cur=GetCurrentThreadId(); uint d; uint tgt=GetWindowThreadProcessId(fg, out d); ShowWindow(h,9); AttachThreadInput(tgt,cur,true); BringWindowToTop(h); SetForegroundWindow(h); AttachThreadInput(tgt,cur,false); }
  public static void Tap(byte vk){ keybd_event(vk,0,0,IntPtr.Zero); System.Threading.Thread.Sleep(60); keybd_event(vk,0,2,IntPtr.Zero); }
  public static void CtrlV(){ keybd_event(0x11,0,0,IntPtr.Zero); keybd_event(0x56,0,0,IntPtr.Zero); System.Threading.Thread.Sleep(50); keybd_event(0x56,0,2,IntPtr.Zero); keybd_event(0x11,0,2,IntPtr.Zero); }
  public static void ClickAt(int x,int y){ SetCursorPos(x,y); System.Threading.Thread.Sleep(120); mouse_event(0x0002,0,0,0,IntPtr.Zero); mouse_event(0x0004,0,0,0,IntPtr.Zero); }
}
"@
Add-Type $sig

$pidm = $mgba.Id
$main = [LP]::FindMainW([uint32]$pidm)

# 스크립팅 창 열기: Alt → Right*3 → Down*5 → Enter (Tools → Scripting)
[LP]::Foc($main); Start-Sleep -Milliseconds 500
foreach ($k in @(0x12,0x27,0x27,0x27,0x28,0x28,0x28,0x28,0x28,0x0D)) {
  [LP]::Tap([byte]$k); Start-Sleep -Milliseconds 300
}
Start-Sleep -Milliseconds 1500

$sw = [LP]::FindScriptW([uint32]$pidm)
if ($sw -eq [IntPtr]::Zero) { Write-Error "스크립팅 창이 열리지 않았습니다."; exit 1 }

# 메인 창 최소화 (키 입력 누수 방지)
[LP]::ShowWindow($main, 6) | Out-Null
Start-Sleep -Milliseconds 500

# 스크립팅 창 포커스 + File 메뉴 → Load script → 파일 다이얼로그
[LP]::Foc($sw); Start-Sleep -Milliseconds 300
$r = New-Object LP+RECT; [LP]::GetWindowRect($sw,[ref]$r) | Out-Null
[LP]::ClickAt([int](($r.Left+$r.Right)/2), $r.Top+12); Start-Sleep -Milliseconds 300

[LP]::Tap(0x12); Start-Sleep -Milliseconds 400  # Alt (File 메뉴)
[LP]::Tap(0x28); Start-Sleep -Milliseconds 400  # Down (첫 항목 = Load script)
[LP]::Tap(0x0D); Start-Sleep -Milliseconds 1600 # Enter (파일 다이얼로그 열림)

# 파일 다이얼로그에 경로 붙여넣기 + Enter
[LP]::CtrlV(); Start-Sleep -Milliseconds 500
[LP]::Tap(0x0D); Start-Sleep -Milliseconds 2800

# 메인 창 복원
[LP]::ShowWindow($main, 9) | Out-Null
Start-Sleep -Milliseconds 500

# 포트 8888 확인
$c = New-Object System.Net.Sockets.TcpClient; $bound = $false
try {
  $iar = $c.BeginConnect("127.0.0.1", 8888, $null, $null)
  if ($iar.AsyncWaitHandle.WaitOne(2000) -and $c.Connected) { $bound = $true }
} catch {} finally { $c.Close() }

if ($bound) {
  Write-Host "  OK: Lua 소켓 서버 로드 완료 (포트 8888 리슨)" -ForegroundColor Green
} else {
  Write-Error "Lua 소켓 서버가 바인딩되지 않았습니다. mGBA GUI에서 수동으로 로드해 주세요."
  Write-Host "  경로: $LuaScript" -ForegroundColor Red
  Write-Host "  방법: Tools -> Scripting -> File -> Load script" -ForegroundColor Red
  exit 1
}

# ============================================================
# 4. mGBA-http 실행
# ============================================================
Write-Host "[4/6] mGBA-http 실행..." -ForegroundColor Yellow
$httpDir = Split-Path -Parent $MgbaHttpExe
Start-Process -FilePath $MgbaHttpExe -WorkingDirectory $httpDir
Start-Sleep -Seconds 2

# ============================================================
# 5. 전체 체인 검증
# ============================================================
Write-Host "[5/6] 전체 연결 체인 검증..." -ForegroundColor Yellow
$maxWait = 30
$ok = $false
for ($i = 0; $i -lt $maxWait; $i++) {
  try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:5000/core/getgametitle" -UseBasicParsing -TimeoutSec 3
    if ($resp.StatusCode -eq 200 -and $resp.Content -match "POKEMON RED") {
      $ok = $true; break
    }
  } catch {}
  Start-Sleep -Seconds 1
}

if ($ok) {
  Write-Host "  OK: 전체 체인 정상 — POKEMON RED 확인" -ForegroundColor Green
} else {
  Write-Error "체인 검증 실패. http://127.0.0.1:5000/core/getgametitle 가 응답하지 않습니다."
  exit 1
}

# ============================================================
# 6. 완료
# ============================================================
Write-Host ""
Write-Host "[6/6] 준비 완료!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  mGBA:        PID $($mgba.Id) (POKEMON RED)" -ForegroundColor White
Write-Host "  Lua 소켓:    :8888 리슨 중" -ForegroundColor White
Write-Host "  mGBA-http:   :5000 응답 중" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "이제 하네스를 실행하세요:" -ForegroundColor Yellow
Write-Host "  cd pss-mgba && pnpm dev" -ForegroundColor White
Write-Host ""
Write-Host "[주의] 절대 하지 말 것:" -ForegroundColor Red
Write-Host "  - mGBA --script ... (존재하지 않는 옵션, 즉시 종료)" -ForegroundColor Red
Write-Host "  - Lua 스크립트 2회 로드 (크래시)" -ForegroundColor Red
Write-Host "  - dofile()로 Lua 로드 (크래시)" -ForegroundColor Red
