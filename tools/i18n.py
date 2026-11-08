"""大肥鱼控制台的多语言文案。

源语言是简体中文：代码里照常写中文，渲染时按当前语言查表。
- 静态文案：CATALOG 里以整句为键，`tr()` 精确命中。
- 带变量的文案：键里用 {0}/{1} 占位，`tr()` 用正则匹配后填充译文。
- 简体中文下 `tr()` 直接返回原文，零开销。
"""

from __future__ import annotations

import re

from i18n_catalog import CATALOG

LANGS = [
    ("ja", "日本語"),
    ("en", "English"),
    ("zh-Hans", "简体中文"),
    ("zh-Hant", "繁體中文"),
]
DEFAULT_LANG = "zh-Hans"
VALID_LANGS = {code for code, _ in LANGS}

_current = DEFAULT_LANG


def load(settings: dict) -> None:
    """按 settings.json 里的 lang 初始化；非法值回落到简体中文。"""
    global _current
    code = str(settings.get("lang") or DEFAULT_LANG)
    _current = code if code in VALID_LANGS else DEFAULT_LANG


def get_lang() -> str:
    return _current


def set_lang(code: str) -> None:
    global _current
    if code in VALID_LANGS:
        _current = code


def lang_name(code: str) -> str:
    for c, name in LANGS:
        if c == code:
            return name
    return code


_PATTERNS = None


def _patterns():
    """把带占位符的源串编译成锚定正则；长的优先，避免短模板抢匹配。"""
    global _PATTERNS
    if _PATTERNS is None:
        out = []
        for src in CATALOG:
            if "{" not in src:
                continue
            parts = re.split(r"\{\d+\}", src)
            rx = r"^" + r"(.+?)".join(re.escape(p) for p in parts) + r"$"
            try:
                out.append((re.compile(rx, re.S), src))
            except re.error:
                continue
        out.sort(key=lambda item: -len(item[1]))
        _PATTERNS = out
    return _PATTERNS


def tr(text: str) -> str:
    """把一段（可能带变量的）中文界面文案翻成当前语言。"""
    if not text or _current == "zh-Hans":
        return text
    hit = CATALOG.get(text)
    if hit:
        out = hit.get(_current)
        if out:
            return out
    for rx, src in _patterns():
        m = rx.match(text)
        if not m:
            continue
        out = CATALOG.get(src, {}).get(_current)
        if not out:
            continue
        try:
            return out.format(*m.groups())
        except Exception:
            return text
    return text


def t(text: str, *args, **kwargs) -> str:
    """模板翻译 + 立即格式化：t("已复制：{0}", text)。"""
    out = tr(text)
    if not args and not kwargs:
        return out
    try:
        return out.format(*args, **kwargs)
    except Exception:
        return out
