# 01. 아키텍처 비교 (Architecture Comparison)

포켓몬스터 레드 버전을 자동으로 플레이하기 위해 다양한 아키텍처가 시도되었습니다. 본 문서에서는 대규모 언어 모델(LLM) 기반의 Grokemon, 강화학습(RL) 기반의 PokemonRedExperiments, 그리고 지식 기반 하이브리드 구조인 POPOPOPOket의 아키텍처를 상세히 비교합니다. 각 시스템은 상태 분석, 의사결정, 입력 제어 방식에서 뚜렷한 차이를 보입니다.

## A. Grokemon 아키텍처 (LLM Agent)

```
Grok 4.3 (OpenAI-compatible API)
  |
  v
CommandAgentRunner (턴 루프 오케스트레이터, 942줄)
  |-- prepareTurn(): 완료 확인, 자동 대화/배틀 처리
  |-- buildAgentObservation(): LLM 입력 구성
  |-- session.sendUserMessage(): LLM 호출
  |-- consumeRunEvents(): 도구 호출 처리, 게임 액션 후 인터럽트
  |-- refreshState(): 게임 상태 동기화
  |-- recordTurn(): 증거 기록
  |
  v
CommandExecutor (모드 기반 라우팅)
  |-- NavigateExecutor: A* 경로탐색 + NPC 장애물 감지
  |-- InteractExecutor: NPC/물체 상호작용
  |-- DialogExecutor: 대화/선택/이름입력
  |-- BattleExecutor: 배틀 메뉴 네비게이션
  |
  v
InputGate (입력 안전 게이트)
  |-- wJoyIgnore 검사 (0xCDCB)
  |-- wWalkCounter 검사 (0xD00D)
  |-- rWY 텍스트 윈도우 검사 (0xFF4A)
  |-- 2회 연속 안정 읽기까지 폴링
  |
  v
MgbaHttpClient -> mGBA-http(:5000) -> mGBASocketServer.lua(:8888) -> mGBA
```

### 주요 컴포넌트:
- 세션 관리: MiniStateReader가 11개의 병렬 RAM 읽기를 수행하여 SessionState의 권위적 모드를 갱신합니다.
- 도구 시스템: navigate, interact, wait, dialog, battle 등 5개의 게임 액션 도구와 메모리 도구, 세이브/로드 기능을 제공합니다.
- 관측 빌더: [SESSION], [TOOLS], [EVENTS], [SUPERVISOR], [MEMORY], [HISTORY] 등의 태그 섹션으로 LLM 입력을 구성합니다.
- 프롬프트 빌더: 모드별 시스템 프롬프트, 게임 지식, 상태 요약을 결합합니다.
- 메모리: 6개 섹션으로 구성된 AgentMemoryStore와 타일, NPC, 워프 정보를 기록하는 MapMemory를 사용합니다.
- Supervisor: StuckDetector, GoalLedger, LLMAdviser, InterventionLoop를 통해 에이전트의 교착 상태를 감지하고 개입합니다.
- 증거: EvidenceRecorder를 통해 각 턴의 실행 결과와 스크린샷을 runs/{runId}/turns/{seq}.json 경로에 기록합니다.

## B. PokemonRedExperiments 아키텍처 (RL)

```
PPO Policy (Stable Baselines 3)
  |-- MultiInputPolicy (Dict 관측 처리)
  |-- CNN encoder (72x80 프레임)
  |-- Fourier encoder (레벨 합산)
  |-- Binary inputs (배지, 이벤트)
  |
  v
RedGymEnv (Gymnasium 래퍼)
  |-- Observation Space: Dict(screens, health, level, badges, events, map, recent_actions)
  |-- Action Space: Discrete(7) [방향4 + A + B + Start]
  |-- Reward Shaping: events*4 + badges*10 + healing*10 + explore + stuck_penalty
  |-- 24프레임/액션 (프레스 0, 릴리스 8, 틱 24)
  |
  v
PyBoy (Python Game Boy 에뮬레이터)
  |-- pyboy.memory[addr]: 직접 RAM 읽기
  |-- pyboy.button('a'): 버튼 입력
  |-- pyboy.screen.ndarray: 스크린 캡처
  |-- pyboy.tick(): 프레임 진행
  |-- 344x 실시간 속도 (headless)
```

### 주요 컴포넌트:
- 훈련: SubprocVecEnv를 통해 64개의 병렬 환경을 구동하며, n_steps=2560, batch=512, gamma=0.997 설정을 사용합니다.
- 탐색 보상: 초기 버전은 프레임 벡터 기반의 KNN을 사용했으나, 후기 버전은 x, y 좌표와 맵 ID 튜플을 카운팅하는 방식으로 개선되었습니다.
- 이벤트 추적: 1024비트 크기의 이벤트 플래그 바이너리 벡터를 통해 게임 진행 상황을 추적합니다.
- 글로벌 맵: 484x476 픽셀 크기의 전체 좌표계와 48x48 크기의 로컬 뷰를 병행하여 위치를 파악합니다.
- 스트리밍: WebSocket 기반의 StreamWrapper를 사용하여 실시간으로 학습 화면을 중계합니다.
- 로깅: TensorBoard, Weights&Biases, CSV 파일에 학습 메트릭을 기록합니다.

## C. POPOPOPOket 공략 아키텍처 (Knowledge Base)

```
TypeScript 하네스 (턴 루프)
  |
  |-- fast-flow 결정 (LLM 바이패스)
  |   |-- Route 1 (0x0C): 자동 북진
  |   |-- 배틀: 자동 A (40턴 제한)
  |   |-- 기타: LLM 판단으로 폴백
  |
  |-- stuck-memory 주입
  |   |-- 실패 이동 기록 (좌표|액션 -> 실패횟수)
  |   |-- STUCK_THRESHOLD=8 반복 -> 프롬프트 주입
  |
  |-- supervisor 정규화
  |   |-- 방향 이동 1타일 정규화
  |   |-- 위험한 다중홀드 거부
  |   |-- 정착 프레임 대기
  |
  v
mGBA-http -> mGBASocketServer.lua -> mGBA
```

### 3층 자동조종 (다층 아키텍처):
```
L3: 정책 LLM (목표 설정, 정책 업데이트)
     ^
     | 보고
L2: 비평가 (이상 감지, 막힘 판단)
     ^
     | 관찰
L1: 무의식 (결정론적/휴리스틱 기본 이동, fast-flow)
```

이 시스템은 효율적인 3층 자동조종 구조를 채택하여 실행 속도를 높이고 API 비용을 절감합니다.
주요 특징은 다음과 같습니다.
- fast-flow 결정: 특정 맵에서의 이동이나 단순 배틀 상황에서는 LLM 호출을 생략하고 미리 정의된 규칙에 따라 행동합니다.
- stuck-memory 주입: 캐릭터가 특정 위치에서 반복적으로 이동에 실패하면 해당 기록을 메모리에 누적하고, 임계값을 초과할 경우 프롬프트에 경고를 주입하여 LLM이 다른 경로를 선택하도록 유도합니다.
- supervisor 정규화: 입력의 안정성을 확보하기 위해 방향 이동을 1타일 단위로 제한하고, 오작동을 유발할 수 있는 다중 키 입력을 차단합니다.

## D. 컴포넌트별 비교표

| 컴포넌트 | Grokemon | PokemonRedExperiments | POPOPOPOket |
| :--- | :--- | :--- | :--- |
| 턴 루프 | CommandAgentRunner | RedGymEnv.step() | fast-flow + LLM |
| 상태 읽기 | MiniStateReader (11 RAM) | memory[addr] 직접 읽기 | RAM + 스크린샷 |
| 모드 감지 | classifyGameMode() | 없음 (항상 step 실행) | visual-fallback |
| 입력 안전 | InputGate (3단계 검증) | 없음 (24프레임 고정) | supervisor 정규화 |
| 경로탐색 | A* Pathfinder | 없음 (정책이 학습) | 없음 |
| 메모리 | AgentMemoryStore + MapMemory | 없음 (정책 내재) | stuck-memory |
| 막힘 감지 | StuckDetector (5레벨) | stuck penalty (-0.05) | stuck-memory (8회 임계) |
| 비전 입력 | 스크린샷 (모델에 전달) | 프레임 스택 (관측 공간) | 원본 + 그리드 + 마스킹 |
| 로깅 | JSON + 스크린샷 | TensorBoard + CSV | pretty-log + 메트릭 |
| 비용 모델 | API 호출 (토큰 비용) | GPU 훈련 (전력 비용) | API + 수동 규칙 |

## E. 하이브리드/외부 아키텍처 참조

### PokeAgent Challenge (NeurIPS 2025)

```
Orchestrator (LLM)
  |-- Battle Strategist (LLM)
  |-- Navigation Planner (A* + LLM)
  |-- Objective Verifier (LLM)
  |-- Gym Puzzle Solver (LLM)
  |
  v
MCP Tools: 경로탐색, BUTTON 입력, 지식 검색, 타입 차트
```

PokeAgent Challenge는 다중 에이전트 협업과 도구 사용에 초점을 맞춘 구조입니다. 오케스트레이터가 하위 전문 에이전트들에게 작업을 분배하고, MCP 도구를 활용하여 문제를 해결합니다.

### Continual Harness (자기개선)

```
Agent Rollout (256 steps)
  -> Process Reward Model 평가
  -> 저보상 구간 재라벨링 (frontier teacher)
  -> Soft SFT 업데이트
  -> 다음 체크포인트
```

Continual Harness는 에이전트의 실행 결과를 평가하여 지속적으로 성능을 개선하는 파이프라인입니다. 저보상 구간을 재라벨링하고 지도 미세조정(SFT)을 수행하여 모델의 행동을 교정합니다.
