# 학습 로그 형식

학습 로그는 몰랐던 것 하나하나를 "학습했는가" 관점에서 추적한다. **내용은 적지 않고 상태와 참조만 둔다.** 문제, 답, 해설, 정리는 답안지·해설지·오답노트·TIL에 있다.

# 파일 위치
`<NOTES>`(노트 폴더)와 `<GENIUS>`(genius 폴더)는 플러그인 설정(`userConfig`)의 값이다. 스킬은 SKILL.md에 적혀 있고, `question` agent는 호출 프롬프트로 받는다.
- 학습 로그: `<GENIUS>/학습 로그.jsonl`
- 답안지: `<GENIUS>/.답안지/<exam>.md` (숨김 폴더. 시험 전에 답이 눈에 띄지 않게)
- 해설지: 시험지 자리(`<GENIUS>/시험/`, `<GENIUS>/복습/`)
- 오답노트: `<GENIUS>/오답/<exam> 오답노트.pdf`
- TIL(오늘 알게 된 것): `<NOTES>/YYYY-MM-DD.md`. 형식은 `references/til-format.md`

# 형식
한 줄이 몰랐던 것 하나다.

```json
{"til": "2026-10-31#Redis에서 캐시를 조회하면 TTL이 자동으로 연장된다고 알고 있음",
 "stages": [{"stage": 1, "exam": "2026-10-31 새 질문", "status": "완료", "done": "2026-11-15"}]}
```

| 키 | 값 |
|---|---|
| `til` | `YYYY-MM-DD#제목`. TIL 파일 날짜와 그 파일의 `##` 제목(글자 그대로) |
| `stages` | 단계 기록. 시험 전에는 `[]` |
| `stage` | `1` 첫 시험, `2`부터 복습. 기본 간격(3,14,60)이면 `2` 3일 복습, `3` 14일 복습, `4` 60일 복습 |
| `exam` | 그 단계 문제가 나온 답안지 이름(확장자 없이). 해설지·오답노트도 이 이름으로 찾는다 |
| `status` | `풀이 대기` · `오답노트 대기` · `다시 쓰기` · `완료` |
| `done` | 단계를 완료한 날 `YYYY-MM-DD`. 완료 전에는 `null` |

# 단계와 상태
- 몰랐던 것을 TIL에 기록할 때 `stages: []`로 줄을 만든다(`question` agent).
- 출제하면 다음 단계를 `풀이 대기`로 붙인다(`test`, `review`).
- 채점에서 오답노트에 넣지 않는 문항(확신 정답, 단순 사실)은 `완료`, 나머지는 `오답노트 대기`(`grade`).
- 오답노트 검사에서 통과하면 `완료`, 아니면 `다시 쓰기`(`note`). 다시 쓴 뒤 다시 검사한다.
- 다음 단계 복습일 = 직전 단계 `done` + 간격. 간격은 플러그인 설정 `review_intervals`(기본 `3,14,60`: 1단계 뒤 3일, 2단계 뒤 14일, 3단계 뒤 60일)이고, `log.py`에 `--intervals`로 넘긴다. 저장하지 않고 계산한다.
- 복습에서 틀려도 단계를 되돌리지 않는다. 같은 단계에서 오답노트를 통과하면 다음 단계로 간다.
- 마지막 단계(간격 개수 + 1, 기본 4단계)를 완료하면 졸업이다.
- **퀘스트**: 시험지 한 장. 그 `exam`의 모든 단계가 `완료`가 되면 끝난다. 끝나지 않은 퀘스트가 있으면 새 시험지를 만들지 않는다.

# 쓰는 방법
학습 로그는 `<ROOT>/scripts/log.py`로만 읽고 쓴다. 파일을 직접 고치지 않는다. 스크립트가 형식을 검사하고, 맞지 않는 값은 거부한다.

```bash
python3 "<ROOT>/scripts/log.py" "<GENIUS>" add "<til>"
python3 "<ROOT>/scripts/log.py" "<GENIUS>" untested          # 첫 시험 대상
python3 "<ROOT>/scripts/log.py" "<GENIUS>" due --intervals "<간격>"   # 복습 대상: 복습일, 다음 단계, til
python3 "<ROOT>/scripts/log.py" "<GENIUS>" issue "<exam>" "<til>" ... --intervals "<간격>"
python3 "<ROOT>/scripts/log.py" "<GENIUS>" unissue "<exam>"     # 풀기 전 시험지 취소(다시 출제할 때)
python3 "<ROOT>/scripts/log.py" "<GENIUS>" grade "<exam>" "<til>" 정답|오답노트
python3 "<ROOT>/scripts/log.py" "<GENIUS>" note "<exam>" "<til>" 통과|"다시 쓰기"
python3 "<ROOT>/scripts/log.py" "<GENIUS>" regrade "<exam>" "<til>" 정답|오답노트   # 채점 판정 정정
python3 "<ROOT>/scripts/log.py" "<GENIUS>" quests            # 끝나지 않은 퀘스트
python3 "<ROOT>/scripts/log.py" "<GENIUS>" show [검색어] --intervals "<간격>"
python3 "<ROOT>/scripts/log.py" "<GENIUS>" retitle "<옛 til>" "<새 til>"
python3 "<ROOT>/scripts/log.py" "<GENIUS>" remove "<til>" ...     # 더 공부하지 않을 til 삭제(진행 중인 시험이 있으면 거부). TIL 노트는 참고용으로 남겨도 된다
python3 "<ROOT>/scripts/log.py" "<GENIUS>" check "<NOTES>"   # 형식과 TIL 제목 확인
```

- `<간격>`은 플러그인 설정 `review_intervals` 값이다. 스킬에서는 `${user_config.review_intervals}`로 넘긴다. 생략하면 `3,14,60`을 쓴다.
- TIL 제목을 고치면 `retitle`로 학습 로그도 함께 고친다.
- 답안지에는 문항마다 `- TIL: <til>` 줄을 둔다(여러 개를 묶었으면 줄마다 하나). 채점과 오답노트 검사가 이 줄로 학습 로그를 고친다.
