# 06 · 수동 플레이 툴킷 (`.omo` PowerShell 드라이버)

라이브 하네스 없이 **사람이 직접 키를 보내고 스크린샷을 찍어** 진행/막힘을 검증하던
PowerShell 드라이버 모음. 화면 보정·공략 루트 확인·디버깅에 썼다.

> 플랫폼: Windows / PowerShell. mGBA 창에 포커스를 강제로 가져온 뒤 키를 주입한다.

---

## 1. `play.ps1` — 키 입력 + 스크린샷 (핵심 드라이버)

mGBA 창에 키 시퀀스를 보내고, 끝나면 전체 화면 스크린샷을 저장한다.

### 파라미터

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `-Keys` | `""` | 콤마 구분 키 시퀀스. `u,d,l,r,a,b,s,e`. 홀드는 `키:ms` (예: `d:400`) |
| `-DefaultHoldMs` | `90` | 탭 기본 누름 시간(ms) |
| `-GapMs` | `140` | 키 사이 간격(ms) |
| `-PreWaitMs` | `250` | 입력 전 대기 |
| `-PostWaitMs` | `500` | 스크린샷 전 대기 |
| `-Out` | `...\Temp\opencode\play.png` | 스크린샷 저장 경로 |

### 키 토큰

| 토큰 | 게임 버튼 | VK |
|---|---|---|
| `u` / `d` / `l` / `r` | ↑ / ↓ / ← / → | `0x26`/`0x28`/`0x25`/`0x27` |
| `a` | A (`X`) | `0x58` |
| `b` | B (`Z`) | `0x5A` |
| `s` | Start (`Enter`) | `0x0D` |
| `e` | Select (`Backspace`) | `0x08` |

### 사용 예

```powershell
# 오른쪽 2번 + A 누르고 스크린샷
pwsh .omo/play.ps1 -Keys "r,r,a" -Out C:\tmp\step.png

# 아래로 길게(400ms) 홀드해서 한 칸 더 이동
pwsh .omo/play.ps1 -Keys "d:400"

# 대사 빠르게 넘기기 (A 연타)
pwsh .omo/play.ps1 -Keys "a,a,a,a" -GapMs 90
```

### 동작 원리

- `Get-Process mGBA` 로 창 핸들 확보. 없으면 `ERROR: mGBA not running`.
- `FocusMGBA()`: `AttachThreadInput` + `BringWindowToTop` + `SetForegroundWindow` + `SetWindowPos`
  (TOPMOST 토글)로 포커스를 확실히 가져온다.
- `keybd_event` 로 keydown → `hold` ms 대기 → keyup. 키마다 `FocusMGBA` 재호출로 포커스 유지.
- 끝나면 `VirtualScreen` 을 캡처해 PNG 저장. 출력: `OK keys='...' -> <png> (title: <창 제목>)`.

> 창 제목에 `POKEMON RED - 0.10.5` 가 보이면 ROM 로드 정상.

---

## 2. 그 외 `.omo` 보조 스크립트

수동 셋업/디버깅 과정에서 만든 헬퍼들(역할 요약):

| 스크립트 | 역할 |
|---|---|
| `focusscript.ps1` | mGBA 창 포커스 강제 확보 로직 (play.ps1의 FocusMGBA와 동일 계열) |
| `click.ps1` | 화면 좌표 클릭 (GUI 다이얼로그 조작용) |
| `menukey.ps1` | 메뉴 단축키 전송 |
| `findscript.ps1` | Scripting 창/파일 다이얼로그 탐색 |
| `loadgui.ps1`, `loadlua.ps1`, `loadlua2.ps1`, `loadlua3.ps1` | Lua 스크립트 GUI 로드 자동화 시도 (멀티윈도우·한글 경로 다이얼로그라 신뢰성 낮아 결국 수동 1회 로드로 정리) |
| `oneshot.ps1`, `oneshot2.ps1` | 셋업~키입력 원샷 실행 시도 |
| `manual-play-archive.md` | 수동 진행/막힘 로그 양식 → [03](03-strategy-guide.md) |
| `ulw-notepad.md` | 작업 노트(시나리오 계약/상태 원장/findings/learnings) |

> 교훈: **Lua 로드 자동화는 멀티윈도우(스크립팅 창 + 한글 경로 파일 다이얼로그)라 너무 불안정**해서,
> 런처는 "한 번만 수동 GUI 로드"를 문서화된 단계로 남기는 쪽으로 정리했다. → [07](07-pitfalls-archive.md)

---

## 3. 수동 검증 워크플로우 (권장)

1. mGBA + ROM 실행 (창 제목으로 로드 확인).
2. `play.ps1 -Keys "..."` 로 한 스텝씩 키 전송 + 스크린샷.
3. 스크린샷으로 결과 확인 → `manual-play-archive.md` 에 진행/막힘 기록.
4. 같은 좌표/화면에서 반복 실패하면 다른 접근으로 전환(아카이브에 남겨 재발 방지).

---

다음: [07 · 함정 아카이브](07-pitfalls-archive.md)
