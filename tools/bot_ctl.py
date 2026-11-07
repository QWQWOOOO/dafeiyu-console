"""大肥鱼控制台 —— 一个 exe 管住 AstrBot / SnowLuma / QQ 的启停与热重启。

设计原则：exe 只做“指挥”，不内嵌任何业务代码。
- AstrBot / SnowLuma 的代码、配置、插件都在磁盘目录里，改完点「热重启」即可生效，
  不需要重新打包 exe（这就是热更新）。
- 路径写在 exe 同目录的 paths.json 里，换机器/换目录改这个文件就行。

命令行：
    BotCtrl.exe start        启动全部
    BotCtrl.exe stop         停止全部
    BotCtrl.exe restart      全部重启
    BotCtrl.exe hot          只热重启 AstrBot（改插件/配置后用）
    BotCtrl.exe status       看状态
不带参数时打开图形界面。
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None


class _Proc:
    """psutil 缺失时的兜底实现（走 PowerShell 取进程列表）。"""

    def __init__(self, pid: int, name: str, cmdline: list[str]):
        self.info = {"pid": pid, "name": name, "cmdline": cmdline, "cwd": None}


def _powershell_procs() -> list:
    import subprocess as sp

    ps = (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    try:
        raw = sp.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            timeout=20,
        ).stdout.decode("utf-8", "ignore")
        data = json.loads(raw) if raw.strip() else []
        if isinstance(data, dict):
            data = [data]
        out = []
        for item in data:
            cmd = (item.get("CommandLine") or "").split()
            out.append(_Proc(int(item.get("ProcessId") or 0), item.get("Name") or "", cmd))
        return out
    except Exception:
        return []

APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
PATHS_FILE = APP_DIR / "paths.json"

DEFAULTS = {
    "astrbot_dir": str(APP_DIR / "app" / "AstrBot"),
    "snowluma_dir": str(APP_DIR / "app" / "SnowLuma"),
    "qq_exe": "",
    "venv_python": str(APP_DIR / "app" / "AstrBot" / "venv" / "Scripts" / "python.exe"),
    "snowluma_node": str(APP_DIR / "app" / "SnowLuma" / "node.exe"),
    "astrbot_web": "http://127.0.0.1:6185",
    "snowluma_web": "http://127.0.0.1:5099",
}

QQ_CANDIDATES = (
    r"C:\apps\QQ\QQ.exe",
    r"C:\Program Files\Tencent\QQNT\QQ.exe",
    r"C:\Program Files (x86)\Tencent\QQNT\QQ.exe",
    r"C:\Program Files\Tencent\QQ\Bin\QQ.exe",
)


def _default_qq() -> str:
    for cand in QQ_CANDIDATES:
        try:
            if Path(cand).exists():
                return cand
        except Exception:
            continue
    return QQ_CANDIDATES[0]


CACHE_DIR = APP_DIR / "cache"


def model_env() -> dict:
    """把 HF / ModelScope / Torch 的缓存指到程序目录下的 cache，保证整个文件夹可整体搬走。"""
    e = {
        "HF_HOME": str(CACHE_DIR / "huggingface"),
        "HUGGINGFACE_HUB_CACHE": str(CACHE_DIR / "huggingface" / "hub"),
        "MODELSCOPE_CACHE": str(CACHE_DIR / "modelscope"),
        "TORCH_HOME": str(CACHE_DIR / "torch"),
    }
    for d in e.values():
        try:
            Path(d).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return e


def load_paths() -> dict:
    cfg = dict(DEFAULTS)
    cfg["qq_exe"] = _default_qq()
    try:
        if PATHS_FILE.exists():
            cfg.update(json.loads(PATHS_FILE.read_text(encoding="utf-8-sig")))
        else:
            PATHS_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return cfg


PATHS = load_paths()

# ---------------------------------------------------------------- 发行信息
def _release_candidates():
    yield APP_DIR / "tools" / "release.json"
    yield APP_DIR / "release.json"
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        yield Path(meipass) / "release.json"
    yield Path(__file__).parent / "release.json"


RELEASE_FILE = next((p for p in _release_candidates() if p.exists()),
                    Path(__file__).parent / "release.json")
_RELEASE = {
    "name": "大肥鱼控制台",
    "version": "0.0.0",
    "build": "",
    "repo": "",
    "issues": "",
    "license": "MIT",
    "author": "",
}
try:
    if RELEASE_FILE.exists():
        _RELEASE.update(json.loads(RELEASE_FILE.read_text(encoding="utf-8-sig")))
except Exception:
    pass

APP_NAME = str(_RELEASE.get("name") or "大肥鱼控制台")
APP_VERSION = str(_RELEASE.get("version") or "0.0.0")
BUILD_DATE = str(_RELEASE.get("build") or "")
REPO_URL = str(_RELEASE.get("repo") or "")
ISSUES_URL = str(_RELEASE.get("issues") or "")
LICENSE_NAME = str(_RELEASE.get("license") or "MIT")
AUTHOR = str(_RELEASE.get("author") or "")


def release_info() -> dict:
    return dict(_RELEASE)

SETTINGS_FILE = APP_DIR / "settings.json"
DEFAULT_SETTINGS = {
    "peak_gate": True,        # 谷时门禁：工作日高峰时段不允许启动
    "auto_qq": True,          # 「启动」时顺带拉起 QQ
    "close_action": "ask",    # ask / tray / quit
    "bg_image": "",           # 面板背景图路径（空 = 默认纯色）
}


def load_settings() -> dict:
    cfg = dict(DEFAULT_SETTINGS)
    try:
        if SETTINGS_FILE.exists():
            cfg.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8-sig")))
    except Exception:
        pass
    return cfg


def save_settings(cfg: dict) -> None:
    try:
        data = dict(DEFAULT_SETTINGS)
        data.update(cfg or {})
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

DETACHED = 0x00000008 | 0x08000000 | 0x00000200
# DETACHED_PROCESS | CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
# CREATE_NO_WINDOW 是必须的：Windows Terminal 作为默认终端时，少了它会弹出黑窗口。


# ---------------------------------------------------------------- 进程发现
def _iter_procs():
    if psutil is None:
        return _powershell_procs()
    out = []
    for p in psutil.process_iter(["pid", "name", "cmdline", "cwd"]):
        try:
            out.append(p)
        except Exception:
            continue
    return out


def find_pid(keyword: str, extra: str | None = None) -> int | None:
    needle = keyword.lower()
    for p in _iter_procs():
        try:
            cmd = " ".join(p.info.get("cmdline") or []).lower()
            if needle in cmd and (extra is None or extra.lower() in cmd):
                return p.info["pid"]
        except Exception:
            continue
    return None


def astrbot_pid() -> int | None:
    """只认真正的 python.exe 进程，避免把包着它的 cmd.exe 当成 AstrBot。"""
    for p in _iter_procs():
        try:
            name = (p.info.get("name") or "").lower()
            cmd = " ".join(p.info.get("cmdline") or []).lower()
            if name.startswith("python") and "main.py" in cmd:
                return p.info["pid"]
        except Exception:
            continue
    return None


def snowluma_pid() -> int | None:
    return find_pid("index.mjs") or find_pid("snowluma")


def qq_pid() -> int | None:
    for p in _iter_procs():
        try:
            name = (p.info.get("name") or "").lower()
            if name == "qq.exe":
                return p.info["pid"]
        except Exception:
            continue
    return None


def _self_chain() -> set[int]:
    """自己 + 所有祖先进程的 PID，任何情况下都不能被 stop 误杀。"""
    out = {os.getpid()}
    try:
        if psutil is not None:
            p = psutil.Process(os.getpid())
            while p is not None and p.pid not in out:
                out.add(p.pid)
                p = p.parent()
        else:
            import ctypes

            class _PE(ctypes.Structure):
                _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                            ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_void_p),
                            ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                            ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                            ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260)]

            k32 = ctypes.windll.kernel32
            cur = os.getpid()
            for _ in range(32):
                pe = _PE()
                pe.dwSize = ctypes.sizeof(_PE)
                if not k32.CreateToolhelp32Snapshot:
                    break
                snap = k32.CreateToolhelp32Snapshot(0x2, 0)
                if k32.Process32FirstW(snap, ctypes.byref(pe)):
                    while True:
                        if pe.th32ProcessID == cur:
                            cur = pe.th32ParentProcessID
                            out.add(cur)
                            break
                        if not k32.Process32NextW(snap, ctypes.byref(pe)):
                            cur = 0
                            break
                k32.CloseHandle(snap)
                if not cur:
                    break
    except Exception:
        pass
    return out


def kill_pid(pid: int | None) -> bool:
    if not pid:
        return False
    if pid in _self_chain():
        return False
    try:
        if psutil is None and pid:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            return True
        if psutil is not None:
            p = psutil.Process(pid)
            for child in p.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
            p.kill()
            return True
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        return True
    except Exception:
        return False


def port_alive(url: str, timeout: float = 0.9) -> bool:
    """只做一次 TCP 连接探测：HTTP GET 在服务已停时会一路等到超时（1.5s/次）。"""
    try:
        from urllib.parse import urlsplit

        parts = urlsplit(url)
        host = parts.hostname or "127.0.0.1"
        port = parts.port or (443 if parts.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=min(timeout, 0.25)):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------- 动作

def _hidden_popen(args, cwd, env, fh):
    """在隐藏的独立控制台里启动控制台程序。

    Windows Terminal 作为默认终端时，DETACHED_PROCESS 仍会让“子进程再 spawn 的进程”弹出黑窗口；
    给父进程一个 SW_HIDE 的新控制台，子进程就会继承它，不会再有窗口冒出来。
    """
    si = None
    flags = 0x00000010 | 0x00000200  # CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
    return subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=fh,
        stderr=subprocess.STDOUT,
        creationflags=flags,
        startupinfo=si,
        close_fds=True,
    )

def start_astrbot(log=print) -> bool:
    if astrbot_pid():
        log("AstrBot 已经在运行")
        return True
    exe = PATHS["venv_python"]
    cwd = PATHS["astrbot_dir"]
    log_path = Path(cwd) / "console.log"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", **model_env())
    with open(log_path, "ab") as fh:
        _hidden_popen([exe, "main.py"], cwd, env, fh)
    log(f"已启动 AstrBot（日志 {log_path}）")
    return True


def start_snowluma(log=print) -> bool:
    if snowluma_pid():
        log("SnowLuma 已经在运行")
        return True
    cwd = PATHS["snowluma_dir"]
    env = dict(
        os.environ,
        SNOWLUMA_ACCEPT_EULA="1",
        SNOWLUMA_ACCEPT_PRIVACY="1",
        SNOWLUMA_HOOK_AUTOLOAD="1",
    )
    log_path = Path(cwd) / "console.log"
    with open(log_path, "ab") as fh:
        _hidden_popen([PATHS["snowluma_node"], "index.mjs"], cwd, env, fh)
    log(f"已启动 SnowLuma（日志 {log_path}）")
    return True


def start_qq(log=print) -> bool:
    if qq_pid():
        log("QQ 已经在运行")
        return True
    exe = PATHS["qq_exe"]
    if not Path(exe).exists():
        log(f"找不到 QQ：{exe}")
        return False
    subprocess.Popen([exe], creationflags=DETACHED, close_fds=True)
    log("已启动 QQ")
    return True


def stop_astrbot(log=print) -> bool:
    pid = astrbot_pid()
    ok = kill_pid(pid)
    # 等它真的退出，避免“刚杀完就判断还在跑”
    end = time.time() + 15
    while time.time() < end and astrbot_pid():
        time.sleep(0.4)
    log("已停止 AstrBot" if ok else "AstrBot 没在运行")
    return ok


def stop_snowluma(log=print) -> bool:
    pid = snowluma_pid()
    ok = kill_pid(pid)
    log("已停止 SnowLuma" if ok else "SnowLuma 没在运行")
    return ok


def stop_qq(log=print) -> bool:
    pid = qq_pid()
    ok = kill_pid(pid)
    log("已停止 QQ" if ok else "QQ 没在运行")
    return ok


def wait_port(url: str, seconds: float = 30, log=print) -> bool:
    end = time.time() + seconds
    while time.time() < end:
        if port_alive(url):
            return True
        time.sleep(1)
    return False


def hot_restart(log=print) -> bool:
    """只重启 AstrBot：插件/配置/人设改完后用它热更新，不动 SnowLuma 和 QQ。"""
    stop_astrbot(log)
    time.sleep(1.0)
    start_astrbot(log)
    if wait_port(PATHS["astrbot_web"], 40, log):
        log("AstrBot 已热重启完成（6185 可访问）")
        return True
    log("AstrBot 重启后端口未就绪，去看 console.log")
    return False


def restart_all(log=print) -> bool:
    hot_restart(log)
    stop_snowluma(log)
    time.sleep(1)
    start_snowluma(log)
    wait_port(PATHS["snowluma_web"], 30, log)
    start_qq(log)
    return True


def status() -> dict:
    return {
        "astrbot": astrbot_pid(),
        "snowluma": snowluma_pid(),
        "qq": qq_pid(),
        "astrbot_web": port_alive(PATHS["astrbot_web"]),
        "snowluma_web": port_alive(PATHS["snowluma_web"]),
    }


def open_logs() -> None:
    for name in ("AstrBot", "SnowLuma"):
        p = Path(PATHS["astrbot_dir" if name == "AstrBot" else "snowluma_dir"]) / "console.log"
        if p.exists():
            subprocess.Popen(["notepad.exe", str(p)])


# ---------------------------------------------------------------- 环境体检
PLUGINS_DIR = Path(PATHS["astrbot_dir"]) / "data" / "plugins"
REQUIRED_FILE = APP_DIR / "required_plugins.json"

_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def _meta_field(path: Path, key: str) -> str:
    """从 metadata.yaml 里取一个简单标量字段（不引入 yaml 依赖）。"""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
            k, _, v = line.partition(":")
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def component_health() -> dict:
    """三个组件各自的安装完整性（关键文件是否存在）。"""
    astrbot = Path(PATHS["astrbot_dir"])
    snow = Path(PATHS["snowluma_dir"])
    venv = Path(PATHS["venv_python"])
    qq = Path(PATHS["qq_exe"])
    snow_entry = snow / "index.mjs"
    if not snow_entry.exists():
        snow_entry = snow / "launcher.bat"

    items = {
        "astrbot": [(astrbot / "main.py", "main.py"), (venv, "venv")],
        "snowluma": [(snow_entry, snow_entry.name), (snow / "package.json", "package.json")],
        "qq": [(qq, "QQ.exe")],
    }
    out: dict[str, dict] = {}
    for key, checks in items.items():
        missing = [label for path, label in checks if not path.exists()]
        out[key] = {
            "installed": not missing,
            "missing": missing,
            "detail": "文件齐全" if not missing else "缺少 " + "、".join(missing),
        }
    return out


def plugin_manifest() -> list[dict]:
    """必要插件清单。第一次运行时按已装插件生成 required_plugins.json，之后以文件为准。"""
    if REQUIRED_FILE.exists():
        try:
            data = json.loads(REQUIRED_FILE.read_text(encoding="utf-8-sig"))
            if isinstance(data, list) and data:
                out = []
                for it in data:
                    name = str(it.get("name") or "").strip()
                    if not name:
                        continue
                    out.append({
                        "name": name,
                        "repo": str(it.get("repo") or "").strip(),
                        "display": str(it.get("display") or name),
                    })
                if out:
                    return out
        except Exception:
            pass
    items: list[dict] = []
    try:
        for d in sorted(PLUGINS_DIR.iterdir()):
            if not d.is_dir() or d.name.endswith(".bak"):
                continue
            meta = d / "metadata.yaml"
            items.append({
                "name": d.name,
                "repo": _meta_field(meta, "repo"),
                "display": _meta_field(meta, "display_name") or d.name,
            })
    except Exception:
        pass
    try:
        REQUIRED_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return items


def scan_plugins() -> list[dict]:
    """逐个检查插件：ok / broken（目录在但缺文件）/ missing。"""
    out = []
    for it in plugin_manifest():
        d = PLUGINS_DIR / it["name"]
        meta = d / "metadata.yaml"
        if not d.exists():
            status = "missing"
        elif not (d / "main.py").exists() or not meta.exists():
            status = "broken"
        else:
            status = "ok"
        out.append({
            **it,
            "status": status,
            "installed": status == "ok",
            "version": _meta_field(meta, "version") if meta.exists() else "",
        })
    return out


def _pip_requirements(plugin_dir: Path) -> tuple[bool, str]:
    req = plugin_dir / "requirements.txt"
    if not req.exists():
        return True, ""
    py = Path(PATHS["venv_python"])
    if not py.exists():
        return True, "venv 不存在，跳过依赖安装"
    try:
        r = subprocess.run([str(py), "-m", "pip", "install", "-r", str(req), "-q"],
                           capture_output=True, text=True, timeout=600,
                           creationflags=_CREATE_NO_WINDOW)
        if r.returncode != 0:
            return False, (r.stderr or r.stdout or "").strip()[-300:]
        return True, ""
    except Exception as exc:
        return False, str(exc)


def install_plugin(item: dict, log=print) -> tuple[bool, str]:
    """从 GitHub 克隆并替换插件目录，再装 requirements.txt。"""
    name = str(item.get("name") or "").strip()
    repo = str(item.get("repo") or "").strip()
    if not name:
        return False, "插件名不能为空"
    if not repo:
        return False, f"{name} 没有配置 GitHub 仓库"
    tmp_root = CACHE_DIR / "plugin_src"
    tmp = tmp_root / name
    shutil.rmtree(tmp, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)
    log(f"正在从 GitHub 安装 {name} …")
    try:
        r = subprocess.run(["git", "clone", "--depth", "1", repo, str(tmp)],
                           capture_output=True, text=True, timeout=300,
                           creationflags=_CREATE_NO_WINDOW)
    except FileNotFoundError:
        return False, "找不到 git，请先安装 Git for Windows"
    except Exception as exc:
        return False, str(exc)
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "git clone 失败").strip()[-300:]

    src = tmp
    if not (src / "main.py").exists():
        nested = [p for p in src.iterdir() if p.is_dir() and (p / "main.py").exists()]
        if nested:
            src = nested[0]

    dst = PLUGINS_DIR / name
    if dst.exists():
        bak = PLUGINS_DIR / f"{name}.bak"
        shutil.rmtree(bak, ignore_errors=True)
        try:
            dst.rename(bak)
        except Exception:
            shutil.rmtree(dst, ignore_errors=True)
    try:
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    except Exception as exc:
        return False, f"复制失败：{exc}"
    ok, err = _pip_requirements(dst)
    shutil.rmtree(tmp, ignore_errors=True)
    if not ok:
        return False, f"已克隆，但依赖安装失败：{err}"
    return True, f"{name} 安装完成"


def install_missing_plugins(log=print) -> tuple[int, int]:
    """一键安装所有缺失/损坏的插件，返回（成功数，总数）。"""
    todo = [p for p in scan_plugins() if p["status"] != "ok"]
    ok = 0
    for item in todo:
        good, msg = install_plugin(item, log=log)
        log(msg)
        ok += 1 if good else 0
    return ok, len(todo)


# ------------------------------------------------------ 组件下载 / 安装
COMPONENT_HOME = {
    "astrbot": "https://github.com/AstrBotDevs/AstrBot",
    "snowluma": "https://github.com/SnowLuma/SnowLuma",
    "qq": "https://im.qq.com/pcqq/index.shtml",
}


def _github_latest(repo: str) -> dict:
    import json

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={
        "User-Agent": "DafeiyuBot",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


class DownloadCanceled(Exception):
    """用户取消了下载。"""


def _download(url: str, dest: Path, log=print, label: str = "",
              should_stop=None) -> Path:
    """带百分比进度回调的下载（可取消）。"""
    req = urllib.request.Request(url, headers={"User-Agent": "DafeiyuBot"})
    with urllib.request.urlopen(req, timeout=45) as resp, open(dest, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        step = 0
        while True:
            chunk = resp.read(262144)
            if not chunk:
                break
            fh.write(chunk)
            done += len(chunk)
            if should_stop is not None and should_stop():
                raise DownloadCanceled()
            if total:
                pct = done * 100 // total
                if pct >= step + 5:
                    step = pct - pct % 5
                    log(f"{label} {pct}%")
    return dest


GH_MIRRORS = ("", "https://gh-proxy.com/", "https://ghproxy.net/")


def _download_any(url: str, dest: Path, log=print, label: str = "",
                  should_stop=None) -> Path:
    """GitHub 直连经常超时，按直连→镜像的顺序重试。"""
    last = None
    for pre in GH_MIRRORS:
        try:
            return _download(pre + url, dest, log=log, label=label,
                             should_stop=should_stop)
        except Exception as exc:
            last = exc
            if pre:
                log(f"{label} 镜像 {pre.split('/')[2]} 失败，继续尝试下一个…")
    raise last if last else RuntimeError("下载失败")


def _base_python() -> str | None:
    """找一个能用来创建 venv 的 python。"""
    if getattr(sys, "frozen", False):
        cand = Path(sys.executable).resolve().parent / "runtime" / "python312" / "python.exe"
        if cand.exists():
            return str(cand)
    for name in ("python.exe", "python3.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _extract_zip(zip_path: Path, dest: Path, log=print) -> bool:
    import zipfile

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        root = ""
        tops = {n.split("/")[0] for n in names if "/" in n}
        if len(tops) == 1 and all(n.startswith(next(iter(tops)) + "/") or n == next(iter(tops)) for n in names):
            root = next(iter(tops)) + "/"
        dest.mkdir(parents=True, exist_ok=True)
        for m in zf.infolist():
            if m.is_dir():
                continue
            rel = m.filename[len(root):] if root and m.filename.startswith(root) else m.filename
            if not rel or rel.endswith("/"):
                continue
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m) as src, open(out, "wb") as fh:
                shutil.copyfileobj(src, fh)
    log(f"已解压到 {dest}")
    return True


def install_component(key: str, log=print, should_stop=None) -> tuple[bool, str]:
    """缺失时下载并安装 AstrBot / SnowLuma / QQ。"""
    key = (key or "").lower()
    if key == "qq":
        import webbrowser
        try:
            webbrowser.open(COMPONENT_HOME["qq"])
            return True, "已打开 QQ 官方下载页，装好点「刷新」"
        except Exception as exc:  # pragma: no cover
            return False, f"打不开下载页：{exc}"

    if key == "snowluma":
        target = Path(PATHS["snowluma_dir"])
        try:
            rel = _github_latest("SnowLuma/SnowLuma")
        except Exception as exc:
            return False, f"查询 SnowLuma 版本失败：{exc}"
        assets = rel.get("assets") or []
        asset = None
        for a in assets:
            name = a.get("name", "")
            if "win" in name and "x64" in name and name.endswith(".zip") and "lite" not in name:
                asset = a
                break
        if not asset:
            return False, "SnowLuma 最新版没有找到 Windows 包"
        tmp = CACHE_DIR / "downloads" / asset["name"]
        tmp.parent.mkdir(parents=True, exist_ok=True)
        log(f"开始下载 SnowLuma {rel.get('tag_name', '')}（{asset['size'] // 1048576} MB）")
        try:
            _download_any(asset["browser_download_url"], tmp, log=log,
                          label="SnowLuma", should_stop=should_stop)
        except Exception as exc:
            return False, f"下载 SnowLuma 失败：{exc}"
        try:
            if target.exists():
                bak = target.with_name(target.name + ".bak")
                if bak.exists():
                    shutil.rmtree(bak, ignore_errors=True)
                target.rename(bak)
            _extract_zip(tmp, target, log=log)
        except Exception as exc:
            return False, f"解压 SnowLuma 失败：{exc}"
        return True, f"SnowLuma {rel.get('tag_name', '')} 已装到 {target}"

    if key == "astrbot":
        target = Path(PATHS["astrbot_dir"])
        if (target / "main.py").exists():
            return True, "AstrBot 目录已存在"
        if target.exists():
            bak = target.with_name(target.name + ".bak")
            if bak.exists():
                shutil.rmtree(bak, ignore_errors=True)
            target.rename(bak)
        target.parent.mkdir(parents=True, exist_ok=True)
        log("开始下载 AstrBot 源码…")
        try:
            subprocess.run(["git", "clone", "--depth", "1",
                            COMPONENT_HOME["astrbot"], str(target)],
                           check=True, capture_output=True, timeout=600)
        except FileNotFoundError:
            tmp = CACHE_DIR / "downloads" / "astrbot.zip"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            try:
                _download_any("https://github.com/AstrBotDevs/AstrBot/archive/refs/heads/master.zip",
                              tmp, log=log, label="AstrBot", should_stop=should_stop)
                _extract_zip(tmp, target, log=log)
            except Exception as exc:
                return False, f"下载 AstrBot 失败：{exc}"
        except Exception as exc:
            return False, f"克隆 AstrBot 失败：{exc}"

        base = _base_python()
        if not base:
            return False, "AstrBot 源码已下载，但本机没有可用的 python 来建虚拟环境"
        venv_dir = target / "venv"
        log("正在创建 AstrBot 虚拟环境（需要几分钟）…")
        try:
            subprocess.run([base, "-m", "venv", str(venv_dir)],
                           check=True, capture_output=True, timeout=600)
        except Exception as exc:
            return False, f"创建虚拟环境失败：{exc}"
        py = venv_dir / "Scripts" / "python.exe"
        req = target / "requirements.txt"
        if py.exists() and req.exists():
            log("正在安装 AstrBot 依赖（这一步最慢）…")
            try:
                subprocess.run([str(py), "-m", "pip", "install", "-q",
                                "--disable-pip-version-check", "-r", str(req)],
                               check=True, capture_output=True, timeout=3600)
            except Exception as exc:
                return False, f"AstrBot 依赖安装失败：{exc}"
        return True, f"AstrBot 已装到 {target}"

    return False, f"不认识的组件：{key}"


# ---------------------------------------------------------------- 图形界面
BG = "#F3F3F3"
CARD = "#FFFFFF"
BORDER = "#E5E5E5"
TEXT = "#1B1B1B"
SUB = "#616161"
ACCENT = "#0067C0"
ACCENT_HOVER = "#1975C5"
GREEN = "#0F7B0F"
GREY_DOT = "#C7C7C7"
W, H = 420, 544


def _round(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, splinesteps=24, **kw)


def _win11_frame(root):
    """Win11 圆角 + Mica 背景（老系统上失败就算了）。"""
    try:
        import ctypes

        root.update_idletasks()
        hwnd = int(ctypes.windll.user32.GetParent(root.winfo_id()))
        dwm = ctypes.windll.dwmapi
        corner = ctypes.c_int(2)  # DWMWCP_ROUND
        dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner))
        backdrop = ctypes.c_int(2)  # Mica
        dwm.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        dark = ctypes.c_int(0)
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
    except Exception:
        pass


def _already_running() -> bool:
    """同一个面板只允许开一个，重复双击时静默退出。"""
    if os.name != "nt":
        return False
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW(None, False, "DafeiyuBotPanel")
        return kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS
    except Exception:
        return False




def _activate_existing() -> bool:
    """重复双击时，把已经藏在托盘里的面板叫回来。"""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "大肥鱼控制台")
        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            return True
    except Exception:
        pass
    return False

def run_gui() -> None:  # pragma: no cover - UI
    if _already_running():
        _activate_existing()
        return
    import panel_ui

    panel_ui.run()
    return
    import tkinter as tk
    import threading

    root = tk.Tk()
    root.title("大肥鱼控制台")
    root.geometry(f"{W}x{H}")
    root.configure(bg=BG)
    root.resizable(False, False)
    try:
        root.tk.call("tk", "scaling", 1.25)
    except Exception:
        pass

    title_font = ("Segoe UI Variable Display", 15, "bold")
    body_font = ("Segoe UI Variable Text", 10)
    small_font = ("Segoe UI Variable Text", 9)
    mono_font = ("Cascadia Mono", 8)

    cv = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0, bd=0)
    cv.pack(fill="both", expand=True)

    cv.create_text(24, 30, text="大肥鱼控制台", anchor="w", font=title_font, fill=TEXT)
    cv.create_text(24, 58, text="AstrBot · SnowLuma · QQ", anchor="w", font=small_font, fill=SUB)

    # ---- 状态卡片
    _round(cv, 16, 80, W - 16, 200, 10, fill=CARD, outline=BORDER)
    rows = {}
    for i, (key, name) in enumerate((("astrbot", "AstrBot"), ("snowluma", "SnowLuma"), ("qq", "QQ"))):
        y = 104 + i * 32
        dot = cv.create_oval(30, y - 4, 38, y + 4, fill=GREY_DOT, outline="")
        cv.create_text(50, y, text=name, anchor="w", font=body_font, fill=TEXT)
        val = cv.create_text(W - 32, y, text="检测中", anchor="e", font=small_font, fill=SUB)
        rows[key] = (dot, val)

    # ---- 按钮
    buttons = {}

    def button(x1, y1, x2, y2, text, cmd, kind="secondary", radius=8):
        fill = {"primary": ACCENT, "secondary": CARD, "ghost": BG}[kind]
        hover = {"primary": ACCENT_HOVER, "secondary": "#F5F5F5", "ghost": "#EAEAEA"}[kind]
        fg = "#FFFFFF" if kind == "primary" else TEXT
        outline = "" if kind in ("primary", "ghost") else BORDER
        rect = _round(cv, x1, y1, x2, y2, radius, fill=fill, outline=outline, tags=("btn",))
        label = cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, font=body_font, fill=fg, tags=("btn",))
        buttons[id(rect)] = (rect, label, fill, hover)

        def on_enter(_e, r=rect, h=hover):
            cv.itemconfigure(r, fill=h)
            cv.configure(cursor="hand2")

        def on_leave(_e, r=rect, f=fill):
            cv.itemconfigure(r, fill=f)
            cv.configure(cursor="")

        def on_click(_e, c=cmd):
            c()

        for item in (rect, label):
            cv.tag_bind(item, "<Enter>", on_enter)
            cv.tag_bind(item, "<Leave>", on_leave)
            cv.tag_bind(item, "<Button-1>", on_click)

    def link(x, y, text, cmd):
        t = cv.create_text(x, y, text=text, anchor="w", font=small_font, fill=ACCENT)
        cv.tag_bind(t, "<Button-1>", lambda _e: cmd())
        cv.tag_bind(t, "<Enter>", lambda _e: cv.configure(cursor="hand2"))
        cv.tag_bind(t, "<Leave>", lambda _e: cv.configure(cursor=""))
        return t

    # ---- 日志卡片
    _round(cv, 16, 366, W - 16, H - 62, 10, fill=CARD, outline=BORDER)
    cv.create_text(32, 382, text="日志", anchor="w", font=small_font, fill=SUB)
    log_items = []
    for i in range(4):
        log_items.append(cv.create_text(32, 404 + i * 22, text="", anchor="w", font=mono_font, fill="#424242"))

    lines = []

    def log(msg: str) -> None:
        lines.append(f"{time.strftime('%H:%M')}  {msg}")
        del lines[:-4]
        for item, text in zip(log_items, lines):
            cv.itemconfigure(item, text=text)

    def bg(fn):
        def runner():
            try:
                fn(log)
            except Exception as e:  # noqa: BLE001
                log(f"出错了：{e}")

        threading.Thread(target=runner, daemon=True).start()

    def open_logs_ui():
        open_logs()

    def copy_status():
        st = status()
        root.clipboard_clear()
        root.clipboard_append(json.dumps(st, ensure_ascii=False))
        log("状态已复制到剪贴板")

    button(16, 216, 254, 258, "启动", lambda: bg(lambda lg: (
        start_astrbot(lg), wait_port(PATHS["astrbot_web"], 30, lg),
        start_snowluma(lg), wait_port(PATHS["snowluma_web"], 30, lg), start_qq(lg))), "primary")
    button(262, 216, W - 16, 258, "全部停止", lambda: bg(lambda lg: (
        stop_qq(lg), stop_snowluma(lg), stop_astrbot(lg))))
    button(16, 266, 207, 306, "热重启 AstrBot", lambda: bg(hot_restart))
    button(215, 266, W - 16, 306, "重启协议端", lambda: bg(lambda lg: (
        stop_snowluma(lg), time.sleep(1), start_snowluma(lg),
        wait_port(PATHS["snowluma_web"], 30, lg))))
    button(16, 314, 207, 350, "全部重启", lambda: bg(restart_all), "ghost")
    button(215, 314, W - 16, 350, "打开面板", lambda: (
        webbrowser.open(PATHS["astrbot_web"]), webbrowser.open(PATHS["snowluma_web"])), "ghost")

    link(24, H - 26, "看日志", open_logs_ui)
    link(104, H - 26, "打开目录", lambda: os.startfile(PATHS["astrbot_dir"]))
    link(196, H - 26, "复制状态", copy_status)

    def refresh():
        st = status()
        for key, (dot, val) in rows.items():
            pid = st.get(key)
            if pid:
                cv.itemconfigure(dot, fill=GREEN)
                cv.itemconfigure(val, text=f"运行中 · {pid}", fill=SUB)
            else:
                cv.itemconfigure(dot, fill=GREY_DOT)
                cv.itemconfigure(val, text="未运行", fill="#9E9E9E")
        root.after(2500, refresh)

    refresh()
    _win11_frame(root)
    log("就绪 · 改完插件点「热重启 AstrBot」即可生效")
    if not Path(PATHS["venv_python"]).exists():
        log(f"找不到 Python：{PATHS['venv_python']}")
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------- 命令行
class _Tee:
    """同时写控制台和日志文件，windowed exe 也能留下可查看的输出。"""

    def __init__(self, *streams):
        self.streams = [s for s in streams if s]

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass
        return len(data)

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


def _attach_console() -> None:
    if not getattr(sys, "frozen", False):
        return
    streams = []
    try:
        import ctypes

        k32 = ctypes.windll.kernel32
        attached = False
        if k32.GetConsoleWindow() == 0:
            # 只挂到已有的父控制台；绝不 AllocConsole，避免无端弹出一个黑窗口
            attached = bool(k32.AttachConsole(-1))
        else:
            attached = True
        if attached:
            streams.append(open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1))
    except Exception:
        pass
    try:
        streams.append(open(APP_DIR / "BotCtrl.log", "w", encoding="utf-8", errors="replace", buffering=1))
    except Exception:
        pass
    if streams:
        sys.stdout = _Tee(*streams)
        sys.stderr = sys.stdout


PEAK_MESSAGE = "现在是高峰时段（周一至周五 9:00-12:00、14:00-18:00），模型贵一倍，先歇会儿。真要启动就加 force。"


def is_peak(now=None) -> bool:
    """DeepSeek 高峰时段：工作日 9:00-12:00 与 14:00-18:00（本地时间）。"""
    now = now or time.localtime()
    if now.tm_wday >= 5:
        return False
    minutes = now.tm_hour * 60 + now.tm_min
    return 540 <= minutes < 720 or 840 <= minutes < 1080



def main() -> None:
    args = sys.argv[1:]
    if args:
        _attach_console()
    if not args:
        run_gui()
        return
    cmd = args[0].lower()
    force = any(a.lower() in ("force", "-f", "--force") for a in args[1:])
    if (cmd in ("start", "up", "restart", "reboot")
            and load_settings().get("peak_gate", True) and is_peak() and not force):
        print(PEAK_MESSAGE)
        return
    if cmd in ("start", "up"):
        start_astrbot()
        wait_port(PATHS["astrbot_web"], 40)
        start_snowluma()
        wait_port(PATHS["snowluma_web"], 30)
        if load_settings().get("auto_qq", True):
            start_qq()
    elif cmd in ("stop", "down"):
        stop_qq()
        stop_snowluma()
        stop_astrbot()
    elif cmd in ("restart", "reboot"):
        restart_all()
    elif cmd in ("hot", "reload"):
        hot_restart()
    elif cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=2))
    elif cmd in ("web", "panel"):
        webbrowser.open(PATHS["astrbot_web"])
        webbrowser.open(PATHS["snowluma_web"])
    elif cmd == "logs":
        open_logs()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
