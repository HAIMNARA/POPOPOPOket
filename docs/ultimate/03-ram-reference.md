# 03 - 통합 RAM 레퍼런스

이 문서는 Pokemon Red 프로젝트 3개에서 사용하는 RAM 주소를 정리한 참조 문서입니다. 각 주소는 16진수와 10진수 표기를 모두 포함합니다.

## 입력 안전 (Grokemon)

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| wJoyIgnore | 0xCDCB | 52683 (프롬프트 제공: 52587) | 입력 잠금 플래그 (0=안전, >0=잠금) | Grokemon (GK) |
| wWalkCounter | 0xD00D | 53261 (프롬프트 제공: 53189) | 걷기 애니메이션 카운터 (0=정지, >0=이동중) | Grokemon (GK) |
| rWY | 0xFF4A | 65354 | 윈도우 Y 레지스터 (144=숨김, <144=표시) | Grokemon (GK) |

## 플레이어 상태

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| wPlayerName | 0xD158-0xD162 | 53592-53602 | 플레이어 이름 (11바이트) | pret/pokered |
| wCurMap / wMapId | 0xD35E | 54110 | 현재 맵 ID | 3개 모두 |
| wYCoord | 0xD361 | 54113 | 플레이어 Y 좌표 | 3개 모두 |
| wXCoord | 0xD362 | 54114 | 플레이어 X 좌표 | 3개 모두 |
| wPlayerFacing | 0xC109 | 49417 | 방향 (0=아래, 4=위, 8=왼쪽, 12=오른쪽) | POPOPOPOket (PP) |
| wPartyCount | 0xD163 (RE) / 0xD2F3 (GK) | 53603 (RE) / 54003 (GK) | 파티 포켓몬 수 | RE + GK |
| wObtainedBadges | 0xD356 | 54102 | 배지 비트필드 (8비트) | 3개 모두 |

## 파티 포켓몬 (PokemonRedExperiments)

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| wPartyMons | 0xD164-0xD169 | 53604-53609 | 파티 포켓몬 종 ID (6마리) | PokemonRedExperiments (RE) |
| Pokemon 1 HP | 0xD16C (low) + 0xD16D (high) | 53612 (low) + 53613 (high) | HP (빅엔디안) | PokemonRedExperiments (RE) |
| Pokemon 1 Level | 0xD18C | 53644 | 레벨 | PokemonRedExperiments (RE) |
| Pokemon 2 Level | 0xD1B8 | 53688 | 레벨 | PokemonRedExperiments (RE) |
| Pokemon 3 Level | 0xD1E4 | 53732 | 레벨 | PokemonRedExperiments (RE) |
| Pokemon 4 Level | 0xD210 | 53776 | 레벨 | PokemonRedExperiments (RE) |
| Pokemon 5 Level | 0xD23C | 53820 | 레벨 | PokemonRedExperiments (RE) |
| Pokemon 6 Level | 0xD268 | 53864 | 레벨 | PokemonRedExperiments (RE) |
| HP Addresses | 0xD16C, 0xD198, 0xD1C4, 0xD1F0, 0xD21C, 0xD248 | 53612, 53656, 53700, 53744, 53788, 53832 | 6마리 HP | PokemonRedExperiments (RE) |
| Max HP | 0xD18D, 0xD1B9, 0xD1E5, 0xD211, 0xD23D, 0xD269 | 53645, 53689, 53733, 53777, 53821, 53865 | 6마리 최대 HP | PokemonRedExperiments (RE) |

## 배틀 상태

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| wIsInBattle | 0xD057 | 53335 | 배틀 플래그 (0=필드, >0=배틀) | 3개 모두 |
| wBattleType | 0xD05A | 53338 | 배틀 유형 (0=야생, 1=트레이너) | GK + PP |
| wBattleMonHP | 0xD015 | 53269 | 아군 포켓몬 HP | GK |
| wEnemyMonHP | 0xCFD6 | 53206 (프롬프트 제공: 53222) | 적 포켓몬 HP | GK |
| wBattleResult | 0xCFEB | 53227 (프롬프트 제공: 53003) | 배틀 결과 | GK + PP |
| wCurrentMenuItem | 0xCC26 | 52262 | 메뉴 커서 위치 | GK |
| Opponent Levels | 0xD8C5, 0xD8F1, 0xD91D, 0xD949, 0xD975, 0xD9A1 | 55493, 55537, 55581, 55625, 55669, 55713 | 적 6마리 레벨 | RE |

## 맵 & 타일

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| wTileMap | 0xC3A0 (360바이트) | 50080 | 화면 타일맵 (20x18) | GK |
| wTileInFrontOfPlayer | 0xD006 | 53254 | 플레이어 앞 타일 ID | GK |
| wTilePlayerStandingOn | 0xCFEE | 53230 | 서있는 타일 ID | GK |
| wGrassRate | 0xD827 | 55335 | 풀숲 조우율 | GK |
| COLLISION_PTR | 0xD530-0xD531 | 54576-54577 | 충돌 데이터 포인터 | RE (PyBoy) |
| TILESET_TYPE | 0xFFD7 | 65495 | 타일셋 유형 | RE (PyBoy) |

## 이벤트 플래그

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| wEventFlags | 0xD747-0xD886 | 55111-55430 | 이벤트 플래그 배열 (V2 전체) | RE |
| wEventFlags (V1) | 0xD747-0xD7F6 | 55111-55286 | 이벤트 플래그 배열 (V1 축소) | RE |
| wEventFlags (GK) | 0xD6E7 | 55015 | 이벤트 플래그 베이스 | GK |
| EVENT_GOT_POKEDEX | bit 37 | - | 도감 획득 | GK |
| EVENT_OAK_GOT_PARCEL | bit 56 | - | 소포 전달 | GK |
| MUSEUM_TICKET | 0xD754 bit 0 | 55124 bit 0 | 박물관 티켓 (제외) | RE |

## 스프라이트 & NPC 데이터 (pret/pokered)

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| Sprite State | 0xC100-0xC1FF | 49408-49663 | 스프라이트 상태 (16개 x 16바이트) | pret/pokered |
| Sprite ID | C1x0 | - | 스프라이트 ID | pret/pokered |
| Sprite Y/X Block | C1x4-C1x5 | - | Y/X 위치 (2x2 블록) | pret/pokered |
| Sprite Movement | C1x6 | - | 이동 바이트 (0xFF=정지, 0xFE=랜덤) | pret/pokered |
| Sprite Anim/Move | 0xC200-0xC2FF | 49664-49919 | 스프라이트 애니메이션/이동 | pret/pokered |
| Walk Anim Counter | C2x0 | - | 걷기 애니메이션 카운터 | pret/pokered |
| Sprite Y/X Tile | C2x4-C2x5 | - | Y/X 위치 (2x2 타일 그리드) | pret/pokered |

## 기타

| 심볼 | 16진수 주소 | 10진수 주소 | 용도 | 사용 프로젝트 |
|------|------------|------------|------|-------------|
| wTextBoxID | 0xD525 | 54565 | 활성 텍스트 박스 ID | pret/pokered |
| wLetterPrintingDelayFlags | 0xD348 | 54088 | 텍스트 출력 상태 | pret/pokered |
| wNamingScreenType | 0xD375 | 54133 | 이름 입력 화면 유형 | pret/pokered |
| MONEY | 0xD347-0xD349 | 54087-54089 | 소지금 (3바이트 BCD) | pret/pokered |
| wPokedexOwned | 0xD2E7 (19바이트) | 53991 | 도감 소유 (151 포켓몬) | pret/pokered |
| wPokedexSeen | 0xD2FA (19바이트) | 54010 | 도감 목격 | pret/pokered |

## 방향 코드 (playerFacing)

| 코드 | 방향 |
|------|------|
| 0 | 아래 (down) |
| 4 | 위 (up) |
| 8 | 왼쪽 (left) |
| 12 | 오른쪽 (right) |

## 주요 맵 ID

| mapId | 위치 | 비고 |
|-------|------|------|
| 0x00 | Pallet Town | 시작 마을 |
| 0x01 | Viridian City | 목표 마일스톤 |
| 0x0C | Route 1 | 결정론적 자동 북진 구간 |
| 0x76 | Hall of Fame | 게임 완료 |

## PyBoy 사용 예시

```python
from pyboy import PyBoy
pyboy = PyBoy("PokemonRed.gb")
y = pyboy.memory[0xD361]
x = pyboy.memory[0xD362]
map_id = pyboy.memory[0xD35E]
in_battle = pyboy.memory[0xD057] != 0
badges = bin(pyboy.memory[0xD356]).count('1')
```

## mGBA-http 사용 예시

```
GET http://127.0.0.1:5000/core/read8?address=0xD35E -> 맵 ID
GET http://127.0.0.1:5000/core/read8?address=0xD361 -> Y 좌표
GET http://127.0.0.1:5000/core/read8?address=0xD362 -> X 좌표
GET http://127.0.0.1:5000/core/read8?address=0xD057 -> 배틀 플래그
```
