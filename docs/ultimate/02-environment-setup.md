# 02. 통합 환경 구축 가이드

이 문서는 포켓몬스터 레드 자동화 프로젝트를 실행하기 위한 두 가지 에뮬레이터 환경 구축 방법을 설명합니다. mGBA-http 방식과 PyBoy 방식의 설치 과정, 실행 순서, 검증 방법, 그리고 발생하기 쉬운 문제 해결법을 다룹니다.

## A. mGBA-http 방식 (Grokemon, POPOPOPOket)

mGBA 에뮬레이터에 HTTP API 서버를 연결하여 TypeScript 하네스로 제어하는 방식입니다.

### 1. 필요 소프트웨어
* Node.js 20 버전 이상 및 pnpm 11.2.2
* mGBA 0.10.x (기본 설치 경로: `C:\Program Files\mGBA\mGBA.exe`)
* mGBA-http 실행파일 (`.local-tools/mgba-http/mGBA-http.exe`)
* mGBASocketServer.lua 스크립트 (`.local-tools/mgba-http/mGBASocketServer.lua`)
* 합법적으로 취득한 포켓몬스터 레드 ROM 파일

### 2. 연결 체인 구조
TypeScript 하네스가 HTTP 요청을 보내면 mGBA-http 서버가 이를 받아 TCP 소켓을 통해 mGBA 내부의 Lua 스크립트 서버로 전달합니다.
```
TypeScript 하네스 -> mGBA-http (포트 5000) -> TCP (포트 8888) -> mGBASocketServer.lua -> mGBA
```

### 3. 시작 순서 (반드시 순서를 준수해야 합니다)

#### 단계 1: mGBA 실행 및 ROM 로드
PowerShell을 열고 아래 명령어로 mGBA와 포켓몬 레드 ROM을 실행합니다.
```powershell
& "C:\Program Files\mGBA\mGBA.exe" "Pokemon - Red Version.gb"
```
실행 후 윈도우 타이틀이 `mGBA - POKEMON RED - 0.10.5`와 같이 표시되는지 확인합니다.

#### 단계 2: Lua 소켓 서버 GUI 로드
mGBA 창의 상단 메뉴에서 `Tools` -> `Scripting` -> `File` -> `Load script`를 선택합니다.
`.local-tools/mgba-http/mGBASocketServer.lua` 파일을 선택하여 로드합니다.
콘솔 창에 `mGBA script server 0.8.2 ready. Listening on port 8888` 메시지가 출력되는지 확인합니다.
*주의: 이 작업은 에뮬레이터 실행 후 딱 한 번만 수행해야 합니다. 중복 로드하거나 dofile() 명령을 사용하면 에뮬레이터가 강제 종료됩니다. CLI 옵션인 --script도 사용하면 안 됩니다.*

#### 단계 3: mGBA-http 실행
새로운 PowerShell 창을 열고 mGBA-http 프록시 서버를 실행합니다.
```powershell
& ".local-tools\mgba-http\mGBA-http.exe"
```
서버가 시작되면 `http://127.0.0.1:5000` 주소로 요청을 보낼 수 있는 상태가 됩니다.

#### 단계 4: 하네스 실행
프로젝트 루트 디렉토리에서 아래 명령어를 순서대로 실행합니다.
```bash
pnpm install
cp .env.example .env
```
`.env` 파일을 열어 필요한 환경 변수를 설정한 뒤 하네스를 구동합니다.
```bash
pnpm run harness preflight
pnpm run harness run --max-turns 100
```

### 4. mGBA-http API 주요 엔드포인트

| 카테고리 | 엔드포인트 | 용도 |
| :--- | :--- | :--- |
| 메모리 읽기 | `/core/read8?address=0xXXXX` | 특정 RAM 주소의 1바이트 값을 읽습니다. |
| 메모리 범위 | `/core/readrange?address=0xXXXX&length=N` | 특정 주소부터 N바이트만큼의 배열을 읽습니다. |
| 버튼 입력 | `/mgba-http/button/tap?button=A` | 지정한 버튼을 한 번 누릅니다. |
| 버튼 홀드 | `/mgba-http/button/hold?button=A&duration=16` | 지정한 프레임 동안 버튼을 누르고 있습니다. |
| 스크린샷 | `/core/screenshot?path=xxx.png` | 현재 게임 화면을 이미지 파일로 저장합니다. |
| 세이브 | `/core/savestateslot?slot=N` | 지정한 슬롯에 게임 상태를 저장합니다. |
| 로드 | `/core/loadstateslot?slot=N` | 지정한 슬롯의 게임 상태를 불러옵니다. |
| 게임 정보 | `/core/getgametitle` | 현재 실행 중인 ROM의 타이틀을 반환합니다. |

### 5. 연결 검증 방법
Python 스크립트를 사용하여 API 서버와 에뮬레이터 간의 연결을 검증할 수 있습니다.
```python
import urllib.request

endpoints = [
    '/core/currentframe',
    '/core/getgamecode',
    '/core/getgametitle',
    '/mgba-http/button/getall'
]

for path in endpoints:
    try:
        with urllib.request.urlopen('http://127.0.0.1:5000' + path, timeout=2) as r:
            print(path, r.status, r.read(200).decode('utf-8', 'replace'))
    except Exception as e:
        print(path, "연결 실패:", e)
```

### 6. Grokemon .env 설정 예시
```ini
MGBA_HTTP_BASE_URL=http://127.0.0.1:5001
POKEMON_VERSION=red
HARNESS_MODE=full-game
OPENAI_BASE_URL=https://api.x.ai/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=grok-4.3
OPENAI_TEMPERATURE=0.2
```

### 7. 고속 실행 설정 (config.ini)
mGBA의 실행 속도를 높이려면 `config.ini` 파일을 다음과 같이 수정합니다.
```ini
fpsTarget=640
audioSync=0
videoSync=0
fastForwardRatio=-1
mute=1
```

---

## B. PyBoy 방식 (PokemonRedExperiments)

Python 환경에서 PyBoy 에뮬레이터를 라이브러리로 직접 호출하여 강화학습을 수행하는 방식입니다.

### 1. 필요 소프트웨어
* Python 3.10 버전 이상
* ffmpeg (시스템 환경 변수 PATH에 등록 필수)
* 합법적으로 취득한 포켓몬스터 레드 ROM 파일 (`PokemonRed.gb`)
  * SHA1 해시값: `ea9bcae617fdf159b045185467ae58b2e4a48b9a`

### 2. 패키지 설치 (V2 버전 권장)
`v2` 디렉토리로 이동하여 필요한 라이브러리를 설치합니다.
```bash
cd v2
pip install -r requirements.txt
```
`requirements.txt` 파일에는 아래 패키지들이 포함되어 있습니다.
* PyBoy==2.4.0
* stable-baselines3==2.3.2
* torch==2.5.0
* websockets==13.1

macOS 사용자는 전용 요구사항 파일을 사용합니다.
```bash
pip install -r macos_requirements.txt
```

### 3. PyBoy API 사용 예시
Python 코드에서 에뮬레이터를 직접 제어하는 방법입니다.
```python
from pyboy import PyBoy

# 헤드리스 모드로 에뮬레이터 초기화
pyboy = PyBoy("PokemonRed.gb", window_type='headless')
pyboy.tick()

# RAM 주소에서 직접 데이터 읽기
y_coord = pyboy.memory[0xD361]
x_coord = pyboy.memory[0xD362]
map_id = pyboy.memory[0xD35E]

# 버튼 입력 전달 및 프레임 진행
pyboy.button('a')
pyboy.button('down')
pyboy.tick()

# 화면 캡처
image = pyboy.screen.image  # PIL Image 객체 반환
ndarray = pyboy.screen.ndarray  # NumPy 배열 반환 (144, 160, 4) RGBA

# 충돌 데이터 포인터 계산
collision_ptr = pyboy.memory[0xD530] + (pyboy.memory[0xD531] << 8)
```

### 4. 훈련 및 실행 명령어

#### 강화학습 훈련 시작
```bash
python baseline_fast_v2.py
```

#### 사전훈련된 모델 실행 (인터랙티브 모드)
```bash
python run_pretrained_interactive.py
```
* 키보드 방향키와 X(A 버튼), Z(B 버튼) 키로 직접 조작할 수 있습니다.
* `agent_enabled.txt` 파일을 편집하여 AI의 자동 플레이를 일시정지할 수 있습니다.

#### TensorBoard 모니터링
학습 진행 상황을 시각적으로 확인하려면 아래 명령어를 실행합니다.
```bash
tensorboard --logdir .
```
웹 브라우저에서 `http://localhost:6006` 주소로 접속하여 모니터링합니다.

---

## C. 에뮬레이터 비교 및 선택 가이드

| 비교 항목 | mGBA-http 방식 | PyBoy 방식 |
| :--- | :--- | :--- |
| 설치 복잡도 | 높음 (에뮬레이터, 프록시, Lua 스크립트 필요) | 낮음 (pip 패키지 설치로 완료) |
| 실행 속도 | 네트워크 통신 레이턴시로 인해 상대적으로 느림 | 최대 344배속 실시간 실행 가능으로 매우 빠름 |
| 프레임 정밀도 | 네트워크 지연으로 인해 프레임 단위 제어가 불안정함 | 프레임 단위로 정확하게 제어 가능 |
| 병렬 인스턴스 | MCP 서버를 통한 별도 제어 필요 | SubprocVecEnv를 사용하여 내장 병렬화 지원 |
| GBA 지원 여부 | 지원함 (mGBA 기반) | 지원하지 않음 (GB 및 GBC 타이틀만 지원) |
| API 스타일 | HTTP REST API 방식 | Python 라이브러리 직접 호출 방식 |
| 디버깅 도구 | Swagger UI 제공 | Python REPL을 통한 실시간 디버깅 |

---

## D. 트러블슈팅 및 문제 해결

### 1. mGBA-http 관련 문제

* **mGBA 실행 즉시 종료되는 현상**
  * 원인: 에뮬레이터 실행 시 `--script` CLI 옵션을 사용했기 때문입니다.
  * 해결책: 해당 옵션을 제거하고 에뮬레이터를 실행한 뒤, GUI 메뉴를 통해 Lua 스크립트를 수동으로 로드해야 합니다.

* **5000번 포트에서 200 응답이 오지 않는 현상**
  * 원인: 8888번 포트가 열려 있지 않거나 Lua 스크립트가 로드되지 않았습니다.
  * 해결책: mGBA 내부에서 Lua 스크립트가 정상적으로 실행 중인지 확인합니다. 콘솔에 리스닝 메시지가 출력되었는지 점검합니다.

* **mGBA 에뮬레이터가 크래시되는 현상**
  * 원인: Lua 스크립트를 중복으로 로드했거나 코드 내부에서 dofile() 함수를 호출했습니다.
  * 해결책: 에뮬레이터를 완전히 종료한 후 재실행하고, Lua 스크립트는 GUI 메뉴를 통해 단 한 번만 로드합니다.

* **HTTP 500 에러 발생**
  * 원인: Lua 스크립트가 로드되지 않은 상태에서 mGBA-http 서버로 요청이 전송되었습니다.
  * 해결책: 에뮬레이터에서 Lua 스크립트를 먼저 로드한 뒤 API 요청을 보냅니다.

* **ECONNREFUSED 에러 발생**
  * 원인: mGBA-http 프록시 서버가 실행되지 않았습니다.
  * 해결책: `mGBA-http.exe` 파일이 정상적으로 실행 중인지 확인합니다.

### 2. PyBoy 관련 문제

* **ImportError: pyboy 에러 발생**
  * 원인: 가상환경에 PyBoy 패키지가 설치되지 않았습니다.
  * 해결책: `pip install pyboy` 명령어로 패키지를 설치합니다.

* **ROM 파일을 찾을 수 없다는 에러 (ROM not found)**
  * 원인: 실행 경로에 `PokemonRed.gb` 파일이 존재하지 않습니다.
  * 해결책: 현재 작업 디렉토리에 ROM 파일이 올바른 이름으로 존재하는지 확인합니다.

* **SDL2 관련 에러 발생**
  * 원인: GUI 화면을 그리기 위한 SDL2 라이브러리가 시스템에 설치되지 않았습니다.
  * 해결책: 코드 초기화 시 `window_type='headless'` 옵션을 사용하여 화면 없이 실행하거나, 시스템에 SDL2 라이브러리를 설치합니다.

* **CUDA 메모리 부족 에러 (CUDA OOM)**
  * 원인: 병렬 환경 개수가 너무 많거나 배치 크기가 그래픽 카드의 메모리 용량을 초과했습니다.
  * 해결책: `num_cpu` 값을 줄이거나 배치 크기 설정을 축소합니다.

---

## E. POPOPOPOket 핵심 함정 및 주의사항 (Pitfalls)

프로젝트 진행 중 발생한 치명적인 오류들과 이를 방지하기 위한 규칙입니다.

1. **한글 경로 포함 시 Lua 로드 실패**
   * 윈도우 사용자 계정명이나 상위 폴더 이름에 한글이 포함되어 있으면 Lua 스크립트가 정상적으로 로드되지 않습니다.
   * 해결책: Lua 스크립트 파일을 영문으로만 구성된 ASCII 경로(예: `C:\temp\`)로 복사한 뒤 로드합니다.

2. **원본 이미지 오염 금지**
   * LLM의 비전 인식을 돕기 위해 화면 이미지 위에 좌표 그리드나 텍스트를 직접 겹쳐서 그리면 안 됩니다.
   * 해결책: 원본 화면 이미지와 가이드 라인이 그려진 이미지를 철저히 분리하여 모델에 전달해야 합니다.

3. **이진 마스킹 사용 금지**
   * 통과 가능한 길과 벽만 구분하는 이진 마스킹을 사용하면 캐릭터가 풀숲을 벽으로 오인하여 우회하는 문제가 발생합니다.
   * 해결책: 빈 공간(green), 풀숲(yellow), 벽(red)의 3단계로 구분된 마스킹을 적용해야 합니다.

4. **과도한 토큰 최적화로 인한 컨텍스트 누락**
   * API 비용을 줄이기 위해 프롬프트에서 이전 행동 기록이나 메모리 정보를 과도하게 생략하면 에이전트가 무한 루프에 빠집니다.
   * 해결책: 비용과 성능의 균형을 맞추고, stuck-memory 정보를 프롬프트에 반드시 포함해야 합니다.

5. **ROM 버전 혼용 금지**
   * 포켓몬스터 레드 버전의 메모리 주소 맵을 골드나 실버 등 다른 버전에 그대로 적용하면 엉뚱한 메모리 값을 읽어와 오작동을 일으킵니다.
   * 해결책: 사용하는 ROM 파일의 버전과 메모리 주소 정의가 일치하는지 항상 검증합니다.

6. **원클릭 런처 사용 시 포트 검증**
   * `launch-pokemon.ps1` 스크립트를 사용하여 환경을 일괄 실행할 때, 이전 프로세스가 종료되지 않아 포트 충돌이 발생할 수 있습니다.
   * 해결책: 스크립트 실행 전에 8888번과 5000번 포트가 사용 중인지 확인하고 기존 프로세스를 정리해야 합니다.
