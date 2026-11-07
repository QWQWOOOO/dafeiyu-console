# -*- coding: utf-8 -*-
"""Generate version_info.txt (Windows exe 属性) from release.json."""
import json
from pathlib import Path

here = Path(__file__).parent
meta = json.loads((here / "release.json").read_text(encoding="utf-8-sig"))
parts = [int(x) for x in str(meta.get("version", "1.0.0")).split(".") if x.isdigit()]
while len(parts) < 4:
    parts.append(0)
ver = tuple(parts[:4])
ver_str = ".".join(str(x) for x in ver)

text = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={ver},
    prodvers={ver},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('080404B0', [
        StringStruct('CompanyName', '{meta.get("author", "")}'),
        StringStruct('FileDescription', '{meta.get("name", "大肥鱼控制台")}'),
        StringStruct('FileVersion', '{ver_str}'),
        StringStruct('InternalName', 'BotCtrl'),
        StringStruct('LegalCopyright', 'Copyright (C) 2026 {meta.get("author", "")} · {meta.get("license", "MIT")}'),
        StringStruct('OriginalFilename', '大肥鱼控制台.exe'),
        StringStruct('ProductName', '{meta.get("name", "大肥鱼控制台")}'),
        StringStruct('ProductVersion', '{ver_str}')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [2052, 1200])])
  ]
)
"""
(here / "version_info.txt").write_text(text, encoding="utf-8")
print("version_info.txt:", ver_str)
