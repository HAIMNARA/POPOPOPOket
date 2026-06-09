# 12 - 플레이테스트 로그: PyBoy 자동화 실전 기록

> 2026-06-09 실행. PyBoy 1.6.9 + Python 3.12 + Pokemon Red ROM으로
> 타이틀 화면부터 Viridian City까지 자동 플레이를 시도하며 발견한 버그, 오류, 막힘 지점과 해결 방안.

---

## 환경 정보

| 항목 | 값 |
|------|-----|
| 에뮬레이터 | PyBoy 1.6.9 (headless 모드) |
| Python | 3.12.10 |
| ROM | Pokemon - Red Version.gb |
| OS | Windows 11 |
| 실행 방식 | 결정론적 휴리스틱 (LLM API 미사용) |

---

## v1 실행: API 호환 문제

### 발견된 버그

**BUG-001: `get_screen_image()` 메서드 미존재**
- 증상: `AttributeError: 'pyboy.pyboy.PyBoy' object has no attribute 'get_screen_image'`
- 원인: PyBoy 1.6.9에서는 `screen_image()` (get_ 접두사 없음)
- 해결: `self.pyboy.get_screen_image()` -> `self.pyboy.screen_image()`
- 교훈: PyBoy 버전별 API 차이 확인 필수. 1.6.9 vs 2.4.0 API가 다름.

**BUG-002: Pillow DeprecationWarning**
- 증상: `'mode' parameter is deprecated and will be removed in Pillow 13`
- 원인: PyBoy 1.6.9의 screen_image()가 구버전 Pillow API 사용
- 영향: 기능에 문제 없음 (경고만)
- 해결: 무시 가능. Pillow 13 이전까지 문제 없음.

### v1 결과
- 스크린샷 1장도 못 찍고 크래시
- 게임 상태: map=0 y=0 x=0 (타이틀 화면)

---

## v2 실행: joyIgnore 게이트 문제

### 발견된 버그

**BUG-003: joyIgnore(0xCDCB) = 172 영구 고정**
- 증상: 모든 로그에서 `joyIgnore=172` (한 번도 0이 되지 않음)
- 원인 후보:
  1. 0xCDCB가 이 ROM 버전에서 wJoyIgnore 주소가 아닐 수 있음
  2. 인트로 컷신이 완전히 종료되지 않아 입력 잠금 지속
  3. 172(0xAC)가 비트필드로 특정 버튼만 잠금하는 것일 수 있음
- 검증: joyIgnore=172임에도 불구하고 플레이어 이동은 실제로 작동함 (y=6->7)
- 해결: **joyIgnore 게이트 완전 제거**. rWY와 walkCounter만 사용.
- 교훈: RAM 주소는 ROM 버전/리비전에 따라 다를 수 있음. 실측 검증 필수.

**BUG-004: 맵 ID 상수 뒤바뀜**
- 증상: `MAP_REDS_HOUSE_2F=37`로 설정했으나 실제 침실은 map=38
- 원인: pokered 디스어셈블리 해석 오류
- 실측:
  - map=37 = Red's House 1F
  - map=38 = Red's House 2F (침실)
- 해결: 상수 교정
- 교훈: RAM에서 읽은 값으로 실측 검증 후 상수 확정할 것.

**BUG-005: 대화창(rWY) 영구 감지**
- 증상: v2에서 rWY=0이 지속되어 모든 단계에서 "Dialog detected" 반복
- 원인: 인트로 종료 후 마지막 대화("...Okay! It's time to go!")가 해제되지 않음
- 해결: 2000프레임 대기 후 clear_dialog() 호출로 해결 (v3에서 확인)

### v2 결과
- 침실 도착 성공 (map=38, y=6, x=3)
- 이동 가능 확인 (y=6->7)
- 하지만 침실 탈출 실패, 대화 무한 감지

---

## v3 실행: 침실 계단 위치 발견

### 핵심 발견

**FINDING-001: 침실 계단은 위쪽(y=1-2, x=6-7)에 위치**
- v3에서 플레이어가 위로 이동 후 map 37/38 반복 전환 발견
- 로그 증거: `Step 0: m=38 y=1 x=7 -> m=37 y=1 x=7` (맵 전환!)
- 침실 바닥(y=7)에서는 x=1~5만 이동 가능 (가구가 x=6-7 차단)
- 침실 위쪽(y=1-3)에서는 x=6-7 접근 가능 (계단 영역)

**FINDING-002: 침실 이동 가능 영역 매핑**
```
침실(map=38) 이동 가능 좌표:
  y=1: x=? ~ x=7  (계단 영역 포함)
  y=2: x=? ~ x=7
  y=3~5: x=? ~ x=5 (추정)
  y=6: x=3 (스폰), x=? ~ x=?
  y=7: x=1 ~ x=5  (바닥, 계단 접근 불가)
```

**FINDING-003: 인트로 완료 조건**
- 타이틀 대기: 2000프레임 (800프레임은 부족 - 저작권 화면에서 멈춤)
- 인트로 A 스팸 후 2000프레임 추가 대기 필요 (컷신/애니메이션 완료)
- `clear_dialog()`로 마지막 대화 1건 해제 -> rWY=144 (성공)

**FINDING-004: 대화 해제 프로토콜**
- rWY < 144 = 대화창 표시 중
- rWY >= 144 = 대화 없음
- A 버튼으로 대화 진행, B 버튼으로 메뉴 취소 (폴백)
- 최대 60회 A + 10회 B로 모든 대화/메뉴 해제 가능

### v3 버그

**BUG-006: 침실 바닥 스캔 전략 실패**
- 증상: y=7 바닥줄을 x=1~5 전체 스캔했으나 맵 전환 없음
- 원인: 계단이 바닥이 아닌 위쪽에 위치 (FINDING-001)
- 해결: v4에서 "위로 먼저, 그다음 오른쪽" 전략으로 변경

### v3 결과
- rWY=144 달성 (대화 해제 성공)
- 침실 이동 가능 영역 매핑 완료
- 계단 위치 추정 (y=1-2, x=6-7)
- map 37/38 전환 확인 (계단 작동 검증)

---

## v4 실행: 10분 타임아웃

### 변경 사항
- 침실: "위로 5칸 -> 오른쪽 5칸" 전략 적용
- joyIgnore 게이트 완전 제거
- 1F 탈출: 계단 재진입 방지 (왼쪽 이동 후 아래로)
- Route 1: 500스텝으로 확장

### 결과
- 10분(600초) 타임아웃으로 결과 파일 미생성
- 스크린샷 6장 생성 (인트로/침실/랩 시작)
- 침실에서 "bed_stuck" 스크린샷 존재 -> 계단 여전히 미발견

### 미해결 문제

**BUG-007: 침실 계단 정확한 경로 미확보**
- 증상: UP+RIGHT 전략으로도 map 전환 안됨 (bed_stuck)
- 추정 원인: 계단 타일이 특정 방향에서만 진입 가능하거나, 워프 좌표가 예상과 다름
- 시도 필요:
  1. pokered 디스어셈블리에서 REDS_HOUSE_2F 워프 데이터 확인
  2. 모든 좌표를 순회하는 brute-force 탐색
  3. PyBoy game_wrapper 활용 (Pokemon Gen1 래퍼 존재 시)
  4. 세이브 스테이트 생성으로 인트로 스킵 (PokemonRedExperiments 방식)

---

## 통합 교훈

### API/환경 교훈
1. PyBoy 버전별 API 차이 (1.6.9 vs 2.4.0): `screen_image()` vs `get_screen_image()`, `get_memory_value()` vs `memory[]`
2. Pillow 호환: v13에서 `mode` 파라미터 제거 예정
3. headless 모드에서 프레임 속도 제한 불가 (경고 무시)

### RAM 주소 교훈
4. joyIgnore(0xCDCB)는 이 ROM에서 항상 172 - 입력 게이트로 사용 불가
5. rWY(0xFF4A)가 가장 신뢰할 수 있는 대화 감지 신호
6. walkCounter(0xD00D)로 이동 애니메이션 완료 감지 가능
7. 맵 ID는 실측 검증 필수 (문서와 실제 값이 다를 수 있음)

### 게임 진행 교훈
8. 타이틀 화면: 최소 2000프레임 대기 필요 (800은 저작권 화면)
9. 인트로 후 2000프레임 추가 대기로 컷신 완전 종료
10. 침실 계단은 바닥이 아닌 위쪽/오른쪽에 위치 (직감과 반대)
11. 가구가 바닥줄에서 계단 영역 접근을 차단 (위에서 우회 필요)
12. map 37/38 전환은 특정 좌표(y=1-2, x=6-7)에서 발생 확인

### 자동화 설계 교훈
13. "명확해 보이는 것도 실측하라": 맵 상수, RAM 주소, 계단 위치 모두 예상과 달랐음
14. 스크린샷 기반 디버깅이 로그보다 빠를 수 있음
15. 단계별 진행 (인트로 -> 침실 -> 1F -> ...) + 각 단계 검증이 한꺼번에 실행보다 안전

---

## 다음 단계 (재시작 시 참고)

### 즉시 해결 필요
1. 침실 계단 워프 좌표 정확히 확인 (pokered 소스 또는 brute-force)
2. 세이브 스테이트 활용으로 인트로 스킵 검토
3. PyBoy Pokemon Gen1 game_wrapper 존재 시 `start_game()` 메서드 활용

### 침실 탈출 후 예상 흐름
```
침실(2F) --계단--> 1F --문--> Pallet Town --남쪽--> Oak 이벤트
  ---> Oak's Lab --포켓볼--> 스타터 획득 --라이벌 배틀--> 승리
  ---> Route 1 --북진--> Viridian City (목표)
```

### 재시작 체크리스트
- [ ] ROM 파일 경로 확인: `C:\Users\하미\Downloads\Pokemon - Red Version.gb`
- [ ] PyBoy 설치 확인: `pip show pyboy`
- [ ] 스크립트 위치: `automation/play.py`
- [ ] 실행: `python automation/play.py`
- [ ] 결과 확인: `automation/runs/<timestamp>/` (events.json, bugs.json, ss/)
