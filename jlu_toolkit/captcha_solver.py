"""CAS /tpass/code 四位数字验证码求解器（纯 Python + Pillow）。

算法：
  1. 只保留近黑色 RGB 像素（彩色噪线被滤掉）
  2. 连通域分割出 4 个数字
  3. 归一化到 12x16 二值图，与内嵌模板库做 kNN（Hamming）

模板在 build 时用真实样本 + ddddocr 标注生成，运行时不需要 ddddocr/onnx。
"""
from __future__ import annotations

import collections
import json
from pathlib import Path
from typing import Optional

TW = 12
TH = 16
_TEMPLATES: Optional[list] = None


def _unpack_bits(packed: bytes, nbits: int = TW * TH) -> bytes:
    out = bytearray(nbits)
    for i in range(nbits):
        if packed[i // 8] & (1 << (i % 8)):
            out[i] = 1
    return bytes(out)


def load_templates() -> list:
    global _TEMPLATES
    if _TEMPLATES is not None:
        return _TEMPLATES
    path = Path(__file__).resolve().parent / "data" / "digit_templates.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    items = []
    for ch, packed in meta["items"]:
        items.append((str(ch), _unpack_bits(bytes.fromhex(packed), meta["tw"] * meta["th"])))
    _TEMPLATES = items
    return items


def _require_pil():
    try:
        from PIL import Image  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "自动识别验证码需要 Pillow。Termux: pkg install python-pillow"
        ) from e
    from PIL import Image

    return Image


def ink_mask(img, thr: int = 50):
    """保留近黑像素为墨迹（0），其余为背景（255）。"""
    Image = _require_pil()
    img = img.convert("RGB")
    w, h = img.size
    px = img.load()
    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    for x in range(w):
        for y in range(h):
            r, g, b = px[x, y]
            if r < thr and g < thr and b < thr:
                mp[x, y] = 0
    return mask


def _components(mask, min_n: int = 12):
    w, h = mask.size
    px = mask.load()
    visited = [[False] * h for _ in range(w)]
    out = []
    for x in range(w):
        for y in range(h):
            if visited[x][y] or px[x, y] >= 128:
                continue
            q = collections.deque([(x, y)])
            visited[x][y] = True
            cells = []
            while q:
                cx, cy = q.popleft()
                cells.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if (
                        0 <= nx < w
                        and 0 <= ny < h
                        and not visited[nx][ny]
                        and px[nx, ny] < 128
                    ):
                        visited[nx][ny] = True
                        q.append((nx, ny))
            if len(cells) < min_n:
                continue
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            ww, hh = x1 - x0 + 1, y1 - y0 + 1
            if ww > 20 or hh < 8 or hh > 28:
                continue
            out.append((x0, x1, y0, y1, cells))
    out.sort(key=lambda c: c[0])
    return out


def _crop_norm(mask, box) -> bytes:
    Image = _require_pil()
    x0, x1, y0, y1, _ = box
    w, h = mask.size
    x0 = max(0, x0 - 1)
    y0 = max(0, y0 - 1)
    x1 = min(w - 1, x1 + 1)
    y1 = min(h - 1, y1 + 1)
    crop = mask.crop((x0, y0, x1 + 1, y1 + 1)).resize((TW, TH), Image.NEAREST)
    bits = []
    px = crop.load()
    for y in range(TH):
        for x in range(TW):
            bits.append(1 if px[x, y] < 128 else 0)
    return bytes(bits)


def _hamming(a: bytes, b: bytes) -> int:
    return sum(x != y for x, y in zip(a, b))


def _predict_digit(feat: bytes, templates: list, k: int = 5) -> str:
    dists = sorted((_hamming(feat, t), d) for d, t in templates)
    top = dists[:k]
    votes = collections.Counter(d for _, d in top)
    best = votes.most_common()
    if len(best) == 1 or best[0][1] > best[1][1]:
        return best[0][0]
    return top[0][1]


def _split_fixed4(mask) -> list:
    """连通域失败时的兜底：按墨迹水平包围盒均分 4 格。"""
    w, h = mask.size
    px = mask.load()
    xs = [x for x in range(w) for y in range(h) if px[x, y] < 128]
    if not xs:
        return []
    x0, x1 = min(xs), max(xs)
    span = x1 - x0 + 1
    boxes = []
    for i in range(4):
        a = x0 + span * i // 4
        b = x0 + span * (i + 1) // 4 - 1
        ys = [y for x in range(a, b + 1) for y in range(h) if px[x, y] < 128]
        if not ys:
            return []
        boxes.append((a, b, min(ys), max(ys), None))
    return boxes


def extract_digit_features(image_bytes: bytes) -> Optional[list]:
    Image = _require_pil()
    import io

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception:
        return None
    mask = ink_mask(img)
    comps = _components(mask)
    if len(comps) != 4:
        comps = _split_fixed4(mask)
        if len(comps) != 4:
            return None
    return [_crop_norm(mask, c) for c in comps]


def solve_captcha(image_bytes: bytes, k: int = 5) -> Optional[str]:
    """识别四位数字验证码。成功返回 4 位字符串，失败返回 None。"""
    try:
        feats = extract_digit_features(image_bytes)
    except Exception:
        return None
    if not feats or len(feats) != 4:
        return None
    templates = load_templates()
    if not templates:
        return None
    pred = "".join(_predict_digit(f, templates, k=k) for f in feats)
    if len(pred) != 4 or not pred.isdigit():
        return None
    return pred
