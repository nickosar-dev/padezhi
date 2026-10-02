#!/usr/bin/env python3
"""Проверяет packs/*.txt и пересобирает packs/index.json, который читает приложение.

Запуск: python3 build_packs.py
Порядок пакетов в index.json сохраняется, новые файлы добавляются в конец.
При ошибках index.json не перезаписывается и скрипт выходит с кодом 1.
"""
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKS = ROOT / "packs"
INDEX = PACKS / "index.json"
CLOZE = re.compile(r"\{\{c(\d+)::(.*?)(?:::(.*?))?\}\}", re.S)
ALLOWED_TAGS = re.compile(r"</?(?:br|i|b)\s*/?>", re.I)
CASE_TAGS = {"gen", "acc", "dat", "instr", "loc", "voc"}


def norm(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def title_of(lines, stem):
    for line in lines:
        if line.startswith("#deck:"):
            parts = [p.strip() for p in line[len("#deck:"):].split("::") if p.strip()]
            if len(parts) > 1 and parts[0].lower() == "polish":
                parts = parts[1:]
            if parts:
                return " · ".join(parts)
    return stem


def check(path, seen):
    errors, warnings, count = [], [], 0
    lines = path.read_text(encoding="utf-8").splitlines()
    for n, line in enumerate(lines, 1):
        if not line.strip() or line.startswith("#"):
            continue
        where = f"{path.name}:{n}"
        cols = line.split("\t")
        if len(cols) != 3:
            errors.append(f"{where}: нужно 3 колонки через Tab (текст, пояснение, теги), а их {len(cols)}")
            continue
        text, extra, tags = cols
        clozes = CLOZE.findall(text)
        if not clozes:
            errors.append(f"{where}: нет пропуска {{{{c1::…}}}}")
            continue
        if text.count("{{") != text.count("}}"):
            errors.append(f"{where}: не закрыты фигурные скобки")
        for field in (text, extra):
            rest = ALLOWED_TAGS.sub("", field)
            if re.search(r"<[a-zA-Z/][^>]*>", rest):
                warnings.append(f"{where}: HTML кроме <br> <i> <b> покажется как текст")
        nums = sorted({int(c[0]) for c in clozes})
        if nums != list(range(1, len(nums) + 1)):
            warnings.append(f"{where}: номера пропусков идут не подряд: {nums}")
        cases = [t for t in tags.split() if t in CASE_TAGS]
        if len(cases) > len(nums):
            warnings.append(f"{where}: падежных тегов ({len(cases)}) больше, чем пропусков ({len(nums)})")
        key = norm(text)
        if key in seen:
            warnings.append(f"{where}: такая же заметка уже есть в {seen[key]} (покажется один раз)")
        else:
            seen[key] = where
        count += 1
    return lines, count, errors, warnings


def main():
    old = []
    if INDEX.exists():
        old = [p["id"] for p in json.loads(INDEX.read_text(encoding="utf-8")).get("packs", [])]
    files = {p.stem: p for p in PACKS.glob("*.txt")}
    order = [i for i in old if i in files] + sorted(i for i in files if i not in old)

    seen, packs, all_errors = {}, [], []
    for pid in order:
        path = files[pid]
        lines, count, errors, warnings = check(path, seen)
        all_errors += errors
        for w in warnings:
            print("предупреждение:", w)
        packs.append({
            "id": pid,
            "file": f"packs/{path.name}",
            "title": title_of(lines, pid),
            "notes": count,
            "hash": hashlib.sha1(path.read_bytes()).hexdigest()[:10],
        })
        print(f"{pid}: {count} заметок — {packs[-1]['title']}")

    if all_errors:
        for e in all_errors:
            print("ОШИБКА:", e)
        print("index.json не обновлён.")
        sys.exit(1)

    INDEX.write_text(json.dumps({
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "packs": packs,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"index.json: {len(packs)} пакетов")


if __name__ == "__main__":
    main()
