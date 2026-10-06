#!/usr/bin/env python3
"""Проверяет пакеты packs/*.json (и старые packs/*.txt) и пересобирает packs/index.json.

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
CASES = {"nom", "gen", "dat", "acc", "instr", "loc", "voc"}
TOPICS = CASES | {"decl", "pres", "past", "fut", "imper", "cond", "aspect", "verb", "prep", "pron", "adj", "mos"}
TYPES = {"cloze", "choice", "table"}


def norm(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def key_of(it):
    """Тот же ключ, из которого приложение считает id заметки (keyOf в index.html)."""
    if it.get("type", "cloze") == "cloze":
        return it["text"] + (f"<br><i>{it['tr']}</i>" if it.get("tr") else "")
    if it["type"] == "choice":
        return f"choice|{it['q']}|{it['answer']}"
    return "table|" + it["q"] + "|" + "|".join(r[1] for r in it["rows"])


def html_warnings(where, *fields):
    out = []
    for f in fields:
        if isinstance(f, str) and re.search(r"<[a-zA-Z/][^>]*>", ALLOWED_TAGS.sub("", f)):
            out.append(f"{where}: HTML кроме <br> <i> <b> покажется как текст")
    return out


def check_cloze(where, text):
    errors, warnings = [], []
    clozes = CLOZE.findall(text)
    if not clozes:
        errors.append(f"{where}: нет пропуска {{{{c1::…}}}}")
        return errors, warnings, []
    if text.count("{{") != text.count("}}"):
        errors.append(f"{where}: не закрыты фигурные скобки")
    nums = sorted({int(c[0]) for c in clozes})
    if nums != list(range(1, len(nums) + 1)):
        warnings.append(f"{where}: номера пропусков идут не подряд: {nums}")
    return errors, warnings, nums


def check_item(where, it):
    errors, warnings = [], []
    t = it.get("type", "cloze")
    if t not in TYPES:
        return [f"{where}: неизвестный type «{t}»"], [], 0
    if it.get("level", 2) not in (1, 2, 3):
        errors.append(f"{where}: level должен быть 1, 2 или 3")
    for topic in it.get("topics", []):
        if topic not in TOPICS:
            errors.append(f"{where}: неизвестная тема «{topic}»")
    for k, tps in (it.get("per") or {}).items():
        for topic in tps:
            if topic not in TOPICS:
                errors.append(f"{where}: неизвестная тема «{topic}» в per[{k}]")
    warnings += html_warnings(where, it.get("text"), it.get("q"), it.get("tr"), it.get("note"))
    cards = 1
    if t == "cloze":
        if not isinstance(it.get("text"), str):
            return errors + [f"{where}: у пропуска нет text"], warnings, 0
        e, w, nums = check_cloze(where, it["text"])
        errors += e
        warnings += w
        cards = len(nums)
    elif t == "choice":
        opts = it.get("options") or []
        if not it.get("q"):
            errors.append(f"{where}: у выбора нет q")
        if not 2 <= len(opts) <= 6:
            errors.append(f"{where}: вариантов должно быть от 2 до 6")
        if len(set(opts)) != len(opts):
            errors.append(f"{where}: варианты повторяются")
        if it.get("answer") not in opts:
            errors.append(f"{where}: answer нет среди options")
        warnings += html_warnings(where, *opts)
    else:
        rows = it.get("rows") or []
        if not it.get("q"):
            errors.append(f"{where}: у таблицы нет q")
        if not rows:
            errors.append(f"{where}: у таблицы нет rows")
        for r in rows:
            if not (isinstance(r, list) and 2 <= len(r) <= 3 and str(r[0]).strip() and str(r[1]).strip()):
                errors.append(f"{where}: строка таблицы должна быть [подпись, ответ] или [подпись, ответ, 1]: {r}")
        if rows and all(len(r) > 2 and r[2] for r in rows):
            errors.append(f"{where}: в таблице нечего заполнять")
    return errors, warnings, cards


def check_json(path, seen):
    errors, warnings, cards, n = [], [], 0, 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, 0, 0, [f"{path.name}: битый JSON: {e}"], []
    title = data.get("title") or path.stem
    for i, it in enumerate(data.get("items", []), 1):
        where = f"{path.name}#{i}"
        e, w, c = check_item(where, it)
        errors += e
        warnings += w
        if e:
            continue
        key = norm(key_of(it))
        if key in seen:
            warnings.append(f"{where}: такая же заметка уже есть в {seen[key]} (покажется один раз)")
        else:
            seen[key] = where
        cards += c
        n += 1
    return title, n, cards, errors, warnings


def check_txt(path, seen):
    """Старый формат Anki: текст<TAB>пояснение<TAB>теги."""
    errors, warnings, cards, n, title = [], [], 0, 0, path.stem
    for num, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#deck:"):
            parts = [p.strip() for p in line[6:].split("::") if p.strip()]
            if len(parts) > 1 and parts[0].lower() == "polish":
                parts = parts[1:]
            title = " · ".join(parts) or title
        if not line.strip() or line.startswith("#"):
            continue
        where = f"{path.name}:{num}"
        cols = line.split("\t")
        if len(cols) != 3:
            errors.append(f"{where}: нужно 3 колонки через Tab (текст, пояснение, теги), а их {len(cols)}")
            continue
        e, w, nums = check_cloze(where, cols[0])
        errors += e
        warnings += w + html_warnings(where, cols[0], cols[1])
        key = norm(cols[0])
        if key in seen:
            warnings.append(f"{where}: такая же заметка уже есть в {seen[key]} (покажется один раз)")
        else:
            seen[key] = where
        cards += len(nums)
        n += 1
    return title, n, cards, errors, warnings


def check_lexicon():
    """lexicon.json — словарь тренировки во вкладке «Грамматика»."""
    path = ROOT / "lexicon.json"
    errors = []
    try:
        lex = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"lexicon.json: {e}"]

    def need(where, value, n):
        if not (isinstance(value, list) and len(value) == n and all(isinstance(x, str) for x in value)):
            errors.append(f"lexicon.json {where}: нужен список из {n} строк")

    nouns = {}
    for n in lex.get("nouns", []):
        w = f"nouns/{n.get('pl')}"
        nouns[n.get("pl")] = n
        need(w + ".sg", n.get("sg"), 7)
        need(w + ".rsg", n.get("rsg"), 6)
        if n.get("pln") is not None or n.get("rpl") is not None:
            need(w + ".pln", n.get("pln"), 6)
            need(w + ".rpl", n.get("rpl"), 6)
        if not n.get("cls"):
            errors.append(f"lexicon.json {w}: нет cls")
    ru_token = re.compile(r"\{(?:[^:{}]+:)?(\w+)\}")
    for case, tpls in lex.get("cases", {}).items():
        for t in tpls:
            if t["pl"].count("___") != 1:
                errors.append(f"lexicon.json cases/{case}: в «{t['pl']}» должно быть одно ___")
            for tok in ru_token.findall(t["ru"]):
                if tok not in ("nom", "gen", "dat", "acc", "instr", "prep"):
                    errors.append(f"lexicon.json cases/{case}: неизвестный падеж {{{tok}}}")
    for p in lex.get("pronouns", []):
        for k in ("gen", "dat", "acc", "instr", "loc"):
            if not p.get("f", {}).get(k) or not p.get("r", {}).get(k):
                errors.append(f"lexicon.json pronouns/{p.get('pl')}: нет формы {k}")
    for t in lex.get("preps", []):
        w = f"preps/{t.get('prep')}+{t.get('case')}"
        if t["pl"].count("___") != 1:
            errors.append(f"lexicon.json {w}: в «{t['pl']}» должно быть одно ___")
        for name in t.get("only", []):
            if name not in nouns:
                errors.append(f"lexicon.json {w}: слова «{name}» нет в nouns")
    for v in lex.get("verbs", []):
        w = f"verbs/{v.get('inf')}"
        need(w + ".pres", v.get("pres"), 6)
        need(w + ".rpres", v.get("rpres"), 6)
        need(w + ".past", v.get("past"), 4)
        need(w + ".rpast", v.get("rpast"), 4)
        if v.get("imper") is not None:
            need(w + ".imper", v.get("imper"), 3)
            need(w + ".rimper", v.get("rimper"), 3)
        if not str(v.get("past", [""])[0]).endswith("em"):
            errors.append(f"lexicon.json {w}: past[0] — форма «ja, м.р.» на -em")
        if v.get("perf"):
            need(w + ".perf.fut", v["perf"].get("fut"), 6)
            need(w + ".perf.rfut", v["perf"].get("rfut"), 6)
    print(f"lexicon.json: {len(nouns)} существительных, {len(lex.get('verbs', []))} глаголов, "
          f"{len(lex.get('preps', []))} шаблонов с предлогами")
    return errors


def main():
    lex_errors = check_lexicon()
    old = []
    if INDEX.exists():
        old = [p["id"] for p in json.loads(INDEX.read_text(encoding="utf-8")).get("packs", [])]
    files = {}
    for p in sorted(PACKS.glob("*.json")) + sorted(PACKS.glob("*.txt")):
        if p.name == INDEX.name:
            continue
        if p.stem in files:
            print(f"ОШИБКА: два пакета с именем {p.stem}: {files[p.stem].name} и {p.name}")
            sys.exit(1)
        files[p.stem] = p
    order = [i for i in old if i in files] + sorted(i for i in files if i not in old)

    seen, packs, all_errors = {}, [], lex_errors
    for pid in order:
        path = files[pid]
        check = check_json if path.suffix == ".json" else check_txt
        title, n, cards, errors, warnings = check(path, seen)
        all_errors += errors
        for w in warnings:
            print("предупреждение:", w)
        packs.append({
            "id": pid,
            "file": f"packs/{path.name}",
            "title": title or pid,
            "notes": n,
            "cards": cards,
            "hash": hashlib.sha1(path.read_bytes()).hexdigest()[:10],
        })
        print(f"{pid}: {n} заметок, {cards} карточек — {packs[-1]['title']}")

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
