# 02 · 환경 셋업

목표: "이미 실행 중인 mGBA"에 LLM 하네스를 붙여 자동 플레이를 시작할 수 있는 상태로 만든다.

---

## 1. 사전 요구사항

- **Node.js 20+**, **pnpm 11.2.2**
- **mGBA 0.10.x** (`C:\Program Files\mGBA\mGBA.exe` 기본 경로 가정)
- **mGBA-http** 실행 파일 (`.local-tools/mgba-http/mGBA-http.exe`)
- **mGBASocketServer.lua** (`.local-tools/mgba-http/mGBASocketServer.lua`)
- **합법적으로 취득한 포켓몬 레드 ROM** (`Pokemon - Red Version.gb`)

> ROM은 본인 카트리지 덤프 또는 합법 경로로 확보해야 한다. 저작권 자료는 이 저장소에 포함하지 않는다.

---

## 2. 설정 파일

`.env.example` 를 `.env` 로 복사 후 로컬 에뮬레이터/모델 설정:

```bash
MGBA_HTTP_BASE_URL=http://127.0.0.1:5000
AI_BASE_URL=https://<your-openai-compatible-endpoint>/v1
AI_API_KEY=<your-key>
AI_MODEL=<model-id>
METRICS_HTTP_HOST=0.0.0.0
METRICS_HTTP_PORT=9464
```

의존성 설치:

```bash
pnpm install
```

---

## 3. 구동 순서 (중요)

순서가 어긋나면 연결이 안 된다. 아래 순서를 지킬 것.

### (1) mGBA를 ROM과 함께 실행

```powershell
& "C:\Program Files\mGBA\mGBA.exe" "C:\Users\<user>\Downloads\Pokemon - Red Version.gb"
```

창 제목이 `mGBA - POKEMON RED - 0.10.5` 처럼 떠야 ROM 로드 성공.

### (2) Lua 소켓 서버를 GUI로 "한 번만" 로드

> 🚨 **mGBA 0.10.x에는 `--script` CLI 옵션이 없다.** `mgba --script <lua> <rom>` 는
> `unknown option -- script` 에러 후 **즉시 종료**된다. 반드시 GUI로 로드한다.

1. mGBA 메뉴: **Tools → Scripting → File → Load script**
2. `.local-tools/mgba-http/mGBASocketServer.lua` 선택
3. 스크립팅 콘솔에 다음이 떠야 정상:
   ```
   mGBA script server 0.8.2 ready. Listening on port 8888
   ```

**금지 사항**
- 스크립팅 콘솔에서 `dofile([[...]])` 로 로드하지 말 것.
- **두 번 이상 로드하지 말 것.** 둘 다 관리되지 않는 소켓/프레임 콜백을 만들어 mGBA를 크래시(use-after-free)시킨다.

### (3) mGBA-http 실행

```powershell
& ".local-tools\mgba-http\mGBA-http.exe"
```

`http://127.0.0.1:5000` 가 200을 응답하면 브리지 준비 완료.

### (4) 하네스 실행

```bash
pnpm dev
```

`:5000` 이 200을 응답한 뒤부터 에이전트가 매 턴 자동으로 한 액션씩 실행한다.

---

## 4. 자동화 런처 (`start-harness.ps1`)

위 (1)·(3)·(4)와 mGBA 설정 튜닝을 한 스크립트가 처리한다.
**단, (2) Lua GUI 로드만은 사람이 한 번 해줘야 한다.**

스크립트가 하는 일:

1. mGBA / mGBA-http / Lua / ROM / `.env`(특히 `AI_API_KEY` 비어있지 않은지) 존재 검증.
2. mGBA `config.ini` 에 고속 실행용 설정 주입:
   - `fpsTarget=640`, `audioSync=0`, `videoSync=0`, `fastForwardRatio=-1`, `mute=1`
3. mGBA를 ROM과 함께 실행(약 3초 대기).
4. mGBA-http 실행.
5. **ACTION REQUIRED** 안내 출력 → 사용자가 GUI로 Lua 로드.
6. `:5000` 을 최대 180초 폴링. `:8888`(Lua) 바인딩 여부로 원인 진단.
7. 준비되면 `pnpm dev` 실행, 종료 시 mGBA/mGBA-http 정리.

```powershell
pwsh ./start-harness.ps1
# 또는 ROM 경로 지정
pwsh ./start-harness.ps1 -Rom "D:\roms\Pokemon - Red Version.gb"
```

---

## 5. 연결 점검 (라이브 실행 전)

`:5000` 이 핵심 엔드포인트에 응답하는지 확인:

```python
import urllib.request
for path in ['/core/currentframe','/core/getgamecode','/core/getgametitle','/mgba-http/button/getall']:
    with urllib.request.urlopen('http://127.0.0.1:5000'+path, timeout=2) as r:
        print(path, r.status, r.read(200).decode('utf-8','replace'))
```

`/core/getgametitle` 에서 `200` 과 `POKEMON RED` 가 나오면 체인 정상.

PowerShell 한 줄 점검:

```powershell
(Invoke-WebRequest "http://localhost:5000/core/getgametitle" -UseBasicParsing).Content
```

---

## 6. 검증 가드레일 (코드 변경 시)

```bash
pnpm typecheck && pnpm test && pnpm build && pnpm check
```

5분 실험 창 예시:

```bash
MGBA_HTTP_BASE_URL=http://127.0.0.1:5000 pnpm dev > .omo/evidence/<task>-pnpm-dev.log 2>&1 & \
  PID=$!; sleep 300; kill -INT $PID; wait $PID || true
```

---

## 7. 관측 스택 (선택)

```bash
docker compose -f docker-compose.grafana.yml up -d
pnpm dev
```

Prometheus가 `host.docker.internal:9464` 를 스크랩, Grafana가 `pss-mgba Run Iterations`
대시보드를 `http://127.0.0.1:3000` 에 프로비저닝. 실험 동안 스택을 켜두면 각 `run_id` 가
별도 시계열로 보인다.

트레이스 뷰어:

```bash
pnpm web:build && pnpm viewer   # 기본 http://127.0.0.1:9474
```

---

다음: [03 · 공략 가이드](03-strategy-guide.md)
