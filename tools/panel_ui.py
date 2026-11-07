"""大肥鱼控制台的面板界面（可缩放 / 设置页 / 托盘 / 关闭询问）。

坐标全部按 96 DPI 的逻辑像素写，渲染时乘一个 dpi_scale，
所以 1080p、2K、4K、笔记本 125%/150% 缩放下都一样清楚、比例不变。
"""

from __future__ import annotations

import ctypes
import threading
import time
import tkinter as tk
from pathlib import Path

import bot_ctl as core
import dashboard_view

THEMES = {
    "light": {
        "BG": "#FBFBFC", "CARD": "#FFFFFF", "BORDER": "#EAEAEE",
        "TEXT": "#17181A", "SUB": "#5B6069", "MUTED": "#9AA0AA",
        "ACCENT": "#3D6EF7", "ACCENT_HOVER": "#5A85F9", "ACCENT_DOWN": "#2F5AD9",
        "GREEN": "#12B76A", "GREY_DOT": "#D6D8DE", "HOVER": "#F3F4F6",
        "CHIP": "#F3F4F6", "DANGER": "#EF4444", "AMBER": "#B45309",
        "SHADOW1": "#F3F3F6", "SHADOW2": "#F8F8FA", "KNOB": "#FFFFFF",
        "TRACK_OFF": "#E3E4E9", "SEG_BG": "#F1F2F4", "BTN_HOVER": "#F7F8FA",
        "ON_ACCENT": "#FFFFFF", "DARK_TITLE": 0,
    },
    "dark": {
        "BG": "#141519", "CARD": "#1C1D23", "BORDER": "#2A2C33",
        "TEXT": "#F3F4F6", "SUB": "#A6AAB5", "MUTED": "#7B8090",
        "ACCENT": "#5B8CFF", "ACCENT_HOVER": "#79A2FF", "ACCENT_DOWN": "#3F6FE0",
        "GREEN": "#34D399", "GREY_DOT": "#464A55", "HOVER": "#242630",
        "CHIP": "#262832", "DANGER": "#F87171", "AMBER": "#FBBF24",
        "SHADOW1": "#101116", "SHADOW2": "#121319", "KNOB": "#F7F8FA",
        "TRACK_OFF": "#383B45", "SEG_BG": "#242630", "BTN_HOVER": "#252732",
        "ON_ACCENT": "#FFFFFF", "DARK_TITLE": 1,
    },
}

BG = CARD = BORDER = TEXT = SUB = MUTED = ""
ACCENT = ACCENT_HOVER = ACCENT_DOWN = GREEN = GREY_DOT = HOVER = CHIP = ""
DANGER = AMBER = SHADOW1 = SHADOW2 = KNOB = TRACK_OFF = SEG_BG = ""
BTN_HOVER = ON_ACCENT = ""
THEME = "light"

# 字体：界面统一走这两个全局，改设置后立刻生效
FONT_FAMILY = "Segoe UI Variable Text"
FONT_SCALE = 1.0
FONT_CHOICES = (
    ("", "系统默认"),
    ("Microsoft YaHei UI", "微软雅黑"),
    ("DengXian", "等线"),
    ("SimSun", "宋体"),
)
FONT_SIZES = ((0.88, "小"), (1.0, "标准"), (1.15, "大"), (1.3, "特大"))


def apply_theme(name: str) -> str:
    """把所有颜色写进模块级变量——绘制函数都直接引用这些全局名。"""
    global THEME
    key = name if name in THEMES else "light"
    THEME = key
    for k, v in THEMES[key].items():
        if k != "DARK_TITLE":
            globals()[k] = v
    return key


def _mix_color(a: str, b: str, k: float) -> str:
    k = max(0.0, min(1.0, k))
    ra, ga, ba = (int(a[i:i + 2], 16) for i in (1, 3, 5))
    rb, gb, bb = (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % (round(ra + (rb - ra) * k),
                              round(ga + (gb - ga) * k),
                              round(ba + (bb - ba) * k))


def blend_theme(a: str, b: str, k: float) -> None:
    """在 a、b 两套配色之间插值，写回模块级颜色变量（供主题切换动画逐帧重绘）。"""
    pa = THEMES.get(a) or THEMES["light"]
    pb = THEMES.get(b) or THEMES["light"]
    for key, va in pa.items():
        if key == "DARK_TITLE":
            continue
        vb = pb.get(key, va)
        if isinstance(va, str) and va.startswith("#"):
            globals()[key] = _mix_color(va, vb, k)
        else:
            globals()[key] = vb


def set_window_alpha(root, alpha: float | None) -> None:
    """整窗透明度：alpha=None 表示恢复不透明并去掉分层样式。"""
    import ctypes

    u = ctypes.windll.user32
    hwnd = u.GetParent(root.winfo_id())
    if not hwnd:
        return
    GWL_EXSTYLE, WS_EX_LAYERED, LWA_ALPHA = -20, 0x00080000, 0x2
    ex = u.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if alpha is None:
        if ex & WS_EX_LAYERED:
            u.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
            u.SetWindowLongW(hwnd, GWL_EXSTYLE, ex & ~WS_EX_LAYERED)
        return
    if not ex & WS_EX_LAYERED:
        u.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)
    u.SetLayeredWindowAttributes(hwnd, 0, max(0, min(255, round(alpha * 255))), LWA_ALPHA)


def system_dark() -> bool:
    """Windows 的「应用使用浅色主题」开关。"""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return not bool(value)
    except Exception:
        return False


apply_theme("light")


def _enable_dpi() -> None:
    """per-monitor DPI aware：先设好再建 Tk 窗口，否则字会糊、坐标会漂。"""
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _win11_frame(root, dark: int = 0) -> None:
    """Win11 圆角 + Mica 背景（老系统上失败就算了）。"""
    try:
        import ctypes

        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        dwm = ctypes.windll.dwmapi
        for attr, value in ((33, 2), (38, 2), (20, int(dark))):
            v = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))
        # 标题栏配色：深色时跟着卡片走，浅色时交还给系统
        if dark:
            def _cref(hexstr: str) -> int:
                r, g, b = (int(hexstr[i:i + 2], 16) for i in (1, 3, 5))
                return (b << 16) | (g << 8) | r
            for attr, val in ((35, _cref(CARD)), (36, _cref(TEXT)), (34, _cref(CARD))):
                v = ctypes.c_int(val)
                dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), 4)
        else:
            for attr in (34, 35, 36):
                v = ctypes.c_int(-1)
                dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), 4)
    except Exception:
        pass


def _round(cv, x1, y1, x2, y2, r, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return cv.create_polygon(pts, smooth=True, splinesteps=24, **kw)


class Panel:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.page = "main"
        self.logs: list[str] = []
        self.hits: list[dict] = []
        self.hover: str | None = None
        self._fresh_install = not core.SETTINGS_FILE.exists()
        self.settings = core.load_settings()
        self._apply_fonts()
        self._set_tab = "general"
        apply_theme("dark" if self._theme_pref() == "dark" else "light")
        self._redraw_job = None
        self.tray = None
        self.dash = None
        self._dash_ready = False
        self._dash_error = False
        self._dash_try_at = 0.0
        self._dash_rect = None
        self._dash_dropping = False
        self._st: dict = {}
        self._astrbot_pid = None
        self._astrbot_web = False
        self._health: dict = {}
        self._plugins: list = []
        self._plugin_loading = False
        self._plugin_page = 0
        self._plugin_warned = False
        self._switches: dict = {}
        self._segs: dict = {}
        self._pill_pos: dict = {}
        self._anim_seq: dict = {}
        self._nav_prev: str | None = None
        self._nav_t: float = 1.0
        self._nav_seq: int = 0
        self._theme_seq: int = 0

        root.title(f"大肥鱼控制台 v{core.APP_VERSION}")
        try:
            _ico = Path(core.APP_DIR) / "tools" / "bot.ico"
            if _ico.exists():
                root.iconbitmap(default=str(_ico))
        except Exception:
            pass
        root.configure(bg=BG)
        sc = self.scale()
        root.minsize(round(900 * sc), round(620 * sc))
        root.geometry(self._initial_geometry(sc))
        self.cv = tk.Canvas(root, bg=BG, highlightthickness=0, bd=0)
        self.cv.pack(fill="both", expand=True)

        self.cv.bind("<Configure>", self._schedule_redraw)
        self.cv.bind("<Motion>", self._on_motion)
        self.cv.bind("<Button-1>", self._on_click)
        self.cv.bind("<Leave>", lambda e: self._set_hover(None))

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Unmap>", self._on_unmap)

        if self._fresh_install and not self.settings.get("onboarded"):
            self.page = "guide"
        self.log("就绪 · 改完插件点「热重启 AstrBot」即可生效")
        self._guide_step = 0
        self._comp_busy: set[str] = set()
        self._comp_pct: dict[str, int] = {}
        self._comp_cancel: dict[str, object] = {}
        import queue as _queue
        self._comp_msgs: "_queue.Queue" = _queue.Queue()
        self._ui_queue: "_queue.Queue" = _queue.Queue()
        self._start_tray()
        self.root.after(120, self._drain_comp)
        self._schedule_redraw()
        threading.Thread(target=self._refresh_loop, daemon=True).start()
        threading.Thread(target=self._status_loop, daemon=True).start()
        self.root.after(120, self._apply_frame)
        self.root.after(400, self._tick_dash)
        self.root.after(1500, self._startup_check)

    # ------------------------------------------------------------ 基础
    def _apply_frame(self) -> None:
        _win11_frame(self.root, THEMES[THEME]["DARK_TITLE"])

    def _theme_pref(self) -> str:
        pref = str(self.settings.get("theme") or "light").lower()
        return pref if pref in ("light", "dark", "system") else "light"

    def _resolve_theme(self) -> str:
        pref = self._theme_pref()
        if pref == "system":
            return "dark" if system_dark() else "light"
        return pref

    def _set_theme(self, pref: str) -> None:
        pref = pref if pref in ("light", "dark", "system") else "light"
        self.settings["theme"] = pref
        core.save_settings(self.settings)
        target = self._resolve_theme()
        names = {"light": "浅色", "dark": "深色", "system": "跟随系统"}
        old = THEME
        # 让内嵌面板跟着换深浅色：重开一次 Edge（AstrBot 按 prefers-color-scheme 渲染）
        if self.dash:
            self._drop_dash()
        seq = self._theme_seq = self._theme_seq + 1

        def apply_now():
            apply_theme(target)
            try:
                self.root.configure(bg=BG)
                self.cv.configure(bg=BG)
            except Exception:
                pass
            self._apply_frame()
            self.log(f"主题：{names.get(pref, pref)}")
            self.redraw()

        if old == target:
            set_window_alpha(self.root, None)
            apply_now()
            return

        # 整窗先淡出、在最暗的一瞬换色、再淡入：比逐帧插值颜色干净（不会糊成灰）
        def step_out(p: float, seq=seq):
            if self._theme_seq != seq:
                return
            set_window_alpha(self.root, 1.0 - 0.88 * p)

        def step_in(p: float, seq=seq):
            if self._theme_seq != seq:
                return
            set_window_alpha(self.root, 0.12 + 0.88 * p)
            if p >= 1.0:
                set_window_alpha(self.root, None)

        def go(seq=seq):
            if self._theme_seq != seq:
                set_window_alpha(self.root, None)
                return
            apply_now()
            self._animate(step_in, 0.18)

        self._animate(step_out, 0.09)
        self.root.after(95, go)

    def _set_tab_to(self, key: str) -> None:
        if key == self._set_tab:
            return
        self._nav_prev = self._set_tab
        self._set_tab = key
        self._nav_t = 0.0
        seq = self._nav_seq = self._nav_seq + 1

        def step(p: float, seq=seq):
            if self._nav_seq != seq:
                return
            self._nav_t = p
            if p >= 1.0:
                self._nav_prev = None
            self.redraw()

        self._animate(step, 0.16)

    def _initial_geometry(self, sc: float) -> str:
        """逻辑尺寸乘 DPI 缩放，再夹到屏幕内，避免高 DPI 下窗口比内容小。"""
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except Exception:
            sw, sh = 1920, 1080
        lw = min(1040, max(900, int(sw / sc * 0.62)))
        lh = min(780, max(640, int(sh / sc * 0.70)))
        w = min(round(lw * sc), sw - round(40 * sc))
        h = min(round(lh * sc), sh - round(96 * sc))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - round(30 * sc))
        return f"{w}x{h}+{x}+{y}"

    def scale(self) -> float:
        """DPI 缩放 × 屏幕逻辑分辨率系数，让 1080p / 4K 都有合适的字号。"""
        try:
            dpi = self.root.winfo_fpixels("1i") / 96.0
        except Exception:
            dpi = 1.0
        try:
            lw = self.root.winfo_screenwidth() / max(dpi, 0.5)
            lh = self.root.winfo_screenheight() / max(dpi, 0.5)
            ratio = (lw * lh) / (1536.0 * 960.0)
            res = max(0.92, min(1.5, ratio ** 0.25))
        except Exception:
            res = 1.0
        return max(0.85, min(2.4, dpi * res))

    def log(self, text: str) -> None:
        self.logs.append(text)
        del self.logs[:-60]
        self._schedule_redraw()

    def _schedule_redraw(self, _e=None) -> None:
        if self._redraw_job:
            try:
                self.root.after_cancel(self._redraw_job)
            except Exception:
                pass
        self._redraw_job = self.root.after(60, self.redraw)

    # ------------------------------------------------------------ 绘制
    def redraw(self) -> None:
        import os as _os
        import time as _time

        _t0 = _time.perf_counter()
        self._redraw_job = None
        cv = self.cv
        cv.delete("all")
        self.hits = []
        self._switches = {}
        self._segs = {}
        W = cv.winfo_width()
        H = cv.winfo_height()
        if W < 80 or H < 80:
            return
        s = self.scale()
        self.s = s
        self._draw_bg(W, H, s)
        m = round(20 * s)
        # 只用后台线程刷新好的缓存：端口探测动辄 1.5s，绝不能在 UI 线程里做
        st = self._st
        self._astrbot_pid = st.get("astrbot")
        self._astrbot_web = bool(st.get("astrbot_web"))
        if self.page == "settings":
            self._draw_settings(W, H, m, s)
        elif self.page == "plugins":
            self._draw_plugins(W, H, m, s)
        elif self.page == "guide":
            self._draw_guide(W, H, m, s)
        else:
            dash_w = 0
            gap = round(12 * s)
            if W >= round(820 * s):
                # 左侧控制区宽度固定，窗口变宽时多出来的全部给右侧面板
                base_ctrl = round(404 * s)
                dash_w = max(round(360 * s), W - 2 * m - base_ctrl - gap)
                dash_w = min(dash_w, W - 2 * m - round(300 * s) - gap)
            ctrl_w = W - dash_w - (gap if dash_w else 0)
            self._draw_main(ctrl_w, H, m, s)
            if dash_w:
                x1 = W - m - dash_w
                self._dash_rect = (x1, m + round(58 * s), W - m, H - m)
                self._card(*self._dash_rect)
                self._text(x1 + round(14 * s), m + round(66 * s), "AstrBot 面板", 11, MUTED,
                           weight="bold")
                cx = (x1 + W - m) / 2
                cy = (m + H) / 2
                if not (self._astrbot_pid or self._astrbot_web):
                    # AstrBot 没跑起来就不开面板，连 Edge 都不启动
                    if self.dash:
                        self._drop_dash()
                    self._text(cx, cy - round(12 * s), "等待启动 AstrBot", 12.5, SUB, anchor="n")
                    self._text(cx, cy + round(12 * s), "点上面的「启动」，面板会在这里打开", 10.5,
                               MUTED, anchor="n")
                elif not self._astrbot_web:
                    # 进程起来了但 WebUI 还没就绪：先等着，别开一个连不上的浏览器
                    self._text(cx, cy - round(12 * s), "AstrBot 正在启动…", 12.5, SUB, anchor="n")
                    self._text(cx, cy + round(12 * s), "WebUI 就绪后会自动打开面板", 10.5,
                               MUTED, anchor="n")
                elif not self._dash_ready:
                    msg = "面板打不开，稍后自动重试" if self._dash_error else "正在打开面板…"
                    self._text(cx, cy, msg, 12, SUB, anchor="n")
                    self._maybe_boot_dash()
                else:
                    self._dock_dash()
            else:
                self._dash_rect = None
                if self.dash:
                    self.dash.hide()
                self._text(m, H - round(30 * s),
                           "窗口再拉宽一点就能在这里直接看 AstrBot 面板", 10.5, SUB)
        try:
            _ms = (_time.perf_counter() - _t0) * 1000
            if _ms > 200:
                self.log(f"重绘用时 {_ms:.0f}ms")
        except Exception:
            pass

    def _text(self, x, y, txt, size, color=TEXT, anchor="nw", weight="normal", family=None):
        fam = family or FONT_FAMILY
        px = max(7, round(size * self.s * FONT_SCALE))
        return self.cv.create_text(
            x, y, text=txt, anchor=anchor, fill=color,
            font=(fam, -px, weight),
        )

    def _card(self, x1, y1, x2, y2, r=12):
        """白卡片：极淡的投影 + 细边，做出“浮在底板上”的层次。"""
        self._shadow(x1, y1, x2, y2, r)
        return _round(self.cv, x1, y1, x2, y2, round(r * self.s),
                      fill=CARD, outline=BORDER, width=1)

    def _shadow(self, x1, y1, x2, y2, r=12, spread=2):
        """Canvas 没有真阴影，用两层极淡的圆角矩形近似。"""
        s = self.s
        for i, color in ((spread, SHADOW1), (1, SHADOW2)):
            d = round(i * s)
            _round(self.cv, x1, y1 + d, x2, y2 + d, round(r * s), fill=color, outline="")

    def _add_hit(self, x1, y1, x2, y2, cb, cursor="hand2"):
        self.hits.append({"box": (x1, y1, x2, y2), "cb": cb, "cursor": cursor})

    def _button(self, x1, y1, x2, y2, label, kind, cb, s):
        r = round(9 * s)
        if kind == "primary":
            fill, hover, fg = ACCENT, ACCENT_HOVER, ON_ACCENT
            outline, width = "", 0
            size, weight = 13, "bold"
        elif kind == "secondary":
            fill, hover, fg = CARD, BTN_HOVER, TEXT
            outline, width = BORDER, 1
            size, weight = 12.5, "normal"
        elif kind == "segment":
            fill, hover, fg = CARD, CARD, TEXT
            outline, width = "", 0
            size, weight = 12.5, "normal"
        else:  # ghost
            fill, hover, fg = BG, HOVER, SUB
            outline, width = "", 0
            size, weight = 12, "normal"
        rect = _round(self.cv, x1, y1, x2, y2, r, fill=fill,
                      outline=outline, width=width)
        self.cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=fg,
                            font=("Segoe UI Variable Text", -round(size * s), weight))
        self._add_hit(x1, y1, x2, y2, cb)
        self.hits[-1].update({"rect": rect, "fill": fill, "hover": hover})

    def _link(self, x, y, label, cb, anchor="nw", size=12):
        item = self._text(x, y, label, size, SUB, anchor)
        b = self.cv.bbox(item)
        if b:
            self._add_hit(*b, cb)
            self.hits[-1].update({"link_text": item})

    # ------------------------------------------------------------ 主页面
    def _draw_bg(self, W, H, s) -> None:
        """用户自选背景图：等比铺满 + 与白底混合，保证文字看得清。"""
        path = self.settings.get("bg_image") or ""
        if not path or not Path(path).exists():
            self._bg_photo = None
            return
        try:
            from PIL import Image, ImageTk
        except Exception:
            return
        key = (path, W, H)
        if getattr(self, "_bg_key", None) == key and getattr(self, "_bg_photo", None) is not None:
            self.cv.create_image(0, 0, image=self._bg_photo, anchor="nw")
            return
        try:
            img = Image.open(path).convert("RGB")
            ratio = max(W / img.width, H / img.height)
            nw, nh = int(img.width * ratio + 0.5), int(img.height * ratio + 0.5)
            img = img.resize((nw, nh), Image.LANCZOS)
            left = (nw - W) // 2
            top = (nh - H) // 2
            img = img.crop((left, top, left + W, top + H))
            white = Image.new("RGB", (W, H), BG)
            img = Image.blend(img, white, 0.74)
            self._bg_photo = ImageTk.PhotoImage(img)
            self._bg_key = key
            self.cv.create_image(0, 0, image=self._bg_photo, anchor="nw")
        except Exception:
            self._bg_photo = None

    def _pick_bg(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="选一张背景图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp *.webp"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.settings["bg_image"] = path
        core.save_settings(self.settings)
        self.log(f"背景已换成 {Path(path).name}")
        self._schedule_redraw()

    def _clear_bg(self) -> None:
        self.settings["bg_image"] = ""
        core.save_settings(self.settings)
        self.log("背景已恢复默认")
        self._schedule_redraw()

    def _draw_main(self, W, H, m, s) -> None:
        cv = self.cv
        st = self._st or {}

        self._text(m, m - 2, "大肥鱼控制台", 19, TEXT, weight="bold",
                   )
        self._text(m, m + round(26 * s), "AstrBot · SnowLuma · QQ", 10.5, MUTED)
        # 右上角设置：小胶囊按钮，比裸链接更像现代工具栏
        bw, bh = round(58 * s), round(26 * s)
        gap_h = round(6 * s)
        self._button(W - m - bw, m - round(2 * s), W - m, m - round(2 * s) + bh,
                     "设置", "secondary", self._open_settings, s)
        self._button(W - m - bw * 2 - gap_h, m - round(2 * s),
                     W - m - bw - gap_h, m - round(2 * s) + bh,
                     "插件", "secondary", self._open_plugins, s)

        # 状态卡：圆点 + 名称 + 右侧状态胶囊
        y = m + round(54 * s)
        row_h = round(30 * s)
        card_h = row_h * 3 + round(12 * s)
        self._card(m, y, W - m, y + card_h)
        rows = [("astrbot", "AstrBot"), ("snowluma", "SnowLuma"), ("qq", "QQ")]
        for i, (key, name) in enumerate(rows):
            cy = y + round(6 * s) + row_h * i + row_h / 2
            pid = st.get(key)
            cv.create_oval(m + round(14 * s), cy - round(3.5 * s),
                           m + round(21 * s), cy + round(3.5 * s),
                           fill=GREEN if pid else GREY_DOT, outline="")
            name_item = self._text(m + round(30 * s), cy, name, 12.5, TEXT, anchor="w")
            info = self._health.get(key) or {}
            good = bool(info.get("installed"))
            box = cv.bbox(name_item)
            tag_x = (box[2] if box else m + round(90 * s)) + round(8 * s)
            self._text(tag_x, cy, "已安装" if good else "缺文件", 9.5,
                       GREEN if good else DANGER, anchor="w")
            label = "运行中" if pid else "未运行"
            tw = round(54 * s)
            chip_r = W - m - round(14 * s)
            if not good:
                bw2, bh2 = round(58 * s), round(24 * s)
                if key in self._comp_busy:
                    pct = self._comp_pct.get(key)
                    txt = f"取消 {pct}%" if pct else "取消"
                    self._button(chip_r - bw2, cy - bh2 / 2, chip_r, cy + bh2 / 2,
                                 txt, "ghost",
                                 lambda k=key: self._cancel_component(k), s)
                elif False:
                    pass
                else:
                    self._button(chip_r - bw2, cy - bh2 / 2, chip_r, cy + bh2 / 2,
                                 "下载", "secondary",
                                 lambda k=key: self._install_component(k), s)
                chip_r -= bw2 + round(8 * s)
            self._chip(chip_r - tw, cy - round(9 * s),
                       chip_r, cy + round(9 * s),
                       label, GREEN if pid else MUTED)
            if pid:
                self._text(chip_r - round(6 * s) - tw, cy, str(pid), 10.5, MUTED, anchor="e")

        # 主要动作：启动 / 全部停止
        gap = round(8 * s)
        btns_y = y + card_h + round(12 * s)
        bh1 = round(40 * s)
        half = (W - 2 * m - gap) / 2
        self._button(m, btns_y, m + half, btns_y + bh1, "启动", "primary", self.start_all, s)
        self._button(W - m - half, btns_y, W - m, btns_y + bh1, "全部停止", "secondary",
                     self.stop_all, s)

        # 次一级动作：2×2 网格
        y2 = btns_y + bh1 + gap
        bh2 = round(32 * s)
        self._button(m, y2, m + half, y2 + bh2, "热重启 AstrBot", "secondary",
                     self.hot_restart, s)
        self._button(W - m - half, y2, W - m, y2 + bh2, "重启协议端", "secondary",
                     self.restart_proto, s)
        y3 = y2 + bh2 + gap
        self._button(m, y3, m + half, y3 + bh2, "全部重启", "ghost", self.restart_all, s)
        self._button(W - m - half, y3, W - m, y3 + bh2, "打开面板", "ghost",
                     self.open_panels, s)

        # 日志卡（吃掉剩余空间）
        log_top = y3 + bh2 + round(12 * s)
        log_bottom = H - round(48 * s)
        if log_bottom - log_top < round(60 * s):
            log_bottom = log_top + round(60 * s)
        self._card(m, log_top, W - m, log_bottom)
        self._text(m + round(14 * s), log_top + round(11 * s), "日志", 11, MUTED, weight="bold")
        cv.create_line(m + round(14 * s), log_top + round(30 * s), W - m - round(14 * s),
                       log_top + round(30 * s), fill=BORDER)
        line_h = round(17.5 * s)
        avail = int((log_bottom - log_top - round(38 * s)) // line_h)
        shown = self.logs[-max(1, avail):] if avail > 0 else []
        ly = log_top + round(38 * s)
        for line in shown:
            cv.create_text(m + round(14 * s), ly, text=line[:220], anchor="nw",
                           fill=SUB, font=("Cascadia Mono", -round(10 * s)))
            ly += line_h
        if not shown:
            cv.create_text(m + round(14 * s), ly, text="还没有日志", anchor="nw",
                           fill=MUTED, font=("Segoe UI Variable Text", -round(10.5 * s)))

        # 底部链接
        fy = H - round(28 * s)
        self._link(m, fy, "看日志", self.open_logs)
        self._link(m + round(74 * s), fy, "打开目录", self.open_dir)
        self._link(m + round(164 * s), fy, "复制状态", self.copy_status)

    def _chip(self, x1, y1, x2, y2, label, color):
        """小号状态胶囊。"""
        _round(self.cv, x1, y1, x2, y2, (y2 - y1) / 2, fill=CHIP, outline="")
        self.cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=color,
                            font=("Segoe UI Variable Text", -round(9.5 * self.s)))

    # ------------------------------------------------------------ 设置页
    SETTING_TABS = (
        ("general", "常规", "开关与启动"),
        ("appearance", "外观", "主题与背景"),
        ("behavior", "行为", "关闭与退出"),
        ("about", "关于", "版本与路径"),
    )

    def _draw_settings(self, W, H, m, s) -> None:
        cv = self.cv
        self._text(m, m - 2, "设置", 19, TEXT, weight="bold",
                   )
        self._text(m, m + round(26 * s), "分类设置 · 改完立即生效", 10.5, MUTED)
        bw, bh = round(66 * s), round(28 * s)
        self._button(W - m - bw, m - round(3 * s), W - m, m - round(3 * s) + bh,
                     "返回", "secondary", self._open_main, s)

        top = m + round(54 * s)
        bottom = H - round(26 * s)
        nav_w = round(190 * s)
        nav_x2 = m + nav_w
        item_h = round(42 * s)
        nav_h = round(20 * s) + (item_h + round(3 * s)) * len(self.SETTING_TABS)
        self._card(m, top, nav_x2, top + nav_h)
        keys = [k for k, _, _ in self.SETTING_TABS]
        cur_i = keys.index(self._set_tab) if self._set_tab in keys else 0
        prev_i = keys.index(self._nav_prev) if self._nav_prev in keys else None
        t = 1.0 if prev_i is None else max(0.0, min(1.0, self._nav_t))
        animating = prev_i is not None and t < 1.0
        step_y = item_h + round(3 * s)

        def item_y(i: int):
            return top + round(10 * s) + step_y * i

        x1, x2 = m + round(8 * s), nav_x2 - round(8 * s)
        # 选中块在两行之间滑动：滑的过程中先画成描边“选框”，到位后再填色，
        # 这样文字不会被半透明色块盖住，也顺带有了进度感。
        fill_k = 1.0 if not animating else max(0.0, (t - 0.72) / 0.28)
        y_prev = item_y(prev_i if prev_i is not None else cur_i)
        y_cur = item_y(cur_i)
        hy = y_prev + (y_cur - y_prev) * t
        if fill_k <= 0.01:
            _round(cv, x1, hy, x2, hy + item_h, round(8 * s), fill="",
                   outline=ACCENT, width=round(2 * s))
        else:
            _round(cv, x1, hy, x2, hy + item_h, round(8 * s),
                   fill=self._mix(CARD, ACCENT, fill_k),
                   outline="" if fill_k > 0.5 else ACCENT,
                   width=round(2 * s))

        for i, (key, label, sub) in enumerate(self.SETTING_TABS):
            y = item_y(i)
            self._add_hit(x1, y, x2, y + item_h, lambda k=key: self._set_tab_to(k))
            active = (i == cur_i)
            a = fill_k if active else 0.0
            tx = x1 + round(12 * s)
            ly = y + (item_h / 2 + (item_h * 0.34 - item_h / 2) * a)
            cv.create_text(tx, ly, text=label, anchor="w",
                           fill=self._mix(TEXT, ON_ACCENT, a),
                           font=("Segoe UI Variable Text", -round(12.5 * s),
                                 "bold" if a > 0.5 else "normal"))
            if active and a > 0.75:
                cv.create_text(tx, y + item_h * 0.70, text=sub, anchor="w",
                               fill=ON_ACCENT,
                               font=("Segoe UI Variable Text", -round(9.5 * s)))

        cx1 = nav_x2 + round(14 * s)
        cx2 = W - m
        if self._set_tab == "appearance":
            self._settings_appearance(cx1, top, cx2, bottom, s)
        elif self._set_tab == "behavior":
            self._settings_behavior(cx1, top, cx2, bottom, s)
        elif self._set_tab == "about":
            self._settings_about(cx1, top, cx2, bottom, s)
        else:
            self._settings_general(cx1, top, cx2, bottom, s)

    # ------------------------------------------------------------ 新手引导
    GUIDE_STEPS = (
        ("check", "检查组件", "备齐三样东西"),
        ("start", "启动服务", "让机器人跑起来"),
        ("qq", "登录 QQ", "扫码登录机器人号"),
        ("link", "连接机器人", "把 AstrBot 接到 SnowLuma"),
        ("done", "完成", "开始用起来"),
    )

    def _open_guide(self) -> None:
        self.page = "guide"
        self._guide_step = 0
        self._schedule_redraw()

    def _guide_go(self, step: int) -> None:
        self._guide_step = max(0, min(len(self.GUIDE_STEPS) - 1, step))
        self._schedule_redraw()

    def _guide_finish(self) -> None:
        self.settings["onboarded"] = True
        core.save_settings(self.settings)
        self.page = "main"
        self.log("新手引导已完成，可以点「启动」了")
        self._schedule_redraw()

    def _guide_skip(self) -> None:
        self.settings["onboarded"] = True
        core.save_settings(self.settings)
        self.page = "main"
        self.log("已跳过新手引导，之后可在「设置 → 关于」里重新打开")
        self._schedule_redraw()

    def _guide_copy(self, text: str) -> None:
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.log(f"已复制：{text}")
        except Exception:
            pass

    def _guide_open_web(self, key: str) -> None:
        import webbrowser

        url = core.PATHS.get(key) or ""
        if url:
            webbrowser.open(url)

    def _draw_guide(self, W, H, m, s) -> None:
        cv = self.cv
        self._text(m, m - 2, "新手引导", 19, TEXT, weight="bold",
                   )
        self._text(m, m + round(26 * s),
                   "跟着四步走：装好组件 → 启动服务 → 扫码登录 QQ → 把 AstrBot 接上",
                   10.5, MUTED)
        bw, bh = round(66 * s), round(28 * s)
        self._button(W - m - bw, m - round(3 * s), W - m, m - round(3 * s) + bh,
                     "跳过", "ghost", self._guide_skip, s)

        top = m + round(56 * s)
        bottom = H - round(26 * s)
        nav_w = round(196 * s)
        item_h = round(44 * s)
        nav_x2 = m + nav_w
        nav_h = round(18 * s) + item_h * len(self.GUIDE_STEPS)
        self._card(m, top, nav_x2, top + nav_h)

        for i, (_key, label, sub) in enumerate(self.GUIDE_STEPS):
            y = top + round(9 * s) + item_h * i
            active = i == self._guide_step
            done = i < self._guide_step
            if active:
                _round(cv, m + round(8 * s), y, nav_x2 - round(8 * s), y + item_h,
                       round(8 * s), fill=ACCENT, outline="")
            if done:
                cx, cy = m + round(26 * s), y + item_h / 2
                cv.create_oval(cx - round(9 * s), cy - round(9 * s),
                               cx + round(9 * s), cy + round(9 * s), fill=GREEN, outline="")
                self._text(cx, cy, "✓", 9, "#FFFFFF", anchor="center")
            else:
                cx, cy = m + round(26 * s), y + item_h / 2
                cv.create_oval(cx - round(9 * s), cy - round(9 * s),
                               cx + round(9 * s), cy + round(9 * s),
                               fill="" if not active else ON_ACCENT,
                               outline=(ON_ACCENT if active else BORDER), width=1)
                self._text(cx, cy, str(i + 1), 9,
                           ACCENT if active else MUTED, anchor="center")
            tx = m + round(44 * s)
            ly = y + (item_h / 2 if not active else item_h * 0.38)
            cv.create_text(tx, ly, text=label, anchor="w",
                           fill=ON_ACCENT if active else TEXT,
                           font=("Segoe UI Variable Text", -round(12.5 * s),
                                 "bold" if active else "normal"))
            if active:
                cv.create_text(tx, y + item_h * 0.70, text=sub, anchor="w",
                               fill=ON_ACCENT,
                               font=("Segoe UI Variable Text", -round(9.5 * s)))
            self._add_hit(m + round(8 * s), y, nav_x2 - round(8 * s), y + item_h,
                          lambda k=i: self._guide_go(k))

        x1 = nav_x2 + round(14 * s)
        x2 = W - m
        self._card(x1, top, x2, bottom)
        step_key = self.GUIDE_STEPS[self._guide_step][0]
        if step_key == "check":
            self._guide_check(x1, top, x2, bottom, s)
        elif step_key == "start":
            self._guide_start(x1, top, x2, bottom, s)
        elif step_key == "qq":
            self._guide_qq(x1, top, x2, bottom, s)
        elif step_key == "link":
            self._guide_link(x1, top, x2, bottom, s)
        else:
            self._guide_done(x1, top, x2, bottom, s)

        # 底部导航
        bh2 = round(32 * s)
        by = H - round(22 * s) - bh2
        self._button(x2 - round(120 * s), by, x2, by + bh2,
                     "完成配置" if self._guide_step == len(self.GUIDE_STEPS) - 1 else "下一步",
                     "primary",
                     self._guide_finish if self._guide_step == len(self.GUIDE_STEPS) - 1
                     else (lambda: self._guide_go(self._guide_step + 1)), s)
        if self._guide_step > 0:
            self._button(x2 - round(120 * s) - round(96 * s), by,
                         x2 - round(120 * s) - round(8 * s), by + bh2,
                         "上一步", "secondary",
                         lambda: self._guide_go(self._guide_step - 1), s)

    def _guide_body(self, x1, y1, x2, y2, s) -> tuple[float, float, float]:
        tx = x1 + round(22 * s)
        tw = (x2 - round(22 * s)) - tx
        return tx, y1 + round(20 * s), tw

    def _guide_check(self, x1, y1, x2, y2, s) -> None:
        cv = self.cv
        tx, ty, tw = self._guide_body(x1, y1, x2, y2, s)
        self._text(tx, ty, "第一步 · 备齐三样东西", 14, TEXT, weight="bold", anchor="w")
        self._text(tx, ty + round(24 * s),
                   "缺哪个就点右边的「安装」，AstrBot / SnowLuma 会自动下载，QQ 会打开官方下载页。",
                   10.5, SUB, anchor="w")

        rows = [("astrbot", "AstrBot", "机器人本体，网页控制台"), ("snowluma", "SnowLuma", "QQ 协议端，负责登录 QQ"),
                ("qq", "QQ", "扫码登录的客户端")]
        ry = ty + round(56 * s)
        row_h = round(58 * s)
        for key, name, desc in rows:
            info = self._health.get(key) or {}
            good = bool(info.get("installed"))
            _round(self.cv, tx, ry, tx + tw, ry + row_h - round(8 * s),
                   round(10 * s), fill=CHIP, outline="")
            cv.create_oval(tx + round(16 * s), ry + row_h / 2 - round(4 * s),
                           tx + round(24 * s), ry + row_h / 2 + round(4 * s),
                           fill=GREEN if good else GREY_DOT, outline="")
            self._text(tx + round(34 * s), ry + round(13 * s), name, 12.5, TEXT, anchor="w")
            self._text(tx + round(34 * s), ry + round(32 * s), desc, 9.5, MUTED, anchor="w")
            bw2, bh2 = round(64 * s), round(26 * s)
            bx2 = tx + tw - round(14 * s)
            if good:
                self._text(bx2, ry + row_h / 2 - round(4 * s), "已就绪", 10, GREEN, anchor="e")
            elif key in self._comp_busy:
                pct = self._comp_pct.get(key)
                self._button(bx2 - bw2, ry + round(8 * s), bx2,
                             ry + round(8 * s) + bh2, f"取消 {pct}%" if pct else "取消",
                             "ghost", lambda k=key: self._cancel_component(k), s)
            else:
                self._button(bx2 - bw2, ry + round(8 * s), bx2,
                             ry + round(8 * s) + bh2, "安装", "secondary",
                             lambda k=key: self._install_component(k), s)
            ry += row_h

        self._button(tx, ry + round(4 * s), tx + round(96 * s), ry + round(36 * s),
                     "重新检测", "ghost", self._guide_recheck, s)

    def _guide_recheck(self) -> None:
        try:
            self._health = core.component_health()
        except Exception:
            pass
        self.log("已重新检测组件")
        self._schedule_redraw()

    def _guide_start(self, x1, y1, x2, y2, s) -> None:
        cv = self.cv
        tx, ty, tw = self._guide_body(x1, y1, x2, y2, s)
        self._text(tx, ty, "第二步 · 把服务跑起来", 14, TEXT, weight="bold", anchor="w")
        self._text(tx, ty + round(24 * s),
                   "点「一键启动」会依次拉起 AstrBot、SnowLuma（和 QQ）。首次启动 AstrBot 大约要 15–30 秒。",
                   10.5, SUB, anchor="w")

        rows = [("astrbot", "AstrBot"), ("snowluma", "SnowLuma"), ("qq", "QQ")]
        ry = ty + round(56 * s)
        for key, name in rows:
            pid = self._st.get(key)
            good = pid is not None
            _round(self.cv, tx, ry, tx + tw, ry + round(44 * s),
                   round(10 * s), fill=CHIP, outline="")
            cv.create_oval(tx + round(16 * s), ry + round(22 * s) - round(4 * s),
                           tx + round(24 * s), ry + round(22 * s) + round(4 * s),
                           fill=GREEN if good else GREY_DOT, outline="")
            self._text(tx + round(34 * s), ry + round(22 * s), name, 12, TEXT, anchor="w")
            self._text(tx + tw - round(16 * s), ry + round(22 * s),
                       ("运行中" + (f" · {pid}" if pid else "")) if good else "未运行",
                       10, GREEN if good else MUTED, anchor="e")
            ry += round(52 * s)

        self._button(tx, ry + round(6 * s), tx + round(132 * s), ry + round(40 * s),
                     "一键启动", "primary", self.start_all, s)
        self._button(tx + round(142 * s), ry + round(6 * s), tx + round(254 * s),
                     ry + round(40 * s), "刷新状态", "ghost", self._guide_recheck, s)
        self._text(tx, ry + round(60 * s),
                   "端口：AstrBot 6185 · SnowLuma 5099（都是在后台跑，不用管命令行窗口）",
                   9.5, MUTED, anchor="w")

    def _guide_dir(self, key: str) -> None:
        import os

        path = core.PATHS.get(key) or ""
        if path:
            try:
                os.startfile(path)
            except Exception:
                pass

    def _guide_qq(self, x1, y1, x2, y2, s) -> None:
        tx, ty, tw = self._guide_body(x1, y1, x2, y2, s)
        self._text(tx, ty, "第三步 · 登录要挂机器人的 QQ", 14, TEXT, weight="bold", anchor="w")
        self._text(tx, ty + round(24 * s),
                   "SnowLuma 把 QQ 挂上后转成 OneBot 协议；扫码这一步得你本人来，程序代替不了。",
                   10.5, SUB, anchor="w")

        steps = [
            ("1", "点「打开 SnowLuma 面板」，会自动打开 127.0.0.1:5099"),
            ("2", "首次登录用账号 admin；初始密码在 SnowLuma 的 console.log 里"),
            ("3", "日志里搜「initial credentials」，形如 user=admin password=xxxx"),
            ("4", "用要当机器人的 QQ 扫码登录，手机上点确认"),
            ("5", "看到「已连接 / 在线」后，回来点「下一步」"),
        ]
        ry = ty + round(56 * s)
        for num, text in steps:
            self.cv.create_oval(tx, ry + round(2 * s), tx + round(18 * s), ry + round(20 * s),
                                fill=CHIP, outline="")
            self._text(tx + round(9 * s), ry + round(11 * s), num, 9.5, SUB, anchor="center")
            self._text(tx + round(28 * s), ry + round(11 * s), text, 11, TEXT, anchor="w")
            ry += round(30 * s)

        # 初始密码提示卡
        card_y = ry + round(8 * s)
        _round(self.cv, tx, card_y, tx + tw, card_y + round(78 * s),
               round(10 * s), fill=CHIP, outline=BORDER, width=1)
        self._text(tx + round(16 * s), card_y + round(12 * s),
                   "找不到初始密码？", 10.5, TEXT, weight="bold", anchor="w")
        self._text(tx + round(16 * s), card_y + round(32 * s),
                   "打开 SnowLuma 目录里的 console.log，搜「initial credentials」。", 9.5, SUB,
                   anchor="w")
        self._text(tx + round(16 * s), card_y + round(50 * s),
                   "登录页也能选「使用访问令牌」，令牌在 配置 → 服务（远程访问）里生成。", 9.5, SUB,
                   anchor="w")
        self._button(tx + tw - round(152 * s), card_y + round(22 * s),
                     tx + tw - round(14 * s), card_y + round(56 * s),
                     "打开 SnowLuma 目录", "secondary",
                     lambda: self._guide_dir("snowluma_dir"), s)

        by = card_y + round(92 * s)
        self._button(tx, by, tx + round(168 * s), by + round(34 * s),
                     "打开 SnowLuma 面板", "primary",
                     lambda: self._guide_open_web("snowluma_web"), s)
        self._text(tx, by + round(46 * s),
                   "提示：SnowLuma 必须先启动（上一步），这个面板才打得开。", 9.5, MUTED, anchor="w")

    def _guide_link(self, x1, y1, x2, y2, s) -> None:
        tx, ty, tw = self._guide_body(x1, y1, x2, y2, s)
        self._text(tx, ty, "第四步 · 让 AstrBot 连上 SnowLuma", 14, TEXT, weight="bold", anchor="w")
        self._text(tx, ty + round(24 * s),
                   "在 AstrBot 里加一个 aiocqhttp 适配器，把下面的地址和 SnowLuma 的令牌填进去。",
                   10.5, SUB, anchor="w")

        url = "ws://127.0.0.1:6199/ws"
        box_y = ty + round(54 * s)
        _round(self.cv, tx, box_y, tx + tw, box_y + round(48 * s),
               round(10 * s), fill=CHIP, outline=BORDER, width=1)
        self._text(tx + round(16 * s), box_y + round(24 * s), url, 12, TEXT,
                   anchor="w", family="Consolas")
        self._button(tx + tw - round(88 * s), box_y + round(10 * s), tx + tw - round(14 * s),
                     box_y + round(38 * s), "复制", "secondary",
                     lambda: self._guide_copy(url), s)
        self._add_hit(tx + round(14 * s), box_y + round(6 * s), tx + tw - round(92 * s),
                      box_y + round(42 * s), lambda: self._guide_copy(url))

        self._text(tx, box_y + round(62 * s), "在 AstrBot 面板里这样配", 11, TEXT,
                   weight="bold", anchor="w")
        steps = [
            ("1", "左侧「平台」→「新增平台」→ 选 aiocqhttp"),
            ("2", "ID 随便填（例如 qq），把「启用」打开"),
            ("3", "「反向 WS 地址」粘贴上面的 ws://127.0.0.1:6199/ws"),
            ("4", "「访问令牌」粘贴 SnowLuma 里那串令牌（见下方卡片）"),
            ("5", "保存后平台列表显示「在线」，回 QQ 里 @ 机器人试一句"),
        ]
        ry = box_y + round(84 * s)
        for num, text in steps:
            self.cv.create_oval(tx, ry + round(2 * s), tx + round(18 * s), ry + round(20 * s),
                                fill=CHIP, outline="")
            self._text(tx + round(9 * s), ry + round(11 * s), num, 9.5, SUB, anchor="center")
            self._text(tx + round(28 * s), ry + round(11 * s), text, 11, TEXT, anchor="w")
            ry += round(28 * s)

        card_y = ry + round(8 * s)
        _round(self.cv, tx, card_y, tx + tw, card_y + round(96 * s),
               round(10 * s), fill=CHIP, outline=BORDER, width=1)
        self._text(tx + round(16 * s), card_y + round(12 * s),
                   "SnowLuma 的访问令牌在哪", 10.5, TEXT, weight="bold", anchor="w")
        self._text(tx + round(16 * s), card_y + round(32 * s),
                   "打开 SnowLuma 面板 → 左侧「配置」→ 顶部切到「客户端」→ 找到"
                   " ws://127.0.0.1:6199/ws 这一行", 9.5, SUB, anchor="w")
        self._text(tx + round(16 * s), card_y + round(50 * s),
                   "→「令牌」点眼睛显示、点复制复制；改完保存，SnowLuma 会自动热重载",
                   9.5, SUB, anchor="w")
        self._text(tx + round(16 * s), card_y + round(70 * s),
                   "两边令牌必须一致；本机连接也可以都留空，但要“都空”。", 9.5, AMBER,
                   anchor="w")

        by = card_y + round(110 * s)
        self._button(tx, by, tx + round(168 * s), by + round(34 * s),
                     "打开 AstrBot 面板", "primary",
                     lambda: self._guide_open_web("astrbot_web"), s)
        self._button(tx + round(180 * s), by, tx + round(180 * s) + round(168 * s),
                     by + round(34 * s), "打开 SnowLuma 面板", "secondary",
                     lambda: self._guide_open_web("snowluma_web"), s)

    def _guide_done(self, x1, y1, x2, y2, s) -> None:
        cv = self.cv
        tx, ty, tw = self._guide_body(x1, y1, x2, y2, s)
        self._text(tx, ty, "都搞定了", 16, TEXT, weight="bold", anchor="w")
        self._text(tx, ty + round(28 * s),
                   "点「完成配置」回到主界面，以后只需要点「启动」，面板会自己出现在右边。",
                   10.5, SUB, anchor="w")

        rows = [("astrbot", "AstrBot", "机器人本体"), ("snowluma", "SnowLuma", "QQ 协议端"),
                ("qq", "QQ", "已登录的客户端")]
        ry = ty + round(64 * s)
        for key, name, desc in rows:
            ok = bool(self._st.get(key))
            _round(self.cv, tx, ry, tx + tw, ry + round(42 * s),
                   round(10 * s), fill=CHIP, outline="")
            cv.create_oval(tx + round(16 * s), ry + round(21 * s) - round(4 * s),
                           tx + round(24 * s), ry + round(21 * s) + round(4 * s),
                           fill=GREEN if ok else GREY_DOT, outline="")
            self._text(tx + round(34 * s), ry + round(21 * s), f"{name} · {desc}", 11.5,
                       TEXT, anchor="w")
            self._text(tx + tw - round(16 * s), ry + round(21 * s),
                       "就绪" if ok else "还没启动", 10, GREEN if ok else AMBER, anchor="e")
            ry += round(50 * s)

        self._text(tx, ry + round(10 * s),
                   "之后想再看这份引导：设置 → 关于 → 重新打开新手引导", 9.5, MUTED, anchor="w")

    # ------------------------------------------------------------ 分类内容
    def _settings_general(self, x1, y1, x2, y2, s) -> None:
        rows = [
            ("peak_gate", "谷时门禁", "工作日 9:00-12:00 / 14:00-18:00 不自动启动"),
            ("auto_qq", "启动时拉起 QQ", "点「启动」时顺带把 QQ 打开"),
        ]
        row_h = round(64 * s)
        card_h = row_h * len(rows) + round(8 * s)
        self._card(x1, y1, x2, y1 + card_h)
        for i, (key, title, desc) in enumerate(rows):
            cy = y1 + round(4 * s) + row_h * i
            if i:
                self.cv.create_line(x1 + round(16 * s), cy, x2 - round(16 * s), cy,
                                    fill=BORDER)
            self._text(x1 + round(18 * s), cy + round(14 * s), title, 13, TEXT)
            self._text(x1 + round(18 * s), cy + round(36 * s), desc, 10.5, MUTED)
            self._switch(x2 - round(18 * s) - round(40 * s), cy + round(22 * s),
                         bool(self.settings.get(key)), key, s)
        self._text(x1 + round(2 * s), y1 + card_h + round(12 * s),
                   "这些开关只影响控制台本身，不会改 AstrBot 的配置。", 10.5, MUTED)

    def _apply_fonts(self) -> None:
        global FONT_FAMILY, FONT_SCALE

        fam = str(self.settings.get("font_family") or "")
        FONT_FAMILY = fam or "Segoe UI Variable Text"
        try:
            FONT_SCALE = float(self.settings.get("font_scale") or 1.0)
        except (TypeError, ValueError):
            FONT_SCALE = 1.0
        FONT_SCALE = max(0.8, min(1.45, FONT_SCALE))

    def _set_font_scale(self, value: str) -> None:
        try:
            val = float(value)
        except (TypeError, ValueError):
            val = 1.0
        self.settings["font_scale"] = val
        core.save_settings(self.settings)
        self._apply_fonts()
        self.log(f"字号：{dict(FONT_SIZES).get(val, val)}")
        self._schedule_redraw()

    def _set_font_family(self, value: str) -> None:
        self.settings["font_family"] = value
        core.save_settings(self.settings)
        self._apply_fonts()
        name = dict((k or "", v) for k, v in FONT_CHOICES).get(value, value or "系统默认")
        self.log(f"字体：{name}")
        self._schedule_redraw()

    def _settings_appearance(self, x1, y1, x2, y2, s) -> None:
        # 主题
        card_h = round(128 * s)
        self._card(x1, y1, x2, y1 + card_h)
        self._text(x1 + round(18 * s), y1 + round(16 * s), "主题", 13, TEXT, weight="bold")
        self._text(x1 + round(18 * s), y1 + round(38 * s),
                   "深色模式适合夜里用，跟随系统会跟着 Windows 的应用主题走。",
                   10.5, MUTED)
        opts = [("light", "浅色"), ("dark", "深色"), ("system", "跟随系统")]
        bx = x1 + round(18 * s)
        by = y1 + round(64 * s)
        seg_h = round(36 * s)
        seg_w = min(round(360 * s), (x2 - x1) - round(36 * s))
        self._segmented(bx, by, seg_w, seg_h, opts, self._theme_pref(),
                        self._set_theme, s, "theme")

        # 字体
        font_y = y1 + card_h + round(16 * s)
        font_h = round(146 * s)
        self._card(x1, font_y, x2, font_y + font_h)
        self._text(x1 + round(18 * s), font_y + round(16 * s), "字体", 13, TEXT, weight="bold")
        self._text(x1 + round(18 * s), font_y + round(38 * s),
                   "字号只影响文字大小，不改布局；换台屏幕或改分辨率后会按新的 DPI 自动适配。",
                   10.5, MUTED)

        self._text(x1 + round(18 * s), font_y + round(64 * s), "字号", 10.5, SUB)
        size_opts = [(str(v), label) for v, label in FONT_SIZES]
        cur_scale = str(float(self.settings.get("font_scale") or 1.0))
        self._segmented(x1 + round(72 * s), font_y + round(56 * s),
                        round(300 * s), round(32 * s), size_opts, cur_scale,
                        self._set_font_scale, s, "font_size")

        self._text(x1 + round(18 * s), font_y + round(108 * s), "字体", 10.5, SUB)
        fam_opts = [(k, label) for k, label in FONT_CHOICES]
        cur_fam = str(self.settings.get("font_family") or "")
        if cur_fam not in dict(fam_opts):
            cur_fam = ""
        self._segmented(x1 + round(72 * s), font_y + round(100 * s),
                        round(360 * s), round(32 * s), fam_opts, cur_fam,
                        self._set_font_family, s, "font_family")

        # 自定义背景
        by2 = font_y + font_h + round(16 * s)
        row_h = round(70 * s)
        self._card(x1, by2, x2, by2 + row_h)
        self._text(x1 + round(18 * s), by2 + round(16 * s), "自定义背景", 13, TEXT)
        cur_bg = self.settings.get("bg_image") or ""
        desc = Path(cur_bg).name if cur_bg else "选一张图片当面板背景（会自动淡化，不挡住文字）"
        self._text(x1 + round(18 * s), by2 + round(38 * s), desc, 10.5, MUTED)
        tw = round(56 * s)
        self._button(x2 - round(18 * s) - tw, by2 + round(21 * s), x2 - round(18 * s),
                     by2 + round(21 * s) + round(28 * s), "选择", "secondary",
                     self._pick_bg, s)
        if cur_bg:
            tw2 = round(44 * s)
            self._button(x2 - round(26 * s) - tw - tw2, by2 + round(21 * s),
                         x2 - round(26 * s) - tw, by2 + round(21 * s) + round(28 * s),
                         "清除", "ghost", self._clear_bg, s)

    def _settings_behavior(self, x1, y1, x2, y2, s) -> None:
        seg_h = round(36 * s)
        block_h = round(46 * s) + seg_h + round(18 * s)
        self._card(x1, y1, x2, y1 + block_h)
        self._text(x1 + round(18 * s), y1 + round(16 * s), "关闭窗口时", 13, TEXT,
                   weight="bold")
        opts = [("ask", "每次询问"), ("tray", "最小化到后台"), ("quit", "直接退出")]
        bx = x1 + round(18 * s)
        by = y1 + round(46 * s)
        seg_w = min(round(520 * s), (x2 - x1) - round(36 * s))
        self._segmented(bx, by, seg_w, seg_h, opts,
                        self.settings.get("close_action", "ask"),
                        self._set_close_action, s, "close")
        self._text(x1 + round(2 * s), y1 + block_h + round(12 * s),
                   "提示：关掉控制台不会停机器人，AstrBot / SnowLuma 会继续在后台跑。",
                   10.5, MUTED)

    def _settings_about(self, x1, y1, x2, y2, s) -> None:
        info = core.release_info()
        repo = str(info.get("repo") or "")
        rows = [
            ("版本", f"{info.get('name', '大肥鱼控制台')} v{info.get('version', '0.0.0')}"
                     + (f" · {info.get('build')} 构建" if info.get("build") else "")),
            ("开源协议", str(info.get("license") or "MIT")
                     + (f" · {info.get('author')}" if info.get("author") else "")),
            ("开源仓库", repo or "未配置（在 tools/release.json 里填 repo 即可）"),
            ("运行目录", str(core.APP_DIR)),
            ("插件目录", str(core.PLUGINS_DIR)),
        ]
        row_h = round(56 * s)
        card_h = row_h * len(rows) + round(8 * s)
        self._card(x1, y1, x2, y1 + card_h)
        for i, (title, value) in enumerate(rows):
            cy = y1 + round(4 * s) + row_h * i
            if i:
                self.cv.create_line(x1 + round(16 * s), cy, x2 - round(16 * s), cy,
                                    fill=BORDER)
            self._text(x1 + round(18 * s), cy + round(11 * s), title, 11, MUTED)
            is_repo = title == "开源仓库" and repo
            self._text(x1 + round(18 * s), cy + round(31 * s), value,
                       12 if not is_repo else 11.5,
                       ACCENT if is_repo else TEXT)
            if is_repo:
                bx1 = x1 + round(18 * s)
                bx2 = min(x2 - round(18 * s), bx1 + round(520 * s))
                self._add_hit(bx1, cy + round(26 * s), bx2, cy + round(50 * s),
                              lambda u=repo: self._open_url(u))

        by = y1 + card_h + round(16 * s)
        bw = round(120 * s)
        gap = round(10 * s)
        self._button(x1, by, x1 + bw * 1.25, by + round(32 * s), "打开仓库",
                     "primary", lambda: self._open_url(repo), s)
        self._button(x1 + bw * 1.25 + gap, by, x1 + bw * 2.25 + gap,
                     by + round(32 * s), "复制仓库地址", "secondary",
                     lambda: self._guide_copy(repo), s)
        by2 = by + round(42 * s)
        self._button(x1, by2, x1 + bw, by2 + round(32 * s), "打开日志目录",
                     "secondary", self.open_dir, s)
        self._button(x1 + bw + gap, by2, x1 + bw * 2 + gap, by2 + round(32 * s),
                     "插件体检", "secondary", self._open_plugins, s)
        self._button(x1 + bw * 2 + gap * 2, by2, x1 + bw * 3 + gap * 2,
                     by2 + round(32 * s), "新手引导", "secondary",
                     self._open_guide, s)
        self._text(x1, by2 + round(46 * s),
                   "面板、主题、插件清单都放在运行目录里，换机器时整个目录拷走即可。",
                   10.5, MUTED)

    def _open_url(self, url: str) -> None:
        import webbrowser

        if url:
            webbrowser.open(url)

    # ------------------------------------------------------------ 动画
    @staticmethod
    def _ease(p: float) -> float:
        """smoothstep：两头慢、中间快，接近 iOS 开关的手感。"""
        return p * p * (3 - 2 * p)

    def _animate(self, step, dur: float = 0.16) -> None:
        t0 = time.time()

        def tick():
            p = min(1.0, (time.time() - t0) / dur)
            step(self._ease(p))
            if p < 1.0:
                self.root.after(16, tick)

        tick()

    @staticmethod
    def _mix(a: str, b: str, k: float) -> str:
        return _mix_color(a, b, k)

    def _switch(self, x, y, on, key, s) -> None:
        w, h = round(38 * s), round(22 * s)
        d = round(16 * s)
        pad = round(3 * s)
        span = w - 2 * pad - d
        track = _round(self.cv, x, y, x + w, y + h, h / 2,
                       fill=ACCENT if on else TRACK_OFF, outline="")
        knob = self.cv.create_oval(0, 0, 0, 0, fill=KNOB, outline=BORDER)
        self._switches[key] = dict(x=x, y=y, d=d, pad=pad, span=span,
                                   track=track, knob=knob, pos=1.0 if on else 0.0)
        self._place_knob(key, 1.0 if on else 0.0)
        self._add_hit(x, y, x + w, y + h, lambda: self._toggle(key))

    def _place_knob(self, key: str, pos: float) -> None:
        st = self._switches.get(key)
        if not st:
            return
        x = st["x"] + st["pad"] + st["span"] * pos
        y = st["y"] + st["pad"]
        d = st["d"]
        self.cv.coords(st["knob"], x, y, x + d, y + d)
        self.cv.itemconfigure(st["track"], fill=self._mix(TRACK_OFF, ACCENT, pos))
        st["pos"] = pos

    # ------------------------------------------------------------ 分段控件
    def _segmented(self, x, y, w, h, options, current, cb, s, key: str) -> None:
        """DSH 风格分段控件：灰底容器 + 会滑动的白色滑块。"""
        cv = self.cv
        _round(cv, x, y, x + w, y + h, round(10 * s), fill=SEG_BG,
               outline=BORDER, width=1)
        inner = w - round(6 * s)
        seg = inner / max(1, len(options))
        idx = next((i for i, (v, _) in enumerate(options) if v == current), 0)
        labels = []
        for i, (val, label) in enumerate(options):
            sx = x + round(3 * s) + i * seg
            labels.append(cv.create_text(
                sx + seg / 2, y + h / 2, text=label,
                fill=TEXT if i == idx else SUB,
                font=("Segoe UI Variable Text", -round(12 * s),
                      "bold" if i == idx else "normal")))
            self._add_hit(sx, y, sx + seg, y + h, lambda v=val: cb(v))
        self._segs[key] = dict(x=x, y=y, seg=seg, h=h, options=options,
                               labels=labels, idx=idx, pill=None)
        self._pill_pos[key] = float(idx)
        self._place_pill(key, float(idx))

    def _place_pill(self, key: str, pos: float) -> None:
        st = self._segs.get(key)
        if not st:
            return
        s = self.s
        x, y, seg, h = st["x"], st["y"], st["seg"], st["h"]
        if st.get("pill") is not None:
            try:
                self.cv.delete(st["pill"])
            except Exception:
                pass
        left = x + round(3 * s) + pos * seg
        st["pill"] = _round(self.cv, left, y + round(3 * s),
                            left + seg - round(2 * s), y + h - round(3 * s),
                            round(9 * s), fill=CARD, outline=BORDER, width=1)
        if st["labels"]:
            self.cv.tag_lower(st["pill"], st["labels"][0])

    def _animate_segment(self, key: str, value) -> None:
        st = self._segs.get(key)
        if not st:
            return
        values = [v for v, _ in st["options"]]
        if value not in values:
            return
        target = float(values.index(value))
        start = self._pill_pos.get(key, float(st["idx"]))
        if abs(target - start) < 0.001:
            return

        seq = self._anim_seq.get(key, 0) + 1
        self._anim_seq[key] = seq

        def step(p, key=key, start=start, target=target, st=st, seq=seq):
            if self._anim_seq.get(key) != seq:
                return
            pos = start + (target - start) * p
            self._pill_pos[key] = pos
            self._place_pill(key, pos)
            if p >= 0.999:
                st["idx"] = int(target)
                for i, item in enumerate(st["labels"]):
                    self.cv.itemconfigure(
                        item, fill=TEXT if i == target else SUB,
                        font=("Segoe UI Variable Text", -round(12 * self.s),
                              "bold" if i == target else "normal"))

        self._animate(step, 0.18)

    # ------------------------------------------------------------ 交互
    def _set_hover(self, key) -> None:
        if key == self.hover:
            return
        old, self.hover = self.hover, key
        for hit in self.hits:
            rect = hit.get("rect")
            if rect is None:
                continue
            tag = hit.get("tag_id")
            if tag is None:
                tag = str(rect)
                hit["tag_id"] = tag
            if tag == old or tag == key:
                try:
                    self.cv.itemconfigure(rect, fill=hit["hover"] if tag == key else hit["fill"])
                except Exception:
                    pass

    def _on_motion(self, e) -> None:
        key = None
        for hit in self.hits:
            x1, y1, x2, y2 = hit["box"]
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                key = str(hit["rect"]) if hit.get("rect") is not None else None
                break
        self.cv.configure(cursor="hand2" if key or self._hit(e) else "")
        self._set_hover(key)

    def _hit(self, e):
        for hit in self.hits:
            x1, y1, x2, y2 = hit["box"]
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                return hit
        return None

    def _on_click(self, e) -> None:
        hit = self._hit(e)
        if hit:
            hit["cb"]()

    def _toggle(self, key) -> None:
        val = not bool(self.settings.get(key))
        self.settings[key] = val
        core.save_settings(self.settings)
        st = self._switches.get(key)
        if st:
            start = st["pos"]
            target = 1.0 if val else 0.0
            seq = self._anim_seq.get(key, 0) + 1
            self._anim_seq[key] = seq

            def step(p, key=key, start=start, target=target, seq=seq):
                if self._anim_seq.get(key) != seq:
                    return
                self._place_knob(key, start + (target - start) * p)

            self._animate(step, 0.18)
            # 日志会触发整块重绘，等动画放完再写
            self.root.after(240, lambda: self.log(f"{'打开' if val else '关闭'}：{key}"))
        else:
            self.log(f"{'打开' if val else '关闭'}：{key}")
            self._schedule_redraw()

    def _set_close_action(self, value) -> None:
        if self.settings.get("close_action") == value:
            return
        self.settings["close_action"] = value
        core.save_settings(self.settings)
        self._animate_segment("close", value)
        self.root.after(260, self._schedule_redraw)

    def _maybe_boot_dash(self) -> None:
        # AstrBot 没起来 / 上一块面板还没收干净，就先不开
        if not self._astrbot_web or self._dash_dropping:
            return
        # 已经有一个正在启动的实例就不用再开
        if self.dash is not None and not self._dash_error:
            return
        now = time.time()
        if now - self._dash_try_at < 8:
            return
        self._dash_try_at = now
        # 父窗口必须是 winfo_id() 这一层（TkChild）；挂外框会被 Canvas 盖住
        owner = self.root.winfo_id()
        threading.Thread(target=self._boot_dash, args=(owner,), daemon=True).start()

    def _boot_dash(self, owner: int) -> None:
        path = core.APP_DIR / "tools" / "_edge_profile"
        url = core.PATHS.get("astrbot_web", "http://127.0.0.1:6185")
        view = dashboard_view.DashboardView(path, url, scale=self.scale(),
                                           dark=THEME == "dark")
        ok = view.ensure(owner)
        self._post(lambda: self._dash_booted(view, ok))

    def _dash_booted(self, view, ok: bool) -> None:
        self._dash_ready = bool(ok)
        self._dash_error = not ok
        if ok:
            self.dash = view
            self.log("面板已就绪")
            self._dock_dash()
            # 输入队列接到 Tk 线程上，网页里才能正常打字/用快捷键
            try:
                view.attach_input()
            except Exception:
                pass
        else:
            self.dash = None
            try:
                view.stop()
            except Exception:
                pass
            self.log("面板打不开：没找到 Edge 或窗口创建失败，8 秒后重试")
        self._schedule_redraw()

    def _drop_dash(self) -> None:
        """AstrBot 停了：把面板连同它的 Edge 一起收掉，回到「等待启动」。"""
        view, self.dash = self.dash, None
        self._dash_ready = False
        self._dash_error = False
        self._dash_try_at = 0.0
        if not view:
            return
        self._dash_dropping = True

        def run():
            try:
                view.stop()
            except Exception:
                pass
            self._post(lambda: self._dash_dropped())

        threading.Thread(target=run, daemon=True).start()

    def _dash_dropped(self) -> None:
        self._dash_dropping = False
        self._schedule_redraw()

    def _dock_dash(self) -> None:
        if not (self.dash and self._dash_rect and self._dash_ready):
            return
        if not self.dash.alive():
            self.dash = None
            self._dash_ready = False
            self._dash_error = True
            self.log("面板连接断开了，稍后自动重连")
            self._schedule_redraw()
            return
        x1, y1, x2, y2 = self._dash_rect
        s = getattr(self, "s", 1.0)
        pad = round(8 * s)
        top = round(26 * s)
        dx = int(x1) + pad
        dy = int(y1) + top + pad
        dw = int(x2 - x1) - pad * 2
        dh = int(y2 - y1) - top - pad * 2
        if dw < 120 or dh < 80:
            return
        if self.dash.shown:
            self.dash.place(dx, dy, dw, dh)
        else:
            self.dash.show(dx, dy, dw, dh)

    def _tick_dash(self) -> None:
        try:
            # 进程在就算「还开着」：WebUI 偶尔探测超时不该把面板收掉
            up = bool(self._astrbot_pid) or self._astrbot_web
            if (self.page == "main" and up and self._dash_ready
                    and self.root.state() in ("normal", "zoomed")):
                self._dock_dash()
                if self.dash:
                    self.dash.focus_page()
            elif self.dash:
                self.dash.hide()
            if not up and self.dash:
                self._drop_dash()
                self._schedule_redraw()
            if self.page == "main" and self._astrbot_web and not self._dash_ready:
                self._maybe_boot_dash()
        except Exception:
            pass
        self.root.after(150, self._tick_dash)

    def _open_settings(self) -> None:
        self.page = "settings"
        if self.dash:
            self.dash.hide()
        try:
            self.root.focus_set()
        except Exception:
            pass
        self._schedule_redraw()

    def _open_main(self) -> None:
        self.page = "main"
        if self.dash:
            self.dash.hide()
        self._schedule_redraw()

    # ------------------------------------------------------------ 动作
    def _bg(self, label, fn) -> None:
        def run():
            self.root.after(0, lambda: self.log(f"{label} ..."))
            try:
                fn()
                self.root.after(0, lambda: self.log(f"{label} 完成"))
            except Exception as exc:  # pragma: no cover
                msg = str(exc)
                self.root.after(0, lambda: self.log(f"{label} 失败：{msg}"))
            self.root.after(0, self._schedule_redraw)

        threading.Thread(target=run, daemon=True).start()

    def start_all(self) -> None:
        def run():
            core.start_astrbot()
            core.wait_port(core.PATHS["astrbot_web"], 40)
            core.start_snowluma()
            core.wait_port(core.PATHS["snowluma_web"], 30)
            if self.settings.get("auto_qq", True):
                core.start_qq()

        self._bg("启动", run)

    def stop_all(self) -> None:
        self._bg("停止", lambda: (core.stop_qq(), core.stop_snowluma(), core.stop_astrbot()))

    def hot_restart(self) -> None:
        self._bg("热重启 AstrBot", core.hot_restart)

    def restart_proto(self) -> None:
        self._bg("重启协议端", lambda: (core.stop_snowluma(), core.start_snowluma()))

    def restart_all(self) -> None:
        self._bg("全部重启", core.restart_all)

    def open_panels(self) -> None:
        import webbrowser

        webbrowser.open(core.PATHS["astrbot_web"])
        webbrowser.open(core.PATHS["snowluma_web"])

    def open_logs(self) -> None:
        core.open_logs()

    def open_dir(self) -> None:
        import os

        os.startfile(str(core.APP_DIR))

    def copy_status(self) -> None:
        import json as _json

        text = _json.dumps(self._st or {}, ensure_ascii=False)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log("状态已复制到剪贴板")

    # ------------------------------------------------------------ 托盘
    def _start_tray(self) -> None:
        try:
            import pystray
            from PIL import Image
        except Exception:
            self.tray = None
            return
        try:
            icon_path = Path(core.APP_DIR) / "tools" / "bot.ico"
            img = Image.open(icon_path) if icon_path.exists() else Image.new("RGB", (64, 64), ACCENT)
            menu = pystray.Menu(
                pystray.MenuItem("显示面板", self._tray_show, default=True),
                pystray.MenuItem("启动", lambda: self._post(self.start_all)),
                pystray.MenuItem("全部停止", lambda: self._post(self.stop_all)),
                pystray.MenuItem("热重启 AstrBot", lambda: self._post(self.hot_restart)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", lambda: self._post(self.quit)),
            )
            self.tray = pystray.Icon("dafeiyu_panel", img, "大肥鱼控制台", menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception:
            self.tray = None

    def _post(self, fn) -> None:
        """从任意线程安全地回到 UI 线程。"""
        import threading

        if threading.current_thread() is threading.main_thread():
            try:
                self.root.after(0, fn)
            except Exception:
                pass
            return
        self._ui_queue.put(fn)

    def _tray_show(self, *_a) -> None:
        self._post(self.show_window)

    def show_window(self) -> None:
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def _to_tray(self) -> None:
        if self.tray is None:
            self._start_tray()
        if self.tray is None:
            # 托盘不可用就老老实实最小化，别让窗口消失得找不回来
            try:
                self.root.iconify()
            except Exception:
                pass
            return
        try:
            self.root.withdraw()
        except Exception:
            pass

    def _on_unmap(self, _e=None) -> None:
        """最小化就老老实实待在任务栏：托盘图标只用于「关闭到后台」和快捷操作。"""
        try:
            if self.root.state() == "iconic" and self.dash:
                self.dash.hide()
        except Exception:
            pass

    # ------------------------------------------------------------ 插件体检
    def _startup_check(self) -> None:
        self._load_plugins(quiet=True)

        def run():
            try:
                health = core.component_health()
            except Exception:
                return
            bad = [k for k, v in health.items() if not v.get("installed")]
            if bad:
                text = "组件文件不完整：" + "、".join(bad) + "，点「插件」查看"
                self._post(lambda: self.log(text))

        threading.Thread(target=run, daemon=True).start()

    def _open_plugins(self) -> None:
        self.page = "plugins"
        self._plugin_page = 0
        if self.dash:
            self.dash.hide()
        try:
            self.root.focus_set()
        except Exception:
            pass
        self._schedule_redraw()
        self._load_plugins(quiet=True)

    def _load_plugins(self, quiet: bool = False) -> None:
        if self._plugin_loading:
            return
        self._plugin_loading = True

        def run():
            try:
                items = core.scan_plugins()
            except Exception as exc:  # pragma: no cover
                items = []
                msg = str(exc)
                self._post(lambda: self.log(f"插件检查失败：{msg}"))

            def done():
                self._plugins = items
                self._plugin_loading = False
                bad_now = [p for p in items if not p.get("installed")]
                if bad_now and not self._plugin_warned:
                    self._plugin_warned = True
                    self.log(f"有 {len(bad_now)} 个必要插件未安装，点「插件」可一键修复")
                if items and not quiet:
                    bad = [p for p in items if not p.get("installed")]
                    tail = "" if not bad else f"，{len(bad)} 个待处理"
                    self.log(f"插件检查：{len(items) - len(bad)}/{len(items)} 已安装{tail}")
                self._schedule_redraw()

            self._post(done)

        threading.Thread(target=run, daemon=True).start()

    def _install_component(self, key: str) -> None:
        """缺组件时下载安装：AstrBot/SnowLuma 自动下，QQ 打开官方下载页。"""
        if key in self._comp_busy:
            return
        self._comp_busy.add(key)
        self._comp_pct.pop(key, None)
        import threading as _th
        ev = _th.Event()
        self._comp_cancel[key] = ev
        self.log(f"开始准备 {key} …")
        self._schedule_redraw()

        def work():
            def logmsg(msg: str) -> None:
                pct = None
                if msg.endswith("%"):
                    try:
                        pct = int(msg.rsplit(" ", 1)[1].rstrip("%"))
                    except Exception:
                        pct = None
                self._comp_msgs.put(("pct", key, pct) if pct is not None else ("log", key, msg))

            ev = self._comp_cancel.get(key)
            try:
                ok, msg = core.install_component(
                    key, log=logmsg, should_stop=(ev.is_set if ev else None))
            except core.DownloadCanceled:
                ok, msg = False, f"{key} 下载已取消"
            except Exception as exc:  # pragma: no cover
                ok, msg = False, f"{key} 安装失败：{exc}"
            self._comp_msgs.put(("done", key, (ok, msg)))

        import threading
        threading.Thread(target=work, daemon=True).start()

    def _drain_comp(self) -> None:
        """后台线程不能直接碰 Tk，消息从这里进 UI。"""
        import queue as _queue

        dirty = False
        while True:
            try:
                kind, key, val = self._comp_msgs.get_nowait()
            except _queue.Empty:
                break
            if kind == "pct":
                self._comp_pct[key] = val
                dirty = True
            elif kind == "done":
                ok, msg = val
                self._component_done(key, ok, msg)
                dirty = True
            else:
                self.log(str(val))
        while True:
            try:
                fn = self._ui_queue.get_nowait()
            except _queue.Empty:
                break
            try:
                fn()
            except Exception:
                pass
        if dirty:
            self._schedule_redraw()
        try:
            self.root.after(120, self._drain_comp)
        except Exception:
            pass

    def _comp_progress(self, key: str, pct: int) -> None:
        self._comp_pct[key] = pct
        self._schedule_redraw()

    def _cancel_component(self, key: str) -> None:
        ev = self._comp_cancel.get(key)
        if ev is not None:
            ev.set()
            self.log(f"正在取消 {key} 下载…")

    def _component_done(self, key: str, ok: bool, msg: str) -> None:
        self._comp_busy.discard(key)
        self._comp_pct.pop(key, None)
        self._comp_cancel.pop(key, None)
        self.log(("✓ " if ok else "✗ ") + msg)
        try:
            self._health = core.component_health()
        except Exception:
            pass
        self._schedule_redraw()

    def _install_one(self, item: dict) -> None:
        name = item.get("name") or ""

        def run():
            ok, msg = core.install_plugin(item, log=lambda t: self._post(lambda: self.log(t)))
            self._post(lambda: self.log(msg))
            if ok:
                self._post(lambda: self.log(f"{name} 已就位，点「热重启 AstrBot」生效"))
            self._post(lambda: self._load_plugins(quiet=True))

        threading.Thread(target=run, daemon=True).start()

    def _install_all(self) -> None:
        if self._plugin_loading:
            return

        def run():
            todo = [p for p in self._plugins if not p.get("installed")]
            if not todo:
                self._post(lambda: self.log("没有需要安装的插件"))
                return
            self._post(lambda: self.log(f"开始安装 {len(todo)} 个插件…"))
            ok = 0
            for item in todo:
                good, msg = core.install_plugin(
                    item, log=lambda t: self._post(lambda: self.log(t)))
                self._post(lambda m=msg: self.log(m))
                ok += 1 if good else 0
            total = len(todo)
            self._post(lambda: self.log(f"安装结束：成功 {ok}/{total}，点「热重启 AstrBot」生效"))
            self._post(lambda: self._load_plugins(quiet=True))

        threading.Thread(target=run, daemon=True).start()

    def _turn_page(self, delta: int) -> None:
        self._plugin_page = max(0, self._plugin_page + delta)
        self._schedule_redraw()

    def _open_repo(self, url: str) -> None:
        import webbrowser

        try:
            webbrowser.open(url)
        except Exception:
            pass

    def open_plugins_dir(self) -> None:
        import os

        try:
            path = core.PLUGINS_DIR
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path))
        except Exception as exc:
            self.log(f"打不开插件目录：{exc}")

    def _draw_plugins(self, W, H, m, s) -> None:
        cw = min(W - 2 * m, round(760 * s))
        rx = m + cw
        self._text(m, m - 2, "插件体检", 19, TEXT, weight="bold",
                   )
        self._text(m, m + round(26 * s), "必要插件从 GitHub 检查、修复或一键安装", 10.5, MUTED)
        bw, bh = round(58 * s), round(26 * s)
        self._button(rx - bw, m - round(2 * s), rx, m - round(2 * s) + bh,
                     "返回", "secondary", self._open_main, s)

        items = self._plugins
        total = len(items)
        ok_n = sum(1 for p in items if p.get("installed"))
        todo = total - ok_n
        y = m + round(54 * s)
        ch = round(68 * s)
        self._card(m, y, rx, y + ch)
        headline = f"{ok_n} / {total} 已安装" if total else "正在检查…"
        self._text(m + round(16 * s), y + round(11 * s), headline, 15, TEXT, weight="bold")
        if not total:
            note, ncolor = "首次检查需要几秒钟", MUTED
        elif todo:
            note, ncolor = f"还有 {todo} 个需要处理，装完点热重启生效", AMBER
        else:
            note, ncolor = "所有必要插件都已就位", GREEN
        self._text(m + round(16 * s), y + round(40 * s), note, 10.5, ncolor)
        if total:
            bw2 = round(112 * s)
            self._button(rx - round(16 * s) - bw2, y + round(19 * s), rx - round(16 * s),
                         y + round(19 * s) + round(30 * s),
                         "一键安装缺失" if todo else "重新检查", "primary",
                         self._install_all if todo else self._load_plugins, s)
            bw3 = round(56 * s)
            self._button(rx - round(24 * s) - bw2 - bw3, y + round(19 * s),
                         rx - round(24 * s) - bw2, y + round(19 * s) + round(30 * s),
                         "刷新", "secondary", self._load_plugins, s)

        y2 = y + ch + round(12 * s)
        row_h = round(48 * s)
        avail = H - y2 - round(66 * s)
        per = max(1, int(avail // row_h))
        pages = max(1, (total + per - 1) // per)
        page = max(0, min(self._plugin_page, pages - 1))
        chunk = items[page * per:(page + 1) * per]
        if chunk:
            self._card(m, y2, rx, y2 + row_h * len(chunk) + round(8 * s))
        for i, item in enumerate(chunk):
            cy = y2 + round(4 * s) + row_h * i
            if i:
                self.cv.create_line(m + round(14 * s), cy, rx - round(14 * s), cy, fill=BORDER)
            status = item.get("status")
            mark, color = {"ok": ("已安装", GREEN), "broken": ("需修复", AMBER)}.get(
                status, ("未安装", DANGER))
            self._text(m + round(16 * s), cy + round(8 * s),
                       item.get("display") or item.get("name"), 12, TEXT)
            repo = (item.get("repo") or "未配置 GitHub 仓库").replace(
                "https://github.com/", "")
            ver = item.get("version")
            sub = (f"v{ver} · " if ver else "") + repo
            self._text(m + round(16 * s), cy + round(27 * s), sub[:70], 9.5, MUTED)
            aw = round(52 * s)
            tw = round(54 * s)
            right = rx - round(16 * s)
            chip_x2 = right - aw - round(8 * s) if status != "ok" else right
            self._chip(chip_x2 - tw, cy + round(15 * s), chip_x2, cy + round(33 * s),
                       mark, color)
            if status != "ok" and not item.get("repo"):
                self._text(right - round(4 * s), cy + round(19 * s),
                           "缺仓库地址", 9.5, MUTED, anchor="e")
            elif status != "ok":
                self._button(right - aw, cy + round(9 * s), right,
                             cy + round(9 * s) + round(30 * s),
                             "修复" if status == "broken" else "安装", "primary",
                             lambda it=item: self._install_one(it), s)
            if item.get("repo"):
                # 整行可点：直接打开对应的 GitHub 仓库
                self._add_hit(m + round(8 * s), cy + round(4 * s), rx - round(8 * s),
                              cy + row_h - round(6 * s),
                              lambda u=item["repo"]: self._open_repo(u))

        if pages > 1:
            py = y2 + row_h * len(chunk) + round(18 * s)
            self._text(m, py, f"{page + 1} / {pages}", 10.5, MUTED)
            if page < pages - 1:
                self._link(rx, py, "下一页 ›", lambda: self._turn_page(1), anchor="ne",
                           size=10.5)
            if page > 0:
                px = rx - (round(96 * s) if page < pages - 1 else 0)
                self._link(px, py, "‹ 上一页", lambda: self._turn_page(-1), anchor="ne",
                           size=10.5)

        fy = H - round(28 * s)
        self._link(m, fy, "打开插件目录", self.open_plugins_dir)
        self._link(rx, fy, "热重启 AstrBot 生效", self.hot_restart, anchor="ne")

    # ------------------------------------------------------------ 关闭
    def on_close(self) -> None:
        try:
            set_window_alpha(self.root, None)
        except Exception:
            pass
        action = self.settings.get("close_action", "ask")
        if action == "tray":
            self._to_tray()
        elif action == "quit":
            self.quit()
        else:
            self._ask_close()

    def _ask_close(self) -> None:
        s = self.scale()
        dlg = tk.Toplevel(self.root)
        dlg.title("关闭大肥鱼控制台")
        dlg.configure(bg=CARD)
        dlg.resizable(False, False)
        w, h = round(360 * s), round(206 * s)
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="要关掉面板，还是留它在后台？", bg=CARD, fg=TEXT,
                 font=("Segoe UI Variable Text", -round(12.5 * s)), anchor="w").pack(
            fill="x", padx=round(18 * s), pady=(round(16 * s), round(4 * s)))
        tk.Label(dlg, text="关掉面板不会停机器人，AstrBot / SnowLuma 会继续运行。",
                 bg=CARD, fg=SUB, font=("Segoe UI Variable Text", -round(10 * s)),
                 anchor="w").pack(fill="x", padx=round(18 * s))

        remember = tk.BooleanVar(value=False)
        tk.Checkbutton(dlg, text="记住这个选择", variable=remember, bg=CARD, fg=SUB,
                       activebackground=CARD, activeforeground=SUB, selectcolor=CARD,
                       bd=0, highlightthickness=0,
                       font=("Segoe UI Variable Text", -round(10 * s))).pack(
            anchor="w", padx=round(12 * s), pady=(round(8 * s), 0))

        row = tk.Frame(dlg, bg=CARD)
        row.pack(fill="x", padx=round(18 * s), pady=(round(10 * s), round(14 * s)))
        row.columnconfigure(0, weight=1, uniform="b")
        row.columnconfigure(1, weight=1, uniform="b")

        def make(text, bg, fg, cmd, col):
            b = tk.Button(row, text=text, command=cmd, relief="flat", bd=0,
                          bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
                          font=("Segoe UI Variable Text", -round(11 * s)),
                          cursor="hand2", height=2)
            b.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else round(8 * s), 0))
            return b

        def finish(action):
            if remember.get():
                self.settings["close_action"] = action
                core.save_settings(self.settings)
            dlg.destroy()
            self._to_tray() if action == "tray" else self.quit()

        make("最小化到后台", ACCENT, "#FFFFFF", lambda: finish("tray"), 0)
        make("直接关闭", CHIP, TEXT, lambda: finish("quit"), 1)
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)  # 点 X 只是取消，不关主窗口

    def quit(self) -> None:
        try:
            if self.dash:
                self.dash.stop()
        except Exception:
            pass
        try:
            if self.tray:
                self.tray.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    # ------------------------------------------------------------ 状态轮询
    def _status_loop(self) -> None:
        """后台刷新进程/端口状态：端口探测要 1s 上下，放到 UI 线程会卡死。"""
        import time

        while True:
            try:
                st = core.status()
                health = core.component_health()
            except Exception:
                st, health = None, None
            if st:
                self._st = st
            if health:
                self._health = health
            try:
                if not self.root.winfo_exists():
                    return
            except Exception:
                return
            time.sleep(1.5)

    def _refresh_loop(self) -> None:
        import time

        while True:
            time.sleep(2.5)
            try:
                if not self.root.winfo_exists():
                    return
                if (self._theme_pref() == "system"
                        and self._resolve_theme() != THEME):
                    self.root.after(0, self._set_theme, "system")
                    continue
                if self.page in ("main", "guide"):
                    self.root.after(0, self._schedule_redraw)
            except Exception:
                return


def run() -> None:
    _enable_dpi()
    root = tk.Tk()
    Panel(root)
    root.mainloop()
