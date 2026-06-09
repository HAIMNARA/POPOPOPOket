# POPOPOPOket — 포켓몬 레드 AI 자동화 최적 워크플로우 & 지식 아카이브

LLM 에이전트, 강화학습(RL), 하이브리드 접근법을 종합 분석하여 **포켓몬 레드(Game Boy)** 를
자동으로 플레이하기 위한 최적 워크플로우와 공략 지식을 체계화한 저장소입니다.

3개 프로젝트를 분석하여 도출한 결과물입니다:
- **[Grokemon](https://github.com/INONONO66/grokemon)** — Grok 4.3 LLM 에이전트 (TypeScript, mGBA-http)
- **[PokemonRedExperiments](https://github.com/PWhiddy/PokemonRedExperiments)** — PPO 강화학습 (Python, PyBoy, 7.9k stars)
- **POPOPOPOket** — 워크플로우/공략 지식 아카이브 (본 저장소)

> **핵심 발견**: 하이브리드 접근(LLM 상위 계획 + 결정론적/RL 하위 실행)이 순수 LLM이나 RL보다 우수하다.
> 메모리 마스킹으로 벽 탐색 수십턴을 1-2턴으로 단축하고, stuck-memory로 무한반복을 차단하며,
> fast-flow로 결정론적 구간의 토큰을 70% 이상 절약할 수 있다.

---

## 이게 뭔가요?

- 사람이 키를 누르는 대신, **LLM이 매 턴 화면(스크린샷)과 RAM 상태를 관찰하고 버튼 하나를 누르는** 방식으로
  포켓몬 레드를 플레이합니다.
- 에뮬레이터 제어는 `mGBA-http`(HTTP API) + `mGBASocketServer.lua`(소켓 서버)를 통해 이뤄집니다.
- TypeScript 하네스가 관찰 → 모델 호출 → 액션 실행 → 메트릭/트레이스 기록의 루프를 돕니다.
- 토큰 낭비를 줄이기 위한 **결정론적 자동조종(fast-flow)**, **막힘 감지(stuck-memory)**,
  **로컬 슈퍼바이저(supervisor)** 가 붙어 있습니다.

이 저장소는 **실행 코드가 아니라 워크플로우와 공략을 문서화한 것**입니다.
(하네스 구현체는 별도 TypeScript 프로젝트에 있으며, 여기서는 그 설계와 지식을 체계화합니다.)

---

## Ultimate 문서 (3개 프로젝트 종합 분석)

Grokemon(LLM), PokemonRedExperiments(RL), POPOPOPOket(지식)을 종합 분석하여 도출한 최적 워크플로우입니다.

| 문서 | 내용 |
|---|---|
| [00 · 종합 개요](docs/ultimate/00-executive-summary.md) | 3개 프로젝트 비교, 핵심 발견, 최적 접근법 요약 |
| [01 · 아키텍처 비교](docs/ultimate/01-architecture-comparison.md) | LLM vs RL vs Hybrid 아키텍처 다이어그램 + 컴포넌트별 비교표 |
| [02 · 통합 환경 구축](docs/ultimate/02-environment-setup.md) | mGBA-http + PyBoy 양쪽 설정, 검증, 트러블슈팅 |
| [03 · 통합 RAM 레퍼런스](docs/ultimate/03-ram-reference.md) | 3개 프로젝트 통합 메모리 주소 (플레이어/파티/배틀/맵/이벤트) |
| [04 · 에이전트 설계 패턴](docs/ultimate/04-agent-design-patterns.md) | LLM/RL/하이브리드 3가지 패러다임, 다층 아키텍처, 유전 알고리즘 |
| [05 · 보상 설계 & 진행도 감지](docs/ultimate/05-reward-and-progress.md) | RL 보상 V1/V2 상세, LLM 9단계 체크포인트, 마일스톤 시스템 |
| [06 · 입력 안전 메커니즘](docs/ultimate/06-input-safety.md) | InputGate 3단계, wJoyIgnore, Supervisor 정규화, Guards |
| [07 · 막힘 감지 & 복구](docs/ultimate/07-stuck-detection.md) | StuckDetector 5레벨, stuck-memory, InterventionLoop |
| [08 · 비전 & 관측 시스템](docs/ultimate/08-vision-and-observation.md) | 비전 입력 v0-v3 진화, 메모리 마스킹, 관측 빌더 |
| [09 · 통합 함정 아카이브](docs/ultimate/09-pitfalls-archive.md) | 3개 프로젝트 통합 20건+ 함정, 빠른 진단 체크리스트 |
| [10 · 최적 워크플로우](docs/ultimate/10-optimal-workflow.md) | **핵심 문서** — 단계별 구현 가이드, 결정 트리, 모델 비교, 안티패턴 |
| [11 · 미래 로드맵](docs/ultimate/11-future-roadmap.md) | P0/P1/P2 개선 사항, 기술 스택 진화 v1-v3 |

---

## 원본 문서 (POPOPOPOket 실험 기록)

| 문서 | 내용 |
|---|---|
| [01 · 개요 & 워크플로우](docs/01-overview-workflow.md) | 전체 아키텍처, 컴포넌트 구성, 매 턴 루프, 대안 아키텍처 패턴 |
| [02 · 환경 셋업](docs/02-environment-setup.md) | mGBA + mGBA-http + Lua 소켓 + 하네스 구동 절차, 연결 점검 |
| [03 · 공략 가이드](docs/03-strategy-guide.md) | 침실 → Viridian City 루트, 마일스톤 9단계, 마스킹 시스템, 세션 핸드오프 |
| [04 · RAM 맵 & 조작 레퍼런스](docs/04-ram-and-controls.md) | 포켓몬 레드 WRAM 주소, 키 매핑, 방향 코드, 맵 ID |
| [05 · 자동조종 & 복구 로직](docs/05-autopilot-and-recovery.md) | fast-flow, stuck-memory, supervisor, 다층 아키텍처, 피드백 루프 |
| [06 · 수동 플레이 툴킷](docs/06-manual-play-toolkit.md) | `.omo` PowerShell 드라이버(키 입력 + 스크린샷) 사용법 |
| [07 · 함정 아카이브](docs/07-pitfalls-archive.md) | 재발 방지 교훈 15건 (스크립트 무한루프 사고, 풀숲 오인식 등) |
| [08 · 회의 리뷰 (2026-06-06)](docs/08-meeting-review-2026-06-06.md) | 자동화 발표 세션 체계화, 참가자별 아키텍처, Grok 효과, 핵심 인사이트 |
| [09 · 향후 로드맵](docs/09-next-roadmap.md) | pyboy 도입, 포획 이벤트, 완전 자동화 에이전트, 기술 스택 진화 |
| [10 · 포스트모템: 스크립트 오류 & Grok 효과](docs/10-grok-script-error-postmortem.md) | "스크립트 추가" 무한루프 사고 원인/해결, Grok 모델 효과 분석 |
| [launch-pokemon.ps1](harness/launch-pokemon.ps1) | 원클릭 런처 (mGBA→Lua GUI 로드→mGBA-http→체인 검증) |

---

## 빠른 시작 (요약)

자세한 절차는 [02 · 환경 셋업](docs/02-environment-setup.md) 참고.

1. **mGBA에 ROM을 먼저 로드**한 상태로 실행.
2. mGBA에서 **Tools → Scripting → File → Load script** 로 `mGBASocketServer.lua` 를 **딱 한 번** 로드.
   - 콘솔에 `mGBA script server 0.8.2 ready. Listening on port 8888` 가 떠야 정상.
3. `mGBA-http` 실행 → `http://127.0.0.1:5000` 에서 200 응답 확인.
4. 하네스 실행(`pnpm dev`) → 에이전트가 매 턴 한 액션씩 실행하며 자동 플레이 시작.

> ⚠️ **가장 큰 함정**: mGBA 0.10.x에는 `--script` CLI 옵션이 **없습니다**
> (`unknown option -- script` 에러 후 즉시 종료). Lua는 반드시 GUI로, **한 번만** 로드하세요.
> 두 번 로드하면 소켓/콜백이 중복되어 mGBA가 크래시합니다. → [07 · 함정 아카이브](docs/07-pitfalls-archive.md)

---

## 핵심 설계 원칙

- **메모리 읽기 = 결정론적 검증**: 포켓몬 레드의 잘 알려진 WRAM 주소를 폴링해 위치/전투/방향을 확인.
  스크린샷만 믿지 않고 RAM으로 진행을 교차검증한다.
- **결정론적 구간은 LLM에게 안 맡긴다**: Route 1 같은 직선 통로는 코드가 "북진"으로 처리해 토큰을 아낀다.
  건물/메뉴/인트로처럼 분기가 많은 곳만 LLM이 판단한다.
- **막힘은 기억한다**: 같은 좌표에서 같은 이동이 반복 실패하면 기록해두고, 프롬프트에 주입해 무한 반복을 막는다.
- **증거 없는 개선은 없다**: 토큰이 줄어도 진행/막힘/액션 다양성/툴 신뢰성이 나빠지면 롤백한다.
- **닫힌 루프만 있으면 개선은 발생한다**: 피드백 루프를 구성하면 속도가 느려도 지속적 개선이 일어난다.
  이슈/티켓 기반 메타 레이어로 검증됨. (2026-06-06 회의 도출)
- **비전 입력은 오염하지 않는다**: 좌표 그리드를 원본에 직접 오버레이하면 모델 추론이 망가진다.
  원본 + 가이드 이미지를 별도로 제공할 것. (2026-06-06 회의 도출)
