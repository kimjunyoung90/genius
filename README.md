# genius

몰랐던 내용을 기록하여, 주기적인 시험을 통해 나의 지식으로 쌓는 학습 플러그인입니다.

전체 흐름은 [흐름도](https://kimjunyoung90.github.io/genius/architecture.html)에서 확인할 수 있습니다.

## 제공 기능

| 기능 | 담당 | 설명 |
|---|---|---|
| 시험지 생성 | `test` 스킬 | 몰랐던 내용이 내 것이 됐는지 확인하는 시험지를 만든다. 모드는 둘 중 고를 수 있다.<ul><li>손글씨 모드(기본)</li><li>대화형 모드(<code>chat</code> 옵션)</li></ul> |
| 채점 | `grade` 스킬 | 푼 시험을 채점하고, 문제마다 해설을 붙인다. 모드는 시험을 본 방식에 맞춰 고른다.<ul><li>손글씨 모드(기본)</li><li>대화형 모드(<code>chat</code> 옵션)</li></ul> |
| 오답 정리 | `note` 스킬 | 정확히 몰랐던 문제를 오답노트로 만들어 자기 말로 다시 정리하게 한다. 모드는 둘 중 고를 수 있다.<ul><li>손글씨 모드(기본)</li><li>대화형 모드(<code>chat</code> 옵션)</li></ul>다 쓴 오답노트는 <code>check</code> 옵션으로 검사받고, 통과해야 시험이 끝난다. |
| 복습 시험 | `review` 스킬 | 복습일이 된 내용만 골라 다른 각도로 다시 내는 복습 시험지 만들기 |
| 피드백 보내기 | `feedback` 스킬 | 불편한 점이나 제안을 정리해 개발자에게 GitHub Issue로 보낸다. |
| 모르는 내용 자동 기록 | `UserPromptSubmit` hook, `question` agent | Claude Code를 쓰다가 몰랐던 것을 물으면, 몰랐던 내용을 TIL과 학습 로그에 알아서 남긴다. |

## 필요 환경

- **Python 3과 `pymupdf`**: 몰랐던 내용 자동 기록과 시험지·해설지 PDF 처리에 사용합니다.
- **Chromium 계열 브라우저(Chrome, Edge, Whale 등)**: 시험지 PDF를 만드는 데 사용합니다.

## 설치

```
/plugin marketplace add kimjunyoung90/claude-marketplace
/plugin install genius@kimjunyoung90
```

## 초기 설정

플러그인 설치 후 필요한 값을 설정합니다. 나중에 바꾸려면 `/config`를 씁니다. 폴더와 학습 로그는 처음 쓸 때 자동으로 만들어집니다.

| 설정 | 내용 |
|---|---|
| `notes_path` | 시험 문제 출제의 소스가 되는 TIL(오늘 알게 된 것) 경로. 예: Obsidian vault 안의 TIL 폴더 |
| `genius_path` | 학습 로그(`학습 로그.jsonl`)와 시험지·해설지·오답노트가 저장되는 경로 |
| `exam_limit` | 첫 시험과 복습 시험이 한 장에 내는 문제 수(실습 과제 포함). 기본 5 |
| `review_intervals` | 단계를 끝낸 뒤 다음 복습까지의 날 수. 기본 `3,14,60` |

## 하루 흐름

시험은 오답노트 검사를 통과해야 끝나고, 아직 끝내지 않은 시험이 있으면 새 시험지는 나오지 않습니다.

1. **기록**: Claude Code를 쓰다가 몰랐던 것을 물으면 TIL과 학습 로그에 자동으로 남습니다.
2. **시험**: `/genius:test`(첫 시험) 또는 `/genius:review`(복습)로 시험지를 받아 풉니다(대화형은 `chat`).
3. **채점**: `/genius:grade`로 채점하면 해설지가 생깁니다(대화형은 `chat`). 다 맞히면 여기서 끝납니다.
4. **오답노트**: 해설지에 질문을 적고 `/genius:note`로 오답노트를 받아 자기 말로 씁니다(대화형은 `chat`).
5. **검사**: `/genius:note check`로 문항마다 통과 여부를 받습니다. 통과하지 못한 문항은 같은 오답노트의 `다시 정리` 칸에 다시 쓰고 검사받습니다. 모두 통과하면 시험이 끝납니다.
6. **복습**: 시험을 끝낸 날부터 `review_intervals`에 정한 날(기본 3·14·60일) 뒤에 같은 순서로 다시 봅니다. 마지막 복습까지 끝내면 졸업합니다.

## 피드백 보내기

불편한 점이나 제안이 있으면 `/genius:feedback <내용>`을 실행합니다. 공부 내용을 뺀 초안을 확인하면 GitHub Issue로 등록됩니다. [Issues](https://github.com/kimjunyoung90/genius/issues/new/choose)에서 직접 써도 됩니다.
