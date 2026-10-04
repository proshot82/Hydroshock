#!/usr/bin/env python3
"""Сверка md5 документов с MANIFEST_MD5.txt (замена md5sum для Windows).

Запуск из корня репозитория:  python tools/check_docs.py
Код выхода: 0 — все суммы совпали; 1 — есть расхождения или пропажи.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "MANIFEST_MD5.txt"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    bad = 0
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        path = ROOT / name.strip().removeprefix("./")
        if not path.is_file():
            print(f"НЕТ ФАЙЛА  {name}")
            bad += 1
            continue
        actual = hashlib.md5(path.read_bytes()).hexdigest()
        if actual == expected:
            print(f"OK         {name}")
        else:
            print(f"НЕ СОВПАЛ  {name}: {actual}, ждали {expected} — файл пересохранён? Руками не чинить.")
            bad += 1
    print("ИТОГ: все суммы совпали" if not bad else f"ИТОГ: расхождений {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
