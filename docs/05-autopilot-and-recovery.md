# 05 · 자동조종 & 복구 로직

토큰을 아끼고 무한루프를 막기 위한 세 가지 로컬 메커니즘:
**fast-flow(결정론적 자동조종)**, **stuck-memory(막힘 감지)**, **supervisor(제어 정규화)**.

---

## 1. fast-flow — 결정론적 zero-LLM 이동

핵심 아이디어: **"명백하게 안전한 수"일 때만** LLM 없이 코드가 액션을 결정한다.
애매하면 `null` 을 반환해 정상 LLM 턴으로 폴백한다.
→ 최악의 경우가 LLM-only 하네스와 동일하도록 보장(절대 무한루프 안 됨).

### 결정 순서 (`chooseFastFlowAction`)

1. **상태 없음/읽기 불가** → `null` (LLM에 위임).
2. **목표 맵(Viridian, `0x01`)** → `null`. 여기선 아무 액션도 안 한다(루프가 `isViridianReached`로 멈춤).
3. **전투 중** → `A` 탭(auto-battle). 단 `battleTurns > 40`(BATTLE_DEFER_CAP) 넘으면 `null` 로 위임
   (이길 수 없는 전투가 영원히 도는 것 방지).
4. **북진 통로 맵(Route 1, `0x0C`)** → `Up` 홀드로 한 타일 북진.
   - 좌표가 바뀌었으면 `blockedNorthTurns = 0` 리셋.
   - 이미 북향(`up`)인데 좌표 그대로면 실장애물(울타리/절벽) → `blockedNorthTurns++`,
     `>= 3`(NORTH_BLOCK_DEFER)이면 `null` 로 위임(LLM이 우회 경로 찾도록).
   - 아직 북향이 아니면 첫 `Up`은 방향 전환만, 다음 `Up`이 실제 이동.
5. **그 외(마사라타운, 실내, Oak 연구소, 메뉴, 미지의 맵)** → `null` (LLM 판단).

### 상수

| 상수 | 값 | 의미 |
|---|---|---|
| `SINGLE_TILE_DURATION` | `12` | 한 타일 이동용 홀드 프레임 |
| `NORTH_BLOCK_DEFER` | `3` | 북향 막힘 N회 후 LLM 위임 |
| `BATTLE_DEFER_CAP` | `40` | auto-A 전투 N턴 후 LLM 위임 |
| `VIRIDIAN_CITY_MAP` | `0x01` | 목표 맵 |
| `ROUTE_ONE_MAP` | `0x0C` | 북진 자동 구간 |

> **왜 Route 1만 북진 자동인가**: 건물·메뉴가 없는 가장 긴 직선 통로라 LLM이 토큰을 가장 많이 태우는 곳.
> Pallet Town·실내·Oak 연구소·메뉴·인트로는 분기가 많아 맹목적 북진이 위험하므로 LLM에게 남긴다.

### fast-flow 메모리

```ts
interface FastFlowMemory {
  battleTurns?: number;       // auto-battle 누적 턴
  blockedNorthTurns?: number; // 북향 막힘 누적
  lastMapId?, lastX?, lastY?; // 직전 위치 (이동 여부 판정용)
}
```

> 구현 노트: fast-flow의 결정 로직은 작성·테스트되었으나 과거 세션 시점엔 `index.ts` 턴 루프에
> 완전히 와이어링되지 않았고, 대사/메뉴 분기는 `dialogueLike/menuLike`가 항상 `visual-fallback`이라
> 죽은 가지였다. 라이브 프레임 보정(시각 휴리스틱)이 와이어링 전제였다. → [07](07-pitfalls-archive.md)

---

## 2. stuck-memory — 막힘 감지 & 복구 힌트

같은 좌표/화면에서 같은 이동이 반복 실패하는 것을 기록해 프롬프트에 주입, 맹목 반복을 차단한다.

### 동작

- **이동 시도 추적**: `mgba_tap`/`mgba_hold` 중 **단일 방향 버튼**만 이동 시도로 본다.
- **정지 판정(`isStationary`)**: 액션 전/후 컨텍스트 키가 같으면 "안 움직임".
  - 상태 기반 컨텍스트 키: `map:<id>:x:<x>:y:<y>:dir:<dir>`
  - RAM 없을 때: 스크린샷 SHA-256 앞 12자리 해시로 컨텍스트 구성.
- **실패 엣지 누적**: `<context>|<action>` 키로 실패 횟수를 센다.
  - `STUCK_THRESHOLD = 8` 회 반복 실패 시 `stuckEvents++` (막힘 이벤트로 카운트).
  - 최근 실패 엣지 최대 `MAX_FAILED_EDGES = 6` 개 유지(오래된 것 제거).
- **복구 시도 기록**: 막힌 뒤 시도한 비이동 액션을 최대 `MAX_RECOVERY_ATTEMPTS = 6` 개 보관.

### 프롬프트 주입 형식 (`formatStuckMemory`)

```
failed movement memory:
- map=12 x=5 y=8 facing=up; hold:Up; failed 8x; last turn 42
recent recovery attempts:
- turn 43: tap:{"button":"B"} after map=12 x=5 y=8 facing=up
```

전투/대사/메뉴 상태이거나 맵·좌표가 `null`이면 이동 컨텍스트를 만들지 않는다(오탐 방지).

---

## 3. supervisor — 제어 정규화 (안전벨트)

로컬 슈퍼바이저는 HTTP 클라이언트 위의 프록시로, 제어 호출이 mGBA에 닿기 전에 정규화한다.

- 방향 이동을 **1타일**로 정규화.
- 비방향 탭 정규화.
- 위험한 방향 멀티홀드 거부.
- 액션 후 정착(settle) 프레임 대기.
- 다음 관찰 전 짧은 흑/로딩 프레임 폴링.

> 구조 노트: `supervisor.ts` 는 타이밍만 다루는 HTTP 프록시. LLM 우회(자동조종) 판단은
> `index.ts` 의 턴 루프(`session.send` 직전)에 들어가야 한다. 슈퍼바이저에 넣으면 안 된다.

---

## 4. 자동조종 우선순위 (설계 의도)

대사/메뉴 자동화까지 포함한 의도된 우선순위(설계):

```
name-entry (이름 입력 auto-START)  >  battle (auto-A)  >  dialogue (auto-A)
```

- 야생 전투(`battleType == 0`) 같은 케이스는 별도 처리 분기 필요.
- 대사/이름입력 감지는 RAM만으로 부족 → **프레임버퍼 휴리스틱**(160×144 매트릭스 분석)이 전제.
  `screenshot-image.ts` 의 PNG 디코드 + Game Boy 크롭 + 픽셀 매트릭스를 활용.

---

## 5. 다층 자동조종 아키텍처 (2026-06-06 회의 도출)

단일 fast-flow + stuck-memory를 넘어, 회의에서 검증된 고급 패턴:

### 5-1. 신경계 모사 3계층

```
L3: 정책 LLM ─── "다음엔 이렇게 해야지" (목표 설정, 정책 갱신)
     ↑ 보고
L2: 크리틱 ────── "지금 이상한가?" (이상 감지, stuck 판별)
     ↑ 관찰
L1: 무의식 이동 ─ 결정론적/휴리스틱 기본 이동 (현재 fast-flow에 해당)
```

- L1은 현재 `chooseFastFlowAction`의 역할
- L2는 현재 `stuck-memory`의 역할을 확장 — 단순 좌표 반복 외에 **행동 패턴 이상**도 감지
- L3은 현재 LLM 턴 판단을 확장 — 실패 패턴을 분석하여 **정책을 생성/갱신**

이 구조는 **코딩 태스크 등 다른 도메인에도 적용 가능**한 범용 패턴.

### 5-2. 메타 레이어: 닫힌 피드백 루프

> "닫힌 루프만 구성하면 속도가 느리더라도 지속적 개선이 발생한다"

구현 원리:
1. 매 이동마다 **갈 수 있는 곳 / 막힌 곳을 기록** (현재 stuck-memory의 확장)
2. 기록 데이터를 판단하는 **메타 레이어** 추가
3. 메타 레이어가 **정책을 업데이트** → 다음 이동에 반영

이것이 "이슈/티켓 시스템 기반 메타 레이어"의 핵심이며,
현재 stuck-memory의 `formatStuckMemory` → 프롬프트 주입이 이 구조의 초기 형태.

### 5-3. 병렬 인스턴스 + 중앙 공략집

fast-flow/stuck-memory가 단일 인스턴스 내 로직이라면,
이 패턴은 **여러 인스턴스를 동시 실행**하여 탐색을 가속:

- 각 인스턴스가 독립적으로 경로 탐색
- 실수/성공 사례를 **중앙 공략집 파일**에 누적
- 새 인스턴스 시작 시 공략집을 읽어 같은 실수 방지
- **MCP 서버**로 에뮬레이터 다중 운용

### 5-4. 인간 vs. AI 지속성 트레이드오프

| | 인간 (바이오 토큰) | AI (API 토큰) |
|---|---|---|
| 단기 속도 | 빠름 | 느림 |
| 지속성 | 수면 필요 → 역전당함 | 24시간 무중단 |
| 관찰력 | 직관적 패턴 인식 | 시각 정보 의존 |

실제 이벤트에서 인간이 먼저 풀고 있었으나, 수면 중 AI에게 역전당한 사례 확인됨.
→ 장기 실행 시나리오에서는 AI 에이전트의 지속성이 핵심 경쟁력.

---

다음: [06 · 수동 플레이 툴킷](06-manual-play-toolkit.md)
