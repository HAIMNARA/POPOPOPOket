# 05 - 보상 설계 및 진행도 감지

이 문서는 PokemonRedExperiments 프로젝트의 강화학습(RL) 보상 설계와 Grokemon 및 POPOPOPOket 프로젝트의 LLM 진행도 감지 시스템을 상세히 다룹니다.

## A. RL 보상 설계 (PokemonRedExperiments)

강화학습 에이전트가 포켓몬스터 레드 게임을 효과적으로 탐색하고 학습하도록 돕기 위해 보상 함수(Reward Function)를 설계했습니다. 초기 버전인 V1에서 개선된 V2로 전환하면서 학습 효율이 크게 향상되었습니다.

### V1 보상 구조

V1에서는 다음과 같은 상태 점수(state_scores)를 기반으로 보상을 계산했습니다.

```python
state_scores = {
    'event': reward_scale * update_max_event_rew(),        # 이벤트 플래그
    'level': reward_scale * get_levels_reward(),            # 포켓몬 레벨
    'heal': reward_scale * total_healing_rew,               # 힐링 보너스
    'op_lvl': reward_scale * update_max_op_level() * 0.2,  # 상대 레벨
    'dead': reward_scale * -0.1 * died_count,               # 사망 페널티
    'badge': reward_scale * get_badges() * 5,               # 배지 보너스
    'explore': reward_scale * get_knn_reward()              # KNN 탐색
}
# reward_scale=4, explore_weight=3
```

### V2 보상 구조 (개선)

V2에서는 불필요한 보상 요소를 제거하고 핵심적인 탐색 및 이벤트 보상의 가중치를 대폭 높였습니다.

```python
state_scores = {
    'event': reward_scale * update_max_event_rew() * 4,                    # 이벤트 (4배)
    'heal': reward_scale * total_healing_rew * 10,                          # 힐링 (10배)
    'badge': reward_scale * get_badges() * 10,                              # 배지 (10배)
    'explore': reward_scale * explore_weight * len(seen_coords) * 0.1,     # 좌표 탐색
    'stuck': reward_scale * get_current_coord_count_reward() * -0.05       # 정체 페널티
}
# reward_scale=0.5, explore_weight=0.25
```

### 보상 컴포넌트 상세

#### 1. 이벤트 보상 (event)
- **RAM 주소 범위**: V2는 0xD747부터 0xD886까지의 영역을 감시합니다. V1은 0xD747부터 0xD7F6까지의 영역만 감시했습니다.
- **계산 방식**: 이벤트 플래그 바이트에서 1로 설정된 비트(set bit)의 개수를 카운트합니다.
- **제외 대상**: 박물관 티켓 플래그(0xD754, bit 0)는 보상 계산에서 제외합니다.
- **기본 이벤트 차감**: 게임 시작 시 기본적으로 설정되어 있는 13개의 플래그는 계산에서 차감합니다.

#### 2. 레벨 보상 (level) - V1 전용
- **RAM 주소**: 0xD18C, 0xD1B8, 0xD1E4, 0xD210, 0xD23C, 0xD268 (파티 포켓몬 6마리의 레벨 주소)
- **계산 방식**: 파티에 속한 포켓몬 6마리의 레벨 합산에서 포켓몬당 2를 빼고, 스타터 포켓몬 보너스 4를 추가로 차감합니다.
- **임계값**: 레벨 합산이 22 이하일 때는 선형적으로 보상을 부여합니다. 22레벨을 초과하면 초과분에 대해 4로 나눈 값을 적용하여 스케일링합니다. V2에서는 이 보상이 제거되었습니다.

#### 3. 힐링 보상 (heal)
- **계산 방식**: 파티 크기가 동일하게 유지되는 상황에서 HP 비율이 증가하는 것을 추적합니다.
- **V1 공식**: `heal_amount * 4`
- **V2 공식**: `heal_amount` 값을 제곱하여 적용합니다. (`heal_amount^2`)
- **초기화**: 에이전트가 사망하면 누적된 힐링 보상은 리셋됩니다.

#### 4. 배지 보상 (badge)
- **RAM 주소**: 0xD356 (배지 획득 상태 비트필드)
- **계산 방식**: 획득한 배지 비트의 개수를 카운트합니다.
- **V1 공식**: `badges * 5`
- **V2 공식**: `badges * 10`

#### 5. 탐색 보상 (explore)
- **V1 KNN 방식**: HNSWLIB 인덱스를 사용합니다. 차원은 4320이며, L2 거리가 2,000,000보다 크면 유니크한 프레임으로 판정합니다.
  - **레벨 22 이전 (pre-reward)**: `base_explore * 0.005`
  - **레벨 22 이후 (post-reward)**: `cur_size * 0.01`
- **V2 좌표 방식**: `(x, y, map_n)` 튜플을 키로 하는 딕셔너리를 사용합니다.
  - **공식**: `len(seen_coords) * 0.1`

#### 6. 정체 페널티 (stuck) - V2 전용
- **계산 방식**: 특정 좌표를 방문한 횟수가 600회를 초과하면 `-0.05`의 페널티를 부여합니다.

### V1과 V2 변화 요약

| 요소 | V1 | V2 |
| :--- | :--- | :--- |
| 탐색 방식 | KNN (4320차원) | 좌표 카운팅 |
| 레벨 보상 | 포함 | 제거 |
| 상대 레벨 보상 | 포함 (x0.2) | 제거 |
| 사망 페널티 | -0.1 | 제거 (힐링 리셋으로 대체) |
| 이벤트 가중치 | x1 | x4 |
| 배지 가중치 | x5 | x10 |
| 힐링 가중치 | x1 | x10 |
| 정체 페널티 | 없음 | -0.05 |

---

## B. LLM 진행도 감지 (Grokemon)

Grokemon 프로젝트는 LLM 에이전트의 게임 진행 상황을 모니터링하기 위해 `FullGameDetector`를 사용합니다. 이 모듈은 약 292줄의 코드로 구현되어 있으며, 총 9단계의 체크포인트를 통해 게임 완료 여부를 추적합니다.

### 9단계 체크포인트

1. **initialObserved**: 게임 상태 데이터를 성공적으로 읽기 시작한 단계입니다.
2. **starterAcquired**: 파티 포켓몬 수가 0보다 커져 스타터 포켓몬을 획득했음을 확인한 단계입니다.
3. **rivalBattleEntered**: 라이벌과의 배틀에 진입한 단계입니다. 특정 배틀 유형 플래그를 통해 감지합니다.
4. **rivalBattleExited**: 라이벌 배틀이 종료된 단계입니다.
5. **badgesObserved**: 획득한 배지 수가 0보다 큰 상태를 관측한 단계입니다.
6. **allBadgesObtained**: 8개의 배지를 모두 획득한 단계입니다.
7. **hallOfFameObserved**: 명예의 전당 맵(ID: 0x76)에 진입한 단계입니다.
8. **hallOfFameCompleted**: 명예의 전당 등록 완료 플래그가 활성화된 단계입니다.
9. **completed**: 최종적으로 게임 클리어 상태에 도달한 단계입니다.

### 각 체크포인트의 검증 방법

- **progressStep**: 에이전트가 도달한 마지막 진행 단계를 나타냅니다.
- **checkpointEvidence**: 각 체크포인트가 달성되었음을 증명하는 데이터 기록 배열입니다.
- **lastObserved**: 가장 최근에 관측된 게임 상태 필드들을 저장합니다.

---

## C. LLM 마일스톤 시스템 (POPOPOPOket)

POPOPOPOket 프로젝트는 LLM 에이전트의 세밀한 행동 진행도를 평가하기 위해 9단계 마일스톤 시스템을 운영합니다.

### 9단계 마일스톤 정의

| 순위 | ID | 의미 |
| :--- | :--- | :--- |
| 0 | title-menu-handled | 타이틀 화면 및 메뉴 조작 완료 |
| 1 | new-game-started-or-resumed | 새 게임 시작 또는 기존 게임 이어하기 |
| 2 | player-control-reached | 플레이어가 캐릭터를 직접 조작할 수 있는 상태 도달 |
| 3 | first-map-transition | 최초로 다른 맵으로 전환 성공 |
| 4 | first-dialogue-completed | 최초로 NPC와의 대화 완료 |
| 5 | first-battle-detected | 최초로 전투 상황 감지 |
| 6 | first-battle-completed | 최초로 전투 완료 |
| 7 | first-pokemon-obtained | 최초로 포켓몬 획득 |
| 8 | viridian-city-reached | 최종 목표인 비리디안 시티 도달 |

### 마일스톤 판정 로직 (우선순위 순서)

마일스톤은 다음 우선순위에 따라 판정됩니다. 조건이 충족되는 가장 높은 순위의 마일스톤이 현재 상태로 결정됩니다.

1. **RAM 데이터 미사용 또는 null**: 판정을 보류하고 null을 반환합니다.
2. **mapId가 0x01인 경우**: `viridian-city-reached`로 판정합니다. 이는 시스템 내에서 가장 높은 우선순위를 가집니다.
3. **배틀이 진행 중인 경우**: `first-battle-detected`로 판정합니다.
4. **배틀이 종료된 직후인 경우**: `first-battle-completed`로 판정합니다.
5. **대화가 완료된 직후인 경우**: `first-dialogue-completed`로 판정합니다.
6. **맵 전환이 발생한 경우**: `first-map-transition`로 판정합니다.
7. **플레이어 조작이 가능한 상태인 경우**: `player-control-reached`로 판정합니다.
8. **메뉴 화면이 활성화된 경우**: `title-menu-handled`로 판정합니다.
9. **기타 상황**: `new-game-started-or-resumed`로 판정합니다.

### 주의 사항: Viridian City와 mapId 0x01 충돌 문제

- **충돌 원인**: 비리디안 시티의 맵 ID는 `0x01`입니다. 만약 첫 맵 전환 테스트를 수행할 때 테스트 환경에서 `mapId`를 `1`로 설정하면, 시스템은 이를 비리디안 시티 도달로 오인하여 `viridian-city-reached` 마일스톤을 잘못 판정하게 됩니다.
- **해결 방안**: 첫 맵 전환 테스트를 설계할 때는 `mapId`를 `2` 이상의 값으로 설정하여 충돌을 방지해야 합니다.
