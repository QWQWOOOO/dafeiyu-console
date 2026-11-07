"""把 AstrBot Dashboard 用 Edge --app 窗口真正嵌进控制台（SetParent）。

窗口层级（Windows 实际结构）：
    TkTopLevel（外框，带标题栏）
      └─ TkChild  ← root.winfo_id()，Canvas 就在这一层
           ├─ Tk Canvas（控制台的绘制层）
           └─ Edge --app 窗口（WS_CHILD，SetParent 挂到 TkChild 上）

两个关键点（也是之前右栏空白的根因）：
1. 父窗口必须是 root.winfo_id() 这一层；挂到外框 TkTopLevel 上会变成
   Canvas 的兄弟窗口，被不透明的 Canvas 整块盖住 → 看起来就是空白。
2. 子窗口坐标直接用 Canvas 坐标；Canvas 与 TkChild 客户区同原点。

Chromium 的 app 窗口自带一条约 30 DIP 的标题栏（画在客户区里，不是系统
非客户区，去掉 WS_CAPTION 也去不掉）。place() 把窗口整体上移 frame 像素，
再用 SetWindowRgn 把顶上那条裁掉，视觉上就是干净地嵌在里面。
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None

USER32 = ctypes.windll.user32
GDI32 = ctypes.windll.gdi32

USER32.SetParent.argtypes = [wt.HWND, wt.HWND]
USER32.SetParent.restype = wt.HWND
USER32.GetParent.argtypes = [wt.HWND]
USER32.GetParent.restype = wt.HWND
USER32.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
USER32.GetWindowLongW.restype = ctypes.c_long
USER32.SetWindowLongW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_long]
USER32.SetWindowLongW.restype = ctypes.c_long
USER32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_uint]
USER32.SetWindowPos.restype = wt.BOOL
USER32.MoveWindow.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, wt.BOOL]
USER32.MoveWindow.restype = wt.BOOL
USER32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
USER32.IsWindow.argtypes = [wt.HWND]
USER32.IsWindowVisible.argtypes = [wt.HWND]
USER32.GetWindowTextW.argtypes = [wt.HWND, ctypes.c_wchar_p, ctypes.c_int]
USER32.GetClassNameW.argtypes = [wt.HWND, ctypes.c_wchar_p, ctypes.c_int]
USER32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
USER32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
USER32.SetWindowRgn.argtypes = [wt.HWND, wt.HRGN, wt.BOOL]
USER32.GetWindowRgn.argtypes = [wt.HWND, wt.HRGN]
USER32.GetWindowRgn.restype = ctypes.c_int
USER32.GetDpiForWindow.argtypes = [wt.HWND]
USER32.GetDpiForWindow.restype = ctypes.c_uint
USER32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
USER32.AttachThreadInput.restype = wt.BOOL
USER32.SetFocus.argtypes = [wt.HWND]
USER32.SetFocus.restype = wt.HWND
USER32.GetFocus.restype = wt.HWND
USER32.GetAncestor.argtypes = [wt.HWND, ctypes.c_uint]
USER32.GetAncestor.restype = wt.HWND
USER32.PostMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
USER32.PostMessageW.restype = wt.BOOL
GDI32.GetRgnBox.argtypes = [wt.HRGN, ctypes.POINTER(wt.RECT)]
GDI32.DeleteObject.argtypes = [wt.HGDIOBJ]

KERNEL32 = ctypes.windll.kernel32
KERNEL32.GetCurrentThreadId.restype = wt.DWORD
KERNEL32.CreateJobObjectW.restype = wt.HANDLE
KERNEL32.SetInformationJobObject.restype = wt.BOOL
KERNEL32.AssignProcessToJobObject.restype = wt.BOOL
KERNEL32.CloseHandle.restype = wt.BOOL

# 让 Edge 跟着控制台一起死：放进 job 后，控制台进程一退出（哪怕是被强杀），
# Windows 会自动把 job 里的 Edge 全干掉，不会留一个孤儿窗口飘在桌面上。
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong)]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wt.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wt.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wt.DWORD),
                ("SchedulingClass", wt.DWORD)]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", _IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]

GDI32.CreateRectRgn.argtypes = [ctypes.c_int] * 4
GDI32.CreateRectRgn.restype = wt.HRGN

WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
USER32.EnumWindows.argtypes = [WNDENUMPROC, wt.LPARAM]
USER32.EnumChildWindows.argtypes = [wt.HWND, WNDENUMPROC, wt.LPARAM]

GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
SWP_FRAMECHANGED = 0x0020
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_TOP = 0
GA_ROOT = 2
SW_HIDE = 0
SW_SHOW = 5
SW_SHOWNA = 8
WM_CLOSE = 0x0010

# Chromium app 窗口标题栏高度（DIP）；实测 125% 缩放下 37 px = 30 DIP
FRAME_DIP = 30
APP_CLASS = "Chrome_WidgetWin_1"
# 真正渲染网页的窗口：拿它和 app 窗口的矩形差，量出标题栏和四周边框
RENDER_HOST_CLASS = "Chrome_RenderWidgetHostHWND"

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def _win_title(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(512)
    USER32.GetWindowTextW(hwnd, buf, 512)
    return buf.value


def _win_class(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    USER32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _win_rect(hwnd: int) -> tuple[int, int, int, int]:
    r = wt.RECT()
    USER32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def _all_windows() -> list[tuple[int, str, str]]:
    found: list[tuple[int, str, str]] = []

    def cb(hwnd, _l):
        found.append((hwnd, _win_title(hwnd), _win_class(hwnd)))
        return True

    USER32.EnumWindows(WNDENUMPROC(cb), 0)
    return found


def _descendants(parent: int) -> list[int]:
    found: list[int] = []

    def cb(hwnd, _l):
        found.append(hwnd)
        return True

    USER32.EnumChildWindows(parent, WNDENUMPROC(cb), 0)
    return found


def _profile_pids(profile_dir: Path) -> set[int]:
    """所有命令行里带这个 user-data-dir 的进程（Edge 会派生一堆子进程）。"""
    needle = str(profile_dir).lower()
    pids: set[int] = set()
    if psutil is not None:
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if (p.info.get("name") or "").lower() != "msedge.exe":
                    continue
                if needle in " ".join(p.info.get("cmdline") or []).lower():
                    pids.add(p.info["pid"])
            except Exception:
                continue
    return pids


def _pick_app_window(pids: set[int], before: set[int]) -> int:
    """挑出真正的 app 窗口：Chrome_WidgetWin_1、可见、有标题、面积最大。"""
    best, best_area = 0, 0
    for hwnd, title, cls in _all_windows():
        if cls != APP_CLASS or not title:
            continue
        if not USER32.IsWindowVisible(hwnd):
            continue
        pid = wt.DWORD()
        USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pids:
            if pid.value not in pids:
                continue
        elif hwnd in before:
            # 拿不到进程列表时退化为“新出现的窗口”
            continue
        x1, y1, x2, y2 = _win_rect(hwnd)
        area = max(0, x2 - x1) * max(0, y2 - y1)
        if area > best_area and area >= 200 * 150:
            best, best_area = hwnd, area
    return best


def edge_exe() -> Optional[str]:
    for p in EDGE_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def _adopt(proc: "subprocess.Popen") -> int:
    """把 Edge 进程塞进一个 kill-on-close 的 job，控制台挂了它就跟着关。"""
    try:
        job = KERNEL32.CreateJobObjectW(None, None)
        if not job:
            return 0
        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        KERNEL32.SetInformationJobObject(
            job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info))
        if not KERNEL32.AssignProcessToJobObject(job, int(proc._handle)):
            KERNEL32.CloseHandle(job)
            return 0
        return job
    except Exception:
        return 0


class DashboardView:
    """懒启动一个 Edge --app 窗口，并把它作为子窗口嵌进控制台。"""

    def __init__(self, profile_dir: Path, url: str, scale: float = 1.0,
                 dark: bool = False) -> None:
        self.profile_dir = Path(profile_dir)
        self.url = url
        self.scale = scale or 1.0
        self.dark = bool(dark)
        self.proc: Optional[subprocess.Popen] = None
        self.hwnd: int = 0
        self.parent_hwnd: int = 0
        self.frame: int = max(0, int(FRAME_DIP * self.scale))
        self.insets: tuple[int, int, int, int] | None = None
        self._measured = False
        self._last = (0, 0, 0, 0)
        self._last_insets: tuple[int, int, int, int] | None = None
        self._shown = False
        self._attached: tuple[int, int] | None = None
        self._host: int = 0
        self._job: int = 0

    # ------------------------------------------------------------ 生命周期
    def alive(self) -> bool:
        if not self.hwnd or not USER32.IsWindow(self.hwnd):
            return False
        return USER32.GetParent(self.hwnd) == self.parent_hwnd

    def attach_input(self) -> bool:
        """把 Tk 线程和 Edge UI 线程的输入队列连起来。

        跨进程的 WS_CHILD 窗口默认收不到键盘：焦点永远留在 TkChild，按键都送进
        Tk 的线程队列。AttachThreadInput 之后两个线程共用一个输入队列，点进网页
        就能正常输入、用 Ctrl+F 等浏览器快捷键。
        """
        if not self.alive():
            return False
        my_tid = KERNEL32.GetCurrentThreadId()
        chrome_tid = USER32.GetWindowThreadProcessId(self.hwnd, None)
        if not chrome_tid or chrome_tid == my_tid:
            return True
        if self._attached == (my_tid, chrome_tid):
            return True
        if self._attached:
            self.detach_input()
        if not USER32.AttachThreadInput(my_tid, chrome_tid, True):
            return False
        self._attached = (my_tid, chrome_tid)
        # 焦点要给真正渲染网页的子窗口，给 app 外框的话按键会被 UI 层吃掉
        if not self._host:
            self._measure()
        USER32.SetFocus(self._host or self.hwnd)
        return True

    def detach_input(self) -> None:
        if not self._attached:
            return
        my_tid, chrome_tid = self._attached
        self._attached = None
        try:
            USER32.AttachThreadInput(my_tid, chrome_tid, False)
        except Exception:
            pass

    def focus_page(self) -> None:
        """把键盘焦点推回网页（Tk 每次激活都会把焦点抢回 TkChild）。"""
        if not self._attached or not self.alive():
            return
        root = USER32.GetAncestor(self.parent_hwnd, GA_ROOT)
        if USER32.GetForegroundWindow() != root:
            return  # 控制台不在前台时别抢别人的焦点
        target = self._host or self.hwnd
        if USER32.GetFocus() != target:
            USER32.SetFocus(target)

    def ensure(self, parent_hwnd: int) -> bool:
        """确保 Edge 窗口存在、已挂到 parent 下；失败返回 False。"""
        self.parent_hwnd = parent_hwnd
        if self.alive():
            return True

        exe = edge_exe()
        if not exe:
            return False

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        before = {h for h, _t, c in _all_windows() if c == APP_CLASS}

        # 已有残留进程就先清掉，避免 profile 被锁
        self._kill_profile()
        try:
            self.proc = subprocess.Popen(
                [
                    exe,
                    f"--app={self.url}",
                    f"--user-data-dir={self.profile_dir}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-features=msEdgeSidebarV2",
                    "--window-size=1000,760",
                    # 先丢到屏幕外，避免嵌入前在左上角闪一下
                    "--window-position=-32000,-32000",
                ] + (["--force-dark-mode"] if self.dark else []),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            self.proc = None
            return False
        self._job = _adopt(self.proc)

        hwnd = 0
        deadline = time.time() + 25
        while time.time() < deadline:
            pids = _profile_pids(self.profile_dir)
            hwnd = _pick_app_window(pids, before)
            if hwnd:
                # 等窗口真正显示、尺寸稳定再挂
                x1, y1, x2, y2 = _win_rect(hwnd)
                if USER32.IsWindowVisible(hwnd) and (x2 - x1) > 300 and (y2 - y1) > 200:
                    break
                hwnd = 0
            if self.proc and self.proc.poll() is not None and not pids:
                # 启动器退出不一定是失败（可能移交给了子进程），再等一会儿
                pass
            time.sleep(0.35)

        if not hwnd:
            return False

        self.hwnd = hwnd
        self._embed()
        if not self.alive():
            return False
        self.frame = max(0, int(FRAME_DIP * self.scale))
        # 等渲染窗口出现，量出真实的标题栏/边框厚度（Chromium 自己画的，各版本/缩放不同）
        deadline = time.time() + 6
        while time.time() < deadline:
            if self._measure():
                break
            time.sleep(0.2)
        return True

    def _measure(self) -> bool:
        """用 RenderWidgetHost 的矩形反推 app 窗口四边内缩量。"""
        if not self.hwnd:
            return False
        host = 0
        for h in _descendants(self.hwnd):
            if _win_class(h) == RENDER_HOST_CLASS:
                x1, y1, x2, y2 = _win_rect(h)
                if (x2 - x1) > 200 and (y2 - y1) > 150:
                    host = h
                    break
        if not host:
            return False
        self._host = host
        wx1, wy1, wx2, wy2 = _win_rect(self.hwnd)
        hx1, hy1, hx2, hy2 = _win_rect(host)
        left = max(0, hx1 - wx1)
        top = max(0, hy1 - wy1)
        right = max(0, wx2 - hx2)
        bottom = max(0, wy2 - hy2)
        # 内缩量不合理就不要（可能量到了奇怪的子窗口）
        if left > 60 or top > 120 or right > 60 or bottom > 60:
            return False
        self.insets = (left, top, right, bottom)
        self._measured = True
        return True

    def _embed(self) -> None:
        style = USER32.GetWindowLongW(self.hwnd, GWL_STYLE)
        style &= ~(WS_POPUP | WS_CAPTION | WS_THICKFRAME |
                   WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX)
        style |= WS_CHILD
        USER32.SetWindowLongW(self.hwnd, GWL_STYLE, style)
        USER32.SetParent(self.hwnd, self.parent_hwnd)
        # 让样式变更立即生效，并放到同层窗口最上面（Canvas 之上）；
        # 先挪到父窗口可见区外，免得还没测量完就在左上角露一块
        USER32.SetWindowPos(self.hwnd, HWND_TOP, -4000, -4000, 60, 60,
                            SWP_FRAMECHANGED | SWP_NOACTIVATE)
        USER32.ShowWindow(self.hwnd, SW_SHOWNA)
        self._shown = True

    @property
    def shown(self) -> bool:
        return self._shown

    # ------------------------------------------------------------ 摆位
    def _region_box(self) -> tuple[int, int, int, int] | None:
        """当前窗口区域的外接矩形（用于判断 Chromium 是否重置了 region）。"""
        rgn = GDI32.CreateRectRgn(0, 0, 0, 0)
        try:
            kind = USER32.GetWindowRgn(self.hwnd, rgn)
            if kind == 0:  # ERROR
                return None
            r = wt.RECT()
            if not GDI32.GetRgnBox(rgn, ctypes.byref(r)):
                return None
            return (r.left, r.top, r.right, r.bottom)
        finally:
            GDI32.DeleteObject(rgn)

    def place(self, x: int, y: int, w: int, h: int) -> None:
        """x/y 是父窗口客户区里“网页内容”的左上角，单位为物理像素。"""
        if not self.alive():
            return
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w < 80 or h < 60:
            return
        if not self._measured and self._measure():
            self._last = (0, 0, 0, 0)
        left, top, right, bottom = self.insets or (0, self.frame, 0, 0)
        # 右边/下边再收 1px，因为 Chromium 会在渲染窗口最后一列/行画一道黑边
        box = (left, top, left + w - 1, top + h - 1)
        if (x, y, w, h) != self._last or (left, top, right, bottom) != self._last_insets:
            self._last = (x, y, w, h)
            self._last_insets = (left, top, right, bottom)
            # 把窗口往外扩出内缩量，再让内容区正好落在 (x, y, w, h)
            USER32.MoveWindow(self.hwnd, x - left, y - top, w + left + right,
                              h + top + bottom, True)
        if self._region_box() != box:
            # Chromium 在重绘/缩放后会把自己的窗口区域重置掉，得重新裁
            rgn = GDI32.CreateRectRgn(*box)
            USER32.SetWindowRgn(self.hwnd, rgn, True)

    def show(self, x: int, y: int, w: int, h: int) -> None:
        if not self.alive():
            return
        self._last = (0, 0, 0, 0)
        self.place(x, y, w, h)
        USER32.ShowWindow(self.hwnd, SW_SHOWNA)
        self._shown = True

    def hide(self) -> None:
        if self.hwnd and USER32.IsWindow(self.hwnd) and self._shown:
            USER32.ShowWindow(self.hwnd, SW_HIDE)
            self._shown = False

    def _kill_profile(self) -> None:
        pids = _profile_pids(self.profile_dir)
        if self.proc and self.proc.pid:
            pids.add(self.proc.pid)
        if not pids:
            return
        # 先礼貌关一次：直接 terminate 会让 Edge 来不及把登录态写回 profile，
        # 下次打开又得重新登录面板。
        if self.hwnd and USER32.IsWindow(self.hwnd):
            USER32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
            deadline = time.time() + 2.5
            while time.time() < deadline and _profile_pids(self.profile_dir):
                time.sleep(0.15)
            pids = _profile_pids(self.profile_dir)
            if self.proc and self.proc.pid:
                pids.add(self.proc.pid)
        if psutil is not None:
            for pid in pids:
                try:
                    psutil.Process(pid).terminate()
                except Exception:
                    continue
        # 给一点时间释放 profile 锁
        time.sleep(0.4)

    def stop(self) -> None:
        self.detach_input()
        self._kill_profile()
        if self._job:
            try:
                KERNEL32.CloseHandle(self._job)
            except Exception:
                pass
            self._job = 0
        self.proc = None
        self.hwnd = 0
        self._shown = False
