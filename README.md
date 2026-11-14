# genius

몰랐던 내용을 기록하여, 주기적인 시험을 통해 나의 지식으로 쌓는 학습 플러그인입니다.

전체 흐름은 [흐름도](https://kimjunyoung90.github.io/genius/architecture.html)에서 확인할 수 있습니다.

## 제공 기능

| 기능 | 담당 | 설명 |
|---|---|---|
| 시험지 생성 | `test` 스킬 | 몰랐던 내용이 내 것이 됐는지 확인하는 시험지를 만든다. 모드는 둘 중 고를 수 있다.<ul><li>손글씨 모드(기본)</li><li>대화형 모드(<code>chat</code> 옵션)</li></ul> |
| 채점 | `grade` 스킬 | 푼 시험을 채점하고, 문제마다 해설을 붙인다. 모드는 시험을 본 방식에 맞춰 고른다.<ul><li>손글씨 모드(기본)</li><li>대화형 모드(<code>chat</code> 옵션)</li></ul> |
| 오답 정리 | `note` 스킬 | 정확히 몰랐던 문제를 오답노트로 만들어 자기 말로 다시 정리하게 한다. 다 쓴 오답노트는 학습 로그로 옮긴다(`save`). |
| 복습 시험 | `review` 스킬 | 복습일이 된 내용만 골라 다른 각도로 다시 내는 복습 시험지 만들기 |
| 피드백 보내기 | `feedback` 스킬 | 불편한 점이나 제안을 정리해 개발자에게 GitHub Issue로 보낸다. |
| 모르는 내용 자동 기록 | `UserPromptSubmit` hook, `question` agent | Claude Code를 쓰다가 몰랐던 것을 물으면, 몰랐던 내용을 학습 로그와 TIL에 알아서 남긴다. |

## 요구 사항

- macOS: PDF 변환과 필기 자르기 스크립트가 Swift(WebKit, PDFKit)를 씁니다. Xcode Command Line Tools(`swift`)가 필요합니다.
- `jq`: hook 스크립트가 씁니다. macOS 15 이상은 기본으로 들어 있고(`/usr/bin/jq`), 그 아래면 `brew install jq`.

## 설치

```
/plugin marketplace add kimjunyoung90/claude-plugins
/plugin install genius@kimjunyoung90
```

## 경로 설정

플러그인을 켤 때 Claude Code가 아래 값을 물어봅니다. 나중에는 `/config`에서 바꿉니다. 폴더와 학습 로그는 스킬이 처음 쓸 때 만듭니다.

| 설정 | 내용 |
|---|---|
| `notes_path` | TIL(오늘 알게 된 것)이 쌓이고 시험 문제가 나오는 노트 폴더. 예: Obsidian vault 안의 TIL 폴더 |
| `genius_path` | `학습 로그.md`, `시험/`, `복습/`, `오답/` PDF 폴더와 숨김 폴더 `.답안지/`. 여러 기기에서 열 수 있는 동기화 폴더 권장 |
| `review_limit` | 복습 시험 한 번에 낼 문제 수. 기본 7 |

## 하루 흐름

1. `/genius:test <노트>`로 시험지를 만들고 노트 없이 손으로 풉니다.
2. `/genius:grade`로 채점합니다. 문제마다 해설이 붙은 해설지가 생기고, 모든 문항이 학습 로그에 기록됩니다.
3. 해설을 읽으며 "질문·내 이해" 칸에 적고 `/genius:note`를 실행합니다. 적은 것을 확인받고 오답노트를 받습니다.
4. 시험지를 닫고 오답노트를 자기 말로 쓴 뒤, `/genius:note save`로 학습 로그에 옮깁니다.
5. 복습일에 `/genius:review`로 복습 시험지를 만들어 풀고, `/genius:grade`로 채점합니다. 밀린 복습이 많으면 `/genius:review 20`처럼 문제 수를 정할 수 있습니다. 복습 간격은 3·14·60일이고, 60일 복습까지 맞히면 졸업합니다. 대화 중 남긴 질문은 `/genius:test new`로 시험을 본 뒤에 복습 일정에 들어갑니다.

시험이나 공부 중이 아니어도, Claude Code를 쓰다가 원리나 차이를 몰라서 한 질문은 question agent가 백그라운드에서 따로 기록합니다. 도구 사용법이나 찾아보면 끝나는 사실은 기록하지 않습니다. 질문은 학습 로그에, 알게 된 내용은 노트 폴더의 그날 TIL(`YYYY-MM-DD.md`)에 남겨서, 대화 중 질문도 시험과 복습에 나옵니다.

## 피드백 보내기

쓰다가 이상하거나 불편한 점이 있으면 `/genius:feedback <내용>`을 실행합니다. 내용을 문제 신고나 개선 제안 양식에 맞게 정리하고, 노트·답안·학습 로그 내용은 뺀 초안을 보여 줍니다. 확인하면 [GitHub CLI](https://cli.github.com)(`gh`) 로그인 계정으로 Issue를 바로 등록합니다. `gh`가 없으면 내용이 채워진 Issue 작성 화면을 브라우저에 열어 주니, 직접 제출하면 됩니다(GitHub 계정 필요). [Issues](https://github.com/kimjunyoung90/genius/issues/new/choose)에서 바로 써도 됩니다.

채점이 틀렸다는 것처럼 내 기록을 고칠 일은 Issue로 보내지 않고 그 자리에서 학습 로그를 고칩니다.
