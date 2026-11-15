"""학습 로그(<GENIUS>/학습 로그.jsonl)를 읽고 쓰는 유일한 통로. 형식에 맞지 않는 값은 거부한다.

한 줄 = 몰랐던 것 하나:
  {"til": "YYYY-MM-DD#TIL 제목", "stages": [{"stage": 1, "exam": "답안지 이름", "status": "풀이 대기", "done": null}]}

usage: python3 log.py "<GENIUS>" <명령> [인자...] [--date YYYY-MM-DD] [--intervals 3,14,60]
  add <til>                       새 줄(stages: []). 이미 있으면 그대로 둔다.
  untested                        아직 시험 보지 않은 til (오래된 순)
  due                             복습일이 된 til: "복습일<TAB>다음 단계<TAB>til" (오래된 순)
  issue <exam> <til>...           다음 단계를 풀이 대기로 추가
  grade <exam> <til> 정답|오답노트   정답이면 완료, 아니면 오답노트 대기
  note <exam> <til> 통과|다시 쓰기    오답노트 검사 결과
  regrade <exam> <til> 정답|오답노트  채점 판정을 고칠 때(그 til의 마지막 단계만)
  quests                          끝나지 않은 퀘스트: "exam<TAB>상태별 개수"
  show [검색어]                    사람이 볼 표
  retitle <옛 til> <새 til>         TIL 제목이 바뀌었을 때
  check "<NOTES>"                 형식 검사와 TIL 제목 존재 확인

--intervals: 단계 사이 날 수(플러그인 설정 review_intervals). 개수 + 1이 마지막 단계다. 없으면 3,14,60.
"""
import datetime
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

STATUSES = ("풀이 대기", "오답노트 대기", "다시 쓰기", "완료")
DEFAULT_INTERVALS = "3,14,60"
INTERVALS = []  # INTERVALS[n-1] = n단계를 끝낸 뒤 n+1단계까지의 날 수. main에서 정한다
LAST_STAGE = 0
TIL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}#\S.*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def die(msg):
    sys.exit(f"오류: {msg}")


def nfc(s):
    return unicodedata.normalize("NFC", s.strip())


def validate(rec, where):
    if set(rec) != {"til", "stages"}:
        die(f"{where}: 키는 til, stages만 허용 ({sorted(rec)})")
    if not isinstance(rec["til"], str) or not TIL_RE.match(rec["til"]):
        die(f"{where}: til은 'YYYY-MM-DD#제목' 형식이어야 한다 ({rec['til']!r})")
    if not isinstance(rec["stages"], list):
        die(f"{where}: stages는 배열이어야 한다")
    for i, s in enumerate(rec["stages"], 1):
        if set(s) != {"stage", "exam", "status", "done"}:
            die(f"{where}: 단계 키는 stage, exam, status, done만 허용 ({sorted(s)})")
        if s["stage"] != i:
            die(f"{where}: stage는 1부터 차례로 ({s['stage']})")
        if not isinstance(s["exam"], str) or not s["exam"].strip():
            die(f"{where}: exam이 비었다")
        if s["status"] not in STATUSES:
            die(f"{where}: status는 {' · '.join(STATUSES)} 중 하나 ({s['status']!r})")
        if s["status"] == "완료":
            if not isinstance(s["done"], str) or not DATE_RE.match(s["done"]):
                die(f"{where}: 완료 단계의 done은 YYYY-MM-DD ({s['done']!r})")
        elif s["done"] is not None:
            die(f"{where}: 완료 전 단계의 done은 null")
        if i < len(rec["stages"]) and s["status"] != "완료":
            die(f"{where}: 앞 단계가 완료되지 않았는데 다음 단계가 있다")


class Log:
    def __init__(self, genius):
        self.path = Path(genius) / "학습 로그.jsonl"
        self.recs = []
        if self.path.exists():
            for n, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip():
                    rec = json.loads(line)
                    validate(rec, f"{n}번째 줄")
                    self.recs.append(rec)
        tils = [r["til"] for r in self.recs]
        if len(tils) != len(set(tils)):
            die("같은 til이 두 줄 이상 있다")

    def find(self, til):
        til = nfc(til)
        for r in self.recs:
            if r["til"] == til:
                return r
        die(f"학습 로그에 없는 til: {til}")

    def save(self):
        for n, rec in enumerate(self.recs, 1):
            validate(rec, f"{n}번째 줄")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".학습 로그.", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for rec in self.recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp, self.path)


def due_date(rec):
    """다음 단계 복습일. 졸업했거나 진행 중이거나 시험 전이면 None."""
    st = rec["stages"]
    if not st or st[-1]["status"] != "완료" or st[-1]["stage"] >= LAST_STAGE:
        return None
    last = st[-1]
    return (datetime.date.fromisoformat(last["done"]) + datetime.timedelta(days=INTERVALS[last["stage"] - 1])).isoformat()


def stage_of(rec, exam):
    for s in rec["stages"]:
        if s["exam"] == exam:
            return s
    die(f"{rec['til']}: 시험 '{exam}'에 나온 단계가 없다")


def set_intervals(text):
    global INTERVALS, LAST_STAGE
    try:
        days = [int(x) for x in text.replace(" ", "").split(",")]
    except ValueError:
        days = []
    if not days or any(d < 1 for d in days):
        die(f"--intervals는 1 이상의 날 수를 쉼표로 ({text!r})")
    INTERVALS, LAST_STAGE = days, len(days) + 1


def main():
    args = sys.argv[1:]
    intervals = DEFAULT_INTERVALS
    if "--intervals" in args:
        i = args.index("--intervals")
        intervals = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
    set_intervals(intervals)
    today = datetime.date.today().isoformat()
    if "--date" in args:
        i = args.index("--date")
        today = args[i + 1]
        del args[i:i + 2]
        if not DATE_RE.match(today):
            die("--date는 YYYY-MM-DD")
    if len(args) < 2:
        sys.exit(__doc__)
    genius, cmd, rest = args[0], args[1], [nfc(a) for a in args[2:]]
    log = Log(genius)

    if cmd == "add" and len(rest) == 1:
        til = rest[0]
        validate({"til": til, "stages": []}, "add")
        if any(r["til"] == til for r in log.recs):
            print("이미 있음")
            return
        log.recs.append({"til": til, "stages": []})
        log.save()
        print("추가")
    elif cmd == "untested" and not rest:
        for r in sorted((r for r in log.recs if not r["stages"]), key=lambda r: r["til"]):
            print(r["til"])
    elif cmd == "due" and not rest:
        rows = [(due_date(r), len(r["stages"]) + 1, r["til"]) for r in log.recs]
        for d, nxt, til in sorted(x for x in rows if x[0] and x[0] <= today):
            print(f"{d}\t{nxt}\t{til}")
    elif cmd == "issue" and len(rest) >= 2:
        exam, tils = rest[0], rest[1:]
        for til in tils:
            r = log.find(til)
            st = r["stages"]
            if st and st[-1]["status"] != "완료":
                die(f"{til}: {st[-1]['stage']}단계가 아직 {st[-1]['status']}")
            if st and st[-1]["stage"] >= LAST_STAGE:
                die(f"{til}: 이미 졸업")
            st.append({"stage": len(st) + 1, "exam": exam, "status": "풀이 대기", "done": None})
        log.save()
        print(f"출제 {len(tils)}개")
    elif cmd == "grade" and len(rest) == 3 and rest[2] in ("정답", "오답노트"):
        s = stage_of(log.find(rest[1]), rest[0])
        if s["status"] != "풀이 대기":
            die(f"이미 채점됨 ({s['status']})")
        s["status"], s["done"] = ("완료", today) if rest[2] == "정답" else ("오답노트 대기", None)
        log.save()
        print(s["status"])
    elif cmd == "regrade" and len(rest) == 3 and rest[2] in ("정답", "오답노트"):
        r = log.find(rest[1])
        s = stage_of(r, rest[0])
        if s is not r["stages"][-1]:
            die("다음 단계가 이미 시작되어 고칠 수 없다")
        if s["status"] == "풀이 대기":
            die("아직 채점 전이다. grade를 쓴다")
        s["status"], s["done"] = ("완료", today) if rest[2] == "정답" else ("오답노트 대기", None)
        log.save()
        print(s["status"])
    elif cmd == "note" and len(rest) == 3 and rest[2] in ("통과", "다시 쓰기"):
        s = stage_of(log.find(rest[1]), rest[0])
        if s["status"] not in ("오답노트 대기", "다시 쓰기"):
            die(f"오답노트 단계가 아니다 ({s['status']})")
        s["status"], s["done"] = ("완료", today) if rest[2] == "통과" else ("다시 쓰기", None)
        log.save()
        print(s["status"])
    elif cmd == "quests" and not rest:
        open_ = {}
        for r in log.recs:
            for s in r["stages"]:
                if s["status"] != "완료":
                    open_.setdefault(s["exam"], {}).setdefault(s["status"], 0)
                    open_[s["exam"]][s["status"]] += 1
        for exam in sorted(open_):
            print(exam + "\t" + ", ".join(f"{k} {v}" for k, v in open_[exam].items()))
    elif cmd == "show" and len(rest) <= 1:
        for r in log.recs:
            if rest and rest[0] not in r["til"]:
                continue
            st = r["stages"]
            if not st:
                state = "시험 전"
            elif st[-1]["stage"] >= LAST_STAGE and st[-1]["status"] == "완료":
                state = "졸업"
            else:
                state = f"{st[-1]['stage']}단계 · {st[-1]['status']}"
                if due_date(r):
                    state += f" (다음 복습 {due_date(r)})"
            print(f"{state}\t{r['til']}")
    elif cmd == "retitle" and len(rest) == 2:
        r = log.find(rest[0])
        validate({"til": rest[1], "stages": []}, "retitle")
        if any(x["til"] == rest[1] for x in log.recs):
            die("새 til이 이미 있다")
        r["til"] = rest[1]
        log.save()
        print("변경")
    elif cmd == "check" and len(rest) == 1:
        notes, missing = Path(rest[0]), []
        for r in log.recs:
            date, title = r["til"].split("#", 1)
            f = notes / f"{date}.md"
            heads = set()
            if f.exists():
                heads = {nfc(h) for h in re.findall(r"^## (.+)$", f.read_text(encoding="utf-8"), re.M)}
            if title not in heads:
                missing.append(r["til"])
        for m in missing:
            print(f"TIL 제목 없음: {m}")
        print(f"형식 정상, {len(log.recs)}줄, TIL 제목 없음 {len(missing)}개")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
