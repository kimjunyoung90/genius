"""HTML을 A4 여러 쪽 PDF로 저장한다. 설치된 Chromium 계열 브라우저(Chrome, Edge, Whale, Brave, Chromium)의 headless 인쇄를 쓴다.

usage: python3 html2pdf.py <입력.html> <출력.pdf>
- 브라우저는 환경 변수 GENIUS_BROWSER(실행 파일 경로)를 먼저 쓰고, 없으면 OS별 기본 설치 위치와 PATH에서 찾는다.
- Windows에는 Edge가 기본으로 깔려 있다. Safari·Firefox는 명령줄 PDF 인쇄가 없어 쓸 수 없다.
- 쪽 크기는 A4가 기본이고, 여백과 크기는 HTML의 @page 규칙이 있으면 그것을 따른다(규칙이 없으면 여백 14mm).
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CANDIDATES = {
    "darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Naver Whale.app/Contents/MacOS/Naver Whale",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ],
    "win32": [
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
        r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles%\Naver\Naver Whale\Application\whale.exe",
        r"%ProgramFiles(x86)%\Naver\Naver Whale\Application\whale.exe",
        r"%LocalAppData%\Naver\Naver Whale\Application\whale.exe",
    ],
}
PATH_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome", "naver-whale", "whale"]
DEFAULT_PAGE = "<style>@page { size: A4; margin: 14mm; }</style>"


def find_browser():
    env = os.environ.get("GENIUS_BROWSER")
    if env and Path(env).exists():
        return env
    key = "win32" if sys.platform.startswith("win") else sys.platform
    for c in CANDIDATES.get(key, []):
        p = os.path.expandvars(c)
        if Path(p).exists():
            return p
    for name in PATH_NAMES:
        p = shutil.which(name)
        if p:
            return p
    sys.exit("Chromium 계열 브라우저(Chrome, Edge, Whale 등)를 찾지 못했다. 설치하거나 GENIUS_BROWSER에 실행 파일 경로를 지정한다.")


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python3 html2pdf.py <in.html> <out.pdf>")
    src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    html = src.read_text(encoding="utf-8")
    # 기본 쪽 설정(A4)을 HTML 앞쪽에 넣은 사본을 같은 폴더에 만들어 인쇄한다(상대 경로 이미지 유지).
    # 브라우저 기본 용지는 Letter라서, @page에 크기가 없어도 A4로 나오게 하려는 것이다. HTML의 @page 규칙이 뒤에 오므로 그쪽이 우선한다.
    tmp = src.with_name(f".{src.stem}.print.html")
    tmp.write_text(html.replace("<head>", "<head>" + DEFAULT_PAGE, 1) if "<head>" in html else DEFAULT_PAGE + html, encoding="utf-8")
    target = tmp
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)  # 실패했을 때 예전 파일을 결과로 착각하지 않게 먼저 지운다.
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            find_browser(), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={profile}", "--no-pdf-header-footer", "--print-to-pdf-no-header",
            "--allow-file-access-from-files", "--virtual-time-budget=2000",
            f"--print-to-pdf={out}", target.as_uri(),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    tmp.unlink(missing_ok=True)
    if not out.exists() or out.stat().st_size == 0:
        sys.exit(f"PDF를 만들지 못했다.\n{r.stderr[-2000:]}")
    print(out)


if __name__ == "__main__":
    main()
