# 04 · RAM 맵 & 조작 레퍼런스

포켓몬 레드(Game Boy)의 WRAM 주소와 입력 매핑 레퍼런스.
이 값들은 **포켓몬 레드 기준**이며, 다른 ROM에는 그대로 적용하면 안 된다.

---

## 1. 포켓몬 레드 WRAM 주소 (read8 폴링 대상)

`pokemon-state.ts` 가 매 턴 읽는 컴팩트 상태 필드:

| 필드 | 주소 | 설명 |
|---|---|---|
| `mapId` | `0xD35E` | 현재 맵 ID |
| `yCoord` | `0xD361` | 플레이어 Y 좌표 |
| `xCoord` | `0xD362` | 플레이어 X 좌표 |
| `playerFacing` | `0xC109` | 바라보는 방향 (코드값) |
| `isInBattle` | `0xD057` | 전투 여부 (0이 아니면 전투 중) |
| `battleType` | `0xD05A` | 전투 종류 (예: 야생=0) |
| `battleResult` | `0xCF0B` | 전투 결과 |

> 주의: 위는 하네스에서 실제 폴링하던 주소 집합이다. `stuck-memory`/초기 분석 노트에서는
> `mapId=0xD35E`, `isInBattle=0xD057`, `battleType=0xD05A` 를 핵심 검증 주소로 사용했다.
> RAM 읽기에 실패하면 시각(스크린샷) 전용 관찰로 폴백한다.

### 파생 상태

- `battle = (isInBattle !== 0)`
- `dialogueLike`, `menuLike` 는 RAM만으로는 신뢰 판정이 어려워 기본값이 `"visual-fallback"`.
  → 대사/메뉴 자동화(auto-A, name-entry auto-START)는 **프레임버퍼 휴리스틱(시각 보정)** 이 필요.
  이게 4a/4b 자동조종의 #1 리스크였다. → [05](05-autopilot-and-recovery.md), [07](07-pitfalls-archive.md)

---

## 2. 방향 코드 (`playerFacing` → 방향)

`formatDirection()` 매핑:

| 코드값 | 방향 |
|---|---|
| `0` | down (아래) |
| `4` | up (위) |
| `8` | left (왼쪽) |
| `12` | right (오른쪽) |
| 그 외 | unknown |

---

## 3. 주요 맵 ID

| 맵 ID | 위치 | 비고 |
|---|---|---|
| `0x01` | **Viridian City** | 목표 마일스톤 (`viridian-city-reached`) |
| `0x0C` | **Route 1** | 북진 결정론적 자동조종 구간 |

> Viridian = `0x01` 이라 마일스톤 테스트에서 "일반 다른 맵"으로 `mapId:1` 을 쓰면 충돌.
> 테스트에서는 일반 맵 변경을 `mapId:2` 로 표현하고 `0x01` 은 Viridian 전용으로 예약한다.

---

## 4. mGBA 기본 조작키

게임패드 → 키보드 기본 매핑 (mGBA 0.10.x 기본값):

| 게임 버튼 | 키보드 키 | `play.ps1` 토큰 | Virtual-Key |
|---|---|---|---|
| ↑ Up | ↑ (Arrow Up) | `u` | `0x26` |
| ↓ Down | ↓ (Arrow Down) | `d` | `0x28` |
| ← Left | ← (Arrow Left) | `l` | `0x25` |
| → Right | → (Arrow Right) | `r` | `0x27` |
| A | `X` | `a` | `0x58` |
| B | `Z` | `b` | `0x5A` |
| Start | `Enter` | `s` | `0x0D` |
| Select | `Backspace` | `e` | `0x08` |

---

## 5. 모델에게 노출되는 제어 툴

LLM이 쓸 수 있는 툴(에이전트 도구):

- `mgba_tap` — 버튼 한 번 누름
- `mgba_tap_many` — 여러 버튼 순차 탭
- `mgba_hold` — 버튼을 일정 시간 누르고 유지
- `mgba_hold_many` — 여러 버튼 홀드
- `mgba_release` — 누른 버튼 해제

> **ROM 로딩/리셋 툴은 의도적으로 노출하지 않는다.** 모델이 게임 진행을 리셋/되돌리지 못하게 막는다.

### 슈퍼바이저 정규화

로컬 supervisor가 제어 호출을 mGBA로 보내기 전에:

- 방향 이동을 **1타일**로 정규화
- 비방향 탭 정규화
- 위험한 방향 멀티홀드 거부
- 액션 후 정착(settle) 프레임 대기
- 다음 관찰 전 짧은 흑/로딩 프레임을 폴링

---

## 6. mGBA-http HTTP 엔드포인트 (점검용)

연결 점검에 쓰는 주요 경로(`http://127.0.0.1:5000`):

| 경로 | 용도 |
|---|---|
| `/core/currentframe` | 현재 프레임 번호 |
| `/core/getgamecode` | 게임 코드 (예: `DMG-AR`) |
| `/core/getgametitle` | 게임 타이틀 (예: `POKEMON RED`) |
| `/mgba-http/button/getall` | 버튼 상태 일괄 조회 |

메모리 읽기는 `read8(addr)` 형태로 위 WRAM 주소를 폴링한다.

---

다음: [05 · 자동조종 & 복구 로직](05-autopilot-and-recovery.md)
