# POPOPOPOket — 포켓몬 레드 자동화 플레이 워크플로우 & 공략 아카이브

LLM 에이전트가 mGBA에서 구동 중인 **포켓몬 레드(Game Boy)** 를 자동으로 플레이하도록 만든
실험의 워크플로우, 공략 지식, 하드원(hard-won) 교훈을 한곳에 체계화한 저장소입니다.

> **목표 마일스톤**: RED 캐릭터를 침실(2F)에서 출발시켜 **Viridian City(초록마을)** 까지 자율 진행.
> 이 저장소는 그 과정에서 만든 자동화 파이프라인 설계, 포켓몬 레드 RAM 맵, 공략 루트,
> 자동조종 로직, 그리고 수없이 깨지면서 알아낸 함정들을 정리한 **지식 베이스**입니다.

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

## 문서 인덱스

| 문서 | 내용 |
|---|---|
| [01 · 개요 & 워크플로우](docs/01-overview-workflow.md) | 전체 아키텍처, 컴포넌트 구성, 매 턴 루프(관찰→판단→액션→기록) |
| [02 · 환경 셋업](docs/02-environment-setup.md) | mGBA + mGBA-http + Lua 소켓 + 하네스 구동 절차, 연결 점검 |
| [03 · 공략 가이드](docs/03-strategy-guide.md) | 침실 → Viridian City 루트, 진행 마일스톤 9단계 체계 |
| [04 · RAM 맵 & 조작 레퍼런스](docs/04-ram-and-controls.md) | 포켓몬 레드 WRAM 주소, 키 매핑, 방향 코드, 맵 ID |
| [05 · 자동조종 & 복구 로직](docs/05-autopilot-and-recovery.md) | fast-flow 결정론적 이동, stuck-memory 막힘 감지, supervisor 정규화 |
| [06 · 수동 플레이 툴킷](docs/06-manual-play-toolkit.md) | `.omo` PowerShell 드라이버(키 입력 + 스크린샷) 사용법 |
| [07 · 함정 아카이브](docs/07-pitfalls-archive.md) | 막힘/오류 기록, 재발 방지 교훈 (mGBA `--script` 함정 등) |

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
