# -*- coding: utf-8 -*-
"""Build the release package: exe + runtime + docs -> zip."""
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
meta = json.loads((HERE / "release.json").read_text(encoding="utf-8-sig"))
ver = meta["version"]
name = f"大肥鱼控制台-v{ver}"

print("[1/5] 生成版本信息")
subprocess.run([sys.executable, str(HERE / "_mkver.py")], check=True)

print("[2/5] PyInstaller 构建")
exe_build = subprocess.run(
    [str(HERE / "buildenv" / "Scripts" / "pyinstaller.exe"), "--noconfirm",
     "--clean", "BotCtrl.spec"],
    cwd=str(HERE), capture_output=True, text=True)
if exe_build.returncode != 0:
    print(exe_build.stdout[-3000:])
    print(exe_build.stderr[-3000:])
    raise SystemExit("构建失败")
exe = HERE / "dist" / "BotCtrl.exe"
print("    ", exe, exe.stat().st_size, "bytes")

DOCS = HERE / "docs"
if not DOCS.exists():
    DOCS = ROOT / "docs"
out = HERE / "dist" / "release" / name
print("[3/5] 组装目录", out)
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

shutil.copy2(exe, out / "大肥鱼控制台.exe")
for doc in ("CHANGELOG.md", "使用说明.txt"):
    shutil.copy2(DOCS / doc, out / doc)
shutil.copy2(ROOT / "README.md", out / "README.md")
shutil.copy2(ROOT / "LICENSE", out / "LICENSE")
if (DOCS / "screenshot-main.png").exists():
    (out / "docs").mkdir(exist_ok=True)
    shutil.copy2(DOCS / "screenshot-main.png", out / "docs" / "screenshot-main.png")
# 发行信息跟着走，便于用户自己改仓库地址
shutil.copy2(HERE / "release.json", out / "release.json")
(out / "tools").mkdir(exist_ok=True)
shutil.copy2(HERE / "release.json", out / "tools" / "release.json")

runtime_src = ROOT / "runtime" / "python312"
if runtime_src.exists():
    print("[4/5] 复制内置 Python（158MB 左右，请稍等）")
    shutil.copytree(runtime_src, out / "runtime" / "python312",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
else:
    print("[4/5] 警告：没有找到 runtime\\python312，包里将缺少内置 Python")

zip_path = HERE / "dist" / f"{name}-win64.zip"
print("[5/5] 打包", zip_path)
if zip_path.exists():
    zip_path.unlink()
t0 = time.time()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for f in out.rglob("*"):
        if f.is_file():
            zf.write(f, f.relative_to(out.parent))
print(f"完成：{zip_path}  {zip_path.stat().st_size / 1048576:.1f} MB  "
      f"用时 {time.time() - t0:.0f}s")
