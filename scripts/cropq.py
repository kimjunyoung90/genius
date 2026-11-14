"""문제 번호 위치를 기준으로 문제와 그 아래 필기를 잘라 q1.png, q2.png ... 로 저장한다.

usage: python3 cropq.py <시험지.pdf> <출력 폴더> <문제 수> [원래 시험지 페이지 수] [채점 표시] [표시 접두사]

- 채점 표시: 문제 순서대로 O(정답), T(부분 정답, 세모), X(오답)를 쉼표로 구분(예: O,T,X,O,X,X). 번호 위에 빨간색으로 그린다.
- 표시 접두사(예: "@Q")를 주면, 번호 대신 해설지에 숨겨 둔 "@Q1@" 같은 표시로 문항 블록을 찾는다(note 단계용).
- 필요: pymupdf (pip install pymupdf). macOS·Windows·Linux 공통.
"""
import os
import sys

import pymupdf

SCALE = 3
RED = (0.85, 0.12, 0.10)
# R+G+B 합이 이보다 작으면 잉크(어두운 픽셀)로 본다. 노란 형광펜 같은 색도 잡히도록 밝기가 아니라 합으로 본다.
DARK_SUM = 600


def count_dark(row, limit):
    """한 줄(RGB 바이트)에서 R+G+B < limit 인 픽셀 수. 모든 채널이 limit/3 이상이면 바로 0."""
    if min(row) * 3 >= limit:
        return 0
    return sum(1 for i in range(0, len(row), 3) if row[i] + row[i + 1] + row[i + 2] < limit)


def find_markers(doc, n, exam_pages, prefix):
    markers = []
    for q in range(1, n + 1):
        key = f"{prefix}{q}@" if prefix else f"{q}."
        found = None
        for pi in range(min(exam_pages, doc.page_count)):
            page = doc[pi]
            h = page.rect.height
            for r in sorted(page.search_for(key), key=lambda r: r.y0):
                # 인쇄 엔진이 페이지가 넘어가는 블록의 숨김 표시를 앞 페이지 맨 아래에 한 번 더 찍는 경우가 있다. 그 복제본은 무시한다.
                if prefix and r.y0 > h - 60:
                    continue
                if not prefix and not (r.x0 < 50 and r.width < 20):
                    continue
                if markers:
                    prev = markers[-1]
                    if pi < prev["page"] or (pi == prev["page"] and r.y0 <= prev["top"]):
                        continue
                found = {"q": q, "page": pi, "top": r.y0, "center": ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)}
                break
            if found:
                break
        if not found:
            sys.exit(f"marker {key} not found")
        markers.append(found)
    return markers


def draw_mark(page, mark, center):
    r = 15
    cx, cy = center[0] + 2, center[1]
    shape = page.new_shape()
    if mark == "O":
        shape.draw_circle((cx, cy), r)
    elif mark in ("T", "△"):
        shape.draw_polyline([(cx, cy - r * 1.1), (cx - r * 1.05, cy + r * 0.75), (cx + r * 1.05, cy + r * 0.75), (cx, cy - r * 1.1)])
    elif mark == "X":
        shape.draw_line((cx - r * 0.85, cy - r * 0.85), (cx + r * 0.85, cy + r * 0.85))
        shape.draw_line((cx + r * 0.85, cy - r * 0.85), (cx - r * 0.85, cy + r * 0.85))
    else:
        return
    shape.finish(color=RED, width=2.4, lineCap=1, lineJoin=1, stroke_opacity=0.9)
    shape.commit()


def ink_bottom(pix):
    """잉크가 있는 마지막 행(픽셀)을 찾는다. 앞 덩어리와 멀리 떨어진 작은 점은 무시한다."""
    h, stride, data = pix.height, pix.stride, pix.samples
    segments = []  # [start, end, width]
    for row in range(h):
        dark = count_dark(data[row * stride:(row + 1) * stride], DARK_SUM)
        if dark < 3:
            continue
        if segments and row - segments[-1][1] <= 2:
            segments[-1][1] = row
            segments[-1][2] = max(segments[-1][2], dark)
        else:
            segments.append([row, row, dark])
    # 작고(높이 6pt 미만), 좁고(가로 50pt 미만, 즉 테두리선이 아님), 앞 덩어리와 30pt 넘게 떨어진 것만 버린다.
    while len(segments) > 1:
        start, end, width = segments[-1]
        if end - start < 6 * SCALE and width < 50 * SCALE and start - segments[-2][1] > 30 * SCALE:
            segments.pop()
        else:
            break
    return segments[-1][1] if segments else h


def main():
    a = sys.argv
    if len(a) < 4:
        sys.exit("usage: python3 cropq.py <pdf> <outdir> <count> [examPages] [marks] [prefix]")
    doc = pymupdf.open(a[1])
    out, n = a[2], int(a[3])
    exam_pages = int(a[4]) if len(a) >= 5 and a[4] else doc.page_count
    marks = [m.strip().upper() for m in a[5].split(",")] if len(a) >= 6 and a[5] else []
    prefix = a[6] if len(a) >= 7 and a[6] else None
    os.makedirs(out, exist_ok=True)

    markers = find_markers(doc, n, exam_pages, prefix)
    for i, m in enumerate(markers):
        page = doc[m["page"]]
        box = page.rect
        top = max(0, m["top"] - (14 if marks else 6))
        bottom = box.height - 28
        if i + 1 < len(markers) and markers[i + 1]["page"] == m["page"]:
            bottom = markers[i + 1]["top"] - 4
        if i < len(marks):
            draw_mark(page, marks[i], m["center"])
        clip = pymupdf.Rect(20, top, box.width - 20, bottom)
        mat = pymupdf.Matrix(SCALE, SCALE)
        pix = page.get_pixmap(matrix=mat, clip=clip, annots=True, alpha=False)
        keep = min(pix.height, ink_bottom(pix) + 14 * SCALE)
        if keep < pix.height:
            clip.y1 = clip.y0 + keep / SCALE
            pix = page.get_pixmap(matrix=mat, clip=clip, annots=True, alpha=False)
        pix.save(os.path.join(out, f"q{m['q']}.png"))
        print(f"q{m['q']}: page {m['page']} y {int(top)}-{int(bottom)}")


if __name__ == "__main__":
    main()
