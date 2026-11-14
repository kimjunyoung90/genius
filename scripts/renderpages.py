"""PDF 페이지를 필기(주석)째 이미지로 만들어 p1.png, p2.png ... 로 저장한다. 위아래 빈 공간은 잘라낸다.

usage: python3 renderpages.py <pdf> <출력 폴더> <페이지 수>
필요: pymupdf (pip install pymupdf). macOS·Windows·Linux 공통.
"""
import os
import sys

import pymupdf

SCALE = 2.5
# R+G+B 합이 이보다 작으면 잉크로 본다.
DARK_SUM = 690


def count_dark(row, limit, need):
    if min(row) * 3 >= limit:
        return 0
    d = 0
    for i in range(0, len(row), 3):
        if row[i] + row[i + 1] + row[i + 2] < limit:
            d += 1
            if d >= need:
                break
    return d


def main():
    a = sys.argv
    if len(a) < 4:
        sys.exit("usage: python3 renderpages.py <pdf> <outdir> <pages>")
    doc = pymupdf.open(a[1])
    out, n = a[2], int(a[3])
    os.makedirs(out, exist_ok=True)
    mat = pymupdf.Matrix(SCALE, SCALE)
    for i in range(min(n, doc.page_count)):
        page = doc[i]
        pix = page.get_pixmap(matrix=mat, annots=True, alpha=False)
        h, stride, data = pix.height, pix.stride, pix.samples
        ink = [r for r in range(h) if count_dark(data[r * stride:(r + 1) * stride], DARK_SUM, 3) >= 3]
        first, last = (ink[0], ink[-1]) if ink else (0, h - 1)
        pad = int(8 * SCALE)
        top, bot = max(0, first - pad), min(h, last + pad)
        clip = pymupdf.Rect(0, top / SCALE, page.rect.width, bot / SCALE)
        page.get_pixmap(matrix=mat, clip=clip, annots=True, alpha=False).save(os.path.join(out, f"p{i + 1}.png"))
        print(f"p{i + 1} rows {top}-{bot}")


if __name__ == "__main__":
    main()
