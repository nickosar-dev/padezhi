#!/usr/bin/env python3
"""Собирает курс: packs/course.json (уроки, объяснения, стих) и packs/norwid-kurs.json (упражнения уроков).

Запуск: python3 make_course.py && python3 build_packs.py
Формы слов берутся из lexicon.json, поэтому ответы карточек всегда совпадают со словарём.
Предложения и переводы написаны здесь вручную. Порядок тем — как в учебных грамматиках
(род → согласование → być → настоящее время → падежи ед. ч. → мн. ч. → времена).
Ключ карточки (а значит, прогресс) зависит от текста задания: правка текста = новая карточка.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEX = json.loads((ROOT / "lexicon.json").read_text(encoding="utf-8"))
NOUN = {n["pl"]: n for n in LEX["nouns"]}
ADJ = {a["pl"]: a for a in LEX["adjs"]}
CI = dict(nom=0, gen=1, dat=2, acc=3, instr=4, loc=5, voc=6)

# род существительных: m — неодушевлённый, ma — одушевлённый (Biernik = Dopełniacz)
G = {"kraj": "m", "chleb": "m", "dar": "m", "ukłon": "m", "światłocień": "m", "stół": "m",
     "bocian": "ma", "Pan": "ma", "Chrystus": "ma", "brat": "ma", "pan": "ma",
     "ziemia": "f", "kruszyna": "f", "wina": "f", "grusza": "f", "rzecz": "f", "przyjaźń": "f", "tęsknota": "f",
     "niebo": "n", "gniazdo": "n", "uszanowanie": "n", "wyznanie": "n", "mieszkanie": "n", "myślenie": "n"}
MEN = {"Pan", "Chrystus", "brat", "pan"}


def N(w, c, pl=False):
    n = NOUN[w]
    return n["pln"][0 if c == "voc" else CI[c]] if pl else n["sg"][CI[c]]


END = {
    "hard": {"m": dict(nom="y", gen="ego", dat="emu", acc="y", acca="ego", instr="ym", loc="ym"),
             "f": dict(nom="a", gen="ej", dat="ej", acc="ą", instr="ą", loc="ej"),
             "n": dict(nom="e", gen="ego", dat="emu", acc="e", instr="ym", loc="ym"),
             "op": dict(nom="e", gen="ych", dat="ym", acc="e", instr="ymi", loc="ych"),
             "mp": dict(gen="ych", dat="ym", acc="ych", instr="ymi", loc="ych")},
    "soft": {"m": dict(nom="i", gen="iego", dat="iemu", acc="i", acca="iego", instr="im", loc="im"),
             "f": dict(nom="ia", gen="iej", dat="iej", acc="ią", instr="ią", loc="iej"),
             "n": dict(nom="ie", gen="iego", dat="iemu", acc="ie", instr="im", loc="im"),
             "op": dict(nom="ie", gen="ich", dat="im", acc="ie", instr="imi", loc="ich"),
             "mp": dict(gen="ich", dat="im", acc="ich", instr="imi", loc="ich")},
}
IRR = {
    "ten": {"m": dict(nom="ten", gen="tego", dat="temu", acc="ten", instr="tym", loc="tym"),
            "ma": dict(nom="ten", gen="tego", dat="temu", acc="tego", instr="tym", loc="tym"),
            "f": dict(nom="ta", gen="tej", dat="tej", acc="tę", instr="tą", loc="tej"),
            "n": dict(nom="to", gen="tego", dat="temu", acc="to", instr="tym", loc="tym"),
            "op": dict(nom="te", gen="tych", dat="tym", acc="te", instr="tymi", loc="tych"),
            "mp": dict(nom="ci", gen="tych", dat="tym", acc="tych", instr="tymi", loc="tych")},
    "mój": {"m": dict(nom="mój", gen="mojego", dat="mojemu", acc="mój", instr="moim", loc="moim"),
            "ma": dict(nom="mój", gen="mojego", dat="mojemu", acc="mojego", instr="moim", loc="moim"),
            "f": dict(nom="moja", gen="mojej", dat="mojej", acc="moją", instr="moją", loc="mojej"),
            "n": dict(nom="moje", gen="mojego", dat="mojemu", acc="moje", instr="moim", loc="moim"),
            "op": dict(nom="moje", gen="moich", dat="moim", acc="moje", instr="moimi", loc="moich"),
            "mp": dict(nom="moi", gen="moich", dat="moim", acc="moich", instr="moimi", loc="moich")},
}


def A(w, g, c):
    """Форма прилагательного: g = m, ma, f, n, mp (мужчины мн.), op (прочие мн.)."""
    if w in IRR:
        return IRR[w][g][c]
    a = ADJ[w]
    if g == "mp" and c == "nom":
        return a["mos"]
    gg, cc = ("m", "acca" if c == "acc" else c) if g == "ma" else (g, c)
    return w[:-1] + END[a["type"]][gg][cc]


def gnum(noun, pl):
    return ("mp" if noun in MEN else "op") if pl else G[noun]


def NP(adj, noun, c, pl=False):
    """прилагательное + существительное в нужном падеже: NP('duży','wina','instr') → dużą winą"""
    return A(adj, gnum(noun, pl), c) + " " + N(noun, c, pl)


def lemma(adj, noun, pl=False):
    return NP(adj, noun, "nom", pl)


def B(ans, hint=""):
    return "{{c1::%s::%s}}" % (ans, hint) if hint else "{{c1::%s}}" % ans


CARDS = []


def card(L, it):
    it["lesson"] = L
    CARDS.append(it)


def cl(L, text, tr, note="", topics=(), level=2):
    card(L, {"type": "cloze", "level": level, "text": text, "tr": tr, "note": note, "topics": list(topics)})


def ch(L, q, options, answer, note="", tr="", topics=(), level=1):
    assert answer in options and len(set(options)) == len(options), q
    card(L, {"type": "choice", "level": level, "q": q, "tr": tr, "options": options, "answer": answer,
             "note": note, "topics": list(topics)})


def tb(L, q, rows, tr="", note="", topics=(), level=3):
    card(L, {"type": "table", "level": level, "q": q, "tr": tr, "rows": rows, "note": note, "topics": list(topics)})


def meanings(L, words, topics=("lex",)):
    """words: [(слово, перевод, где в стихе)] → «что значит?» с вариантами из того же урока"""
    ms = [w[1] for w in words]
    k = len(words)
    steps = [s for s in (1, 3, 5, 7, 2, 4) if s % k][:3] if k > 3 else [1, 2][:k - 1]
    for i, (w, m, ctx) in enumerate(words):
        opts = [m] + [ms[(i + s) % k] for s in steps]
        opts = list(dict.fromkeys(opts))
        ch(L, "<b>%s</b><br>Что значит это слово?" % w, opts, m, note=ctx, topics=topics)


def decl_rows(noun, pl=False, adj=None, voc=True):
    ks = ["nom", "gen", "dat", "acc", "instr", "loc"] + (["voc"] if voc and not pl else [])
    rows = []
    for k in ks:
        f = NP(adj, noun, k, pl) if adj else N(noun, k, pl)
        rows.append([k, f, 1] if k == "nom" else [k, f])
    return rows


def conj_rows(forms, persons=("ja", "ty", "on, ona", "my", "wy", "oni, one")):
    return [[p, f] for p, f in zip(persons, forms)]


VERB = {v["inf"]: v for v in LEX["verbs"]}

# ---------------------------------------------------------------- уроки
LESSONS = []


def lesson(n, title, ref, intro):
    LESSONS.append({"n": n, "title": title, "ref": ref, "intro": intro.strip()})


# 1 ---------------------------------------------------------------
lesson(1, "Слова стиха: существительные", "ref-read", """
<p>Сначала слова: без них не прочитать ни одной строки. Здесь все существительные из «Moja piosnka [II]». Стих целиком с переводом — во вкладке «Уроки».</p>
<p><b>Как читать.</b> Ударение почти всегда на предпоследнем слоге: kru-SZY-na, usza-no-WA-nie. <b>sz</b> = ш, <b>cz</b> = ч, <b>rz</b> и <b>ż</b> = ж, <b>ł</b> — как английское w, <b>ó</b> = у, <b>ą</b> и <b>ę</b> — носовые «он» и «эн».</p>
<p>В карточке польское слово, выбери перевод. Под ответом — строчка стиха, где слово встречается.</p>
""")
NOUNS_POEM = [
    ("kraj", "страна", "«Do kraju tego» — в ту страну"),
    ("chleb", "хлеб", "«kruszynę chleba» — крошку хлеба"),
    ("kruszyna", "крошка", "«gdzie kruszynę chleba» — где крошку хлеба"),
    ("ziemia", "земля", "«Podnoszą z ziemi» — поднимают с земли"),
    ("uszanowanie", "уважение", "«przez uszanowanie» — из уважения"),
    ("dar", "дар", "«Dla darów nieba» — к дарам неба"),
    ("niebo", "небо", "«darów nieba» — даров неба"),
    ("Pan", "Господь; господин", "«Tęskno mi, Panie» — тоскую, Господи"),
    ("wina", "вина", "«gdzie winą jest dużą» — где большой виной считается"),
    ("gniazdo", "гнездо", "«Popsować gniazdo» — разорить гнездо"),
    ("grusza", "груша (дерево)", "«na gruszy» — на груше"),
    ("bocian", "аист", "«gniazdo bocianie» — аистиное гнездо"),
    ("ukłon", "поклон", "«pierwsze ukłony» — первые поклоны"),
    ("wyznanie", "исповедание, признание", "«Chrystusa wyznanie» — исповедание Христа"),
    ("rzecz", "вещь", "«do rzeczy innej» — по другой вещи"),
    ("mieszkanie", "жилище, квартира", "«gdzie leży mieszkanie» — где находится жилище"),
    ("tęsknota", "тоска", "у Норвида «beztęsknota» — жизнь без тоски"),
    ("myślenie", "мышление, раздумье", "у Норвида «bezmyślenie» — жизнь без раздумий"),
    ("światłocień", "светотень", "«Bez światłocienia» — без светотени"),
    ("przyjaźń", "дружба", "«Przyjaźni mojéj» — моей дружбе"),
]
meanings(1, NOUNS_POEM)

# 2 ---------------------------------------------------------------
lesson(2, "Род существительных; ten, ta, to", "ref-nouns", """
<p>Как в русском, три рода, и обычно его видно по окончанию:</p>
<ul><li><b>мужской</b> — на согласный: kraj, chleb, dar, ukłon, bocian, Pan;</li>
<li><b>женский</b> — на -a: ziemia, kruszyna, wina, grusza, tęsknota; и некоторые на мягкий согласный: rzecz, przyjaźń — их запоминаем;</li>
<li><b>средний</b> — на -o и -e: niebo, gniazdo, uszanowanie, wyznanie, mieszkanie.</li></ul>
<p>Род не всегда как в русском: <b>kraj</b> мужского рода, а «страна» — женского; <b>światłocień</b> мужского, а «светотень» — женского.</p>
<p>«Этот» тоже по родам: <b>ten</b> kraj, <b>ta</b> ziemia, <b>to</b> niebo. У Норвида: «Do kraju <b>tego</b>» — это тот же ten, только в другом падеже (урок 11).</p>
""")
GNOTE = {
    "kraj": "На согласный → мужской. По-русски «страна» — женский: роды не совпадают.",
    "rzecz": "На согласный, но женский — как и русское «вещь». Такие слова запоминаем.",
    "przyjaźń": "На мягкий согласный, женский — как русское «дружба», хотя окончание другое.",
    "światłocień": "На согласный → мужской. По-русски «светотень» — женский.",
}
GNAME = {"m": "мужской", "ma": "мужской", "f": "женский", "n": "средний"}
for w, m, _ in NOUNS_POEM:
    g = GNAME[G[w]]
    end = {"мужской": "на согласный → мужской", "женский": "на -a → женский", "средний": "на -o / -e → средний"}[g]
    ch(2, "<b>%s</b> (%s)<br>Какого рода?" % (w, m), ["мужской", "женский", "средний"], g,
       note=GNOTE.get(w, end[0].upper() + end[1:] + "."), topics=["lex"])
for noun, ru in [("kraj", "эта страна"), ("dar", "этот дар"), ("światłocień", "эта светотень"), ("ziemia", "эта земля"),
                 ("rzecz", "эта вещь"), ("przyjaźń", "эта дружба"), ("niebo", "это небо"), ("mieszkanie", "это жилище")]:
    t = A("ten", G[noun], "nom")
    cl(2, B(t, "этот / эта / это") + " " + noun, ru,
       "%s — %s род → %s." % (noun, GNAME[G[noun]], t), ["adj"])

# 3 ---------------------------------------------------------------
lesson(3, "Прилагательные: согласование", "ref-adj", """
<p>Прилагательное меняет окончание по роду существительного, как в русском:</p>
<ul><li>мужской: duż<b>y</b> kraj, pierwsz<b>y</b> ukłon;</li>
<li>женский: duż<b>a</b> wina, inn<b>a</b> rzecz;</li>
<li>средний: duż<b>e</b> gniazdo, odwieczn<b>e</b> wyznanie.</li></ul>
<p>Мягкие прилагательные вместо -y пишут -i: bocian<b>i</b>, bocian<b>ia</b>, bocian<b>ie</b>. «Мой» — <b>mój, moja, moje</b>.</p>
<p>В стихах прилагательное часто стоит после существительного: «gniazdo bocianie» = bocianie gniazdo, «rzeczy innej» = innej rzeczy.</p>
""")
meanings(3, [
    ("duży", "большой", "«winą jest dużą» — большой виной"),
    ("pierwszy", "первый", "«pierwsze ukłony» — первые поклоны"),
    ("odwieczny", "извечный, вековой", "«odwieczne Chrystusa wyznanie» — извечное исповедание Христа"),
    ("inny", "другой", "«do rzeczy innej» — по другой вещи"),
    ("niewinny", "невинный", "«Równie niewinnej» — столь же невинной"),
    ("bociani", "аистиный", "«gniazdo bocianie» — аистиное гнездо"),
    ("mój", "мой", "«Przyjaźni mojéj» — моей дружбе"),
], topics=("lex", "adj"))
for adj, noun, ru in [("duży", "wina", "большая вина"), ("duży", "gniazdo", "большое гнездо"),
                      ("pierwszy", "rzecz", "первая вещь"), ("pierwszy", "wyznanie", "первое признание"),
                      ("odwieczny", "ziemia", "извечная земля"), ("odwieczny", "niebo", "извечное небо"),
                      ("inny", "rzecz", "другая вещь"), ("inny", "mieszkanie", "другое жилище"),
                      ("niewinny", "przyjaźń", "невинная дружба"), ("bociani", "gniazdo", "аистиное гнездо"),
                      ("mój", "przyjaźń", "моя дружба"), ("mój", "mieszkanie", "моё жилище")]:
    f = A(adj, G[noun], "nom")
    cl(3, B(f, adj) + " " + noun, ru, "%s — %s род → %s." % (noun, GNAME[G[noun]], f), ["adj"])
ch(3, "___ światłocień<br>Какая форма?", ["inny", "inna", "inne"], "inny",
   "światłocień — мужской род (хотя «светотень» — женский), поэтому inny.", "другая светотень", ["adj"])
ch(3, "___ rzecz<br>Какая форма?", ["niewinna", "niewinny", "niewinne"], "niewinna",
   "rzecz — женский род, поэтому niewinna.", "невинная вещь", ["adj"])

# 4 ---------------------------------------------------------------
lesson(4, "Глагол być, местоимения, служебные слова", "ref-pres", """
<p><b>Личные местоимения:</b> ja (я), ty (ты), on (он), ona (она), ono (оно), my (мы), wy (вы), <b>oni</b> (они — если есть хоть один мужчина), <b>one</b> (они — все остальные).</p>
<p><b>być</b> — быть: jestem, jesteś, jest, jesteśmy, jesteście, są. Местоимение обычно опускают: <i>Jestem</i> = я (есть).</p>
<p>В отличие от русского, связку не пропускают: <i>Kraj <b>jest</b> duży</i> — страна большая. У Норвида: «pierwsze ukłony <b>są</b> jak…» — первые поклоны (суть) как…</p>
<p>И короткие слова стиха: gdzie, jak, bo, i, tak, nie, jeszcze, już.</p>
""")
tb(4, "Проспрягай в настоящем времени: <b>być</b>", conj_rows(VERB["być"]["pres"]), "быть",
   "Местоимение обычно опускают: jestem = я (есть).", ["pres"])
for before, ans, after, ru in [("(ja) ", "jestem", " tu.", "Я здесь."), ("(ty) ", "jesteś", " tu.", "Ты здесь."),
                               ("Kraj ", "jest", " duży.", "Страна большая."), ("(my) ", "jesteśmy", " tu.", "Мы здесь."),
                               ("(wy) ", "jesteście", " tu.", "Вы здесь.")]:
    cl(4, before + B(ans, "być") + after, ru, "być: jestem, jesteś, jest, jesteśmy, jesteście, są.", ["pres"])
ch(4, "«они» — о группе женщин или о вещах<br>По-польски?", ["one", "oni", "ona", "ono"], "one",
   "one — для всех, кроме групп с мужчинами. oni — если есть хоть один мужчина.", topics=["pron", "mos"])
ch(4, "«они» — о мужчинах (или мужчинах и женщинах)<br>По-польски?", ["oni", "one", "ono", "on"], "oni",
   "oni — мужско-личная форма: хватит одного мужчины в группе.", topics=["pron", "mos"])
meanings(4, [
    ("gdzie", "где", "«Do kraju tego, gdzie…» — в ту страну, где…"),
    ("jak", "как", "«Są jak odwieczne… wyznanie» — как извечное исповедание"),
    ("bo", "потому что", "«Bo wszystkim służą» — потому что всем служат"),
    ("i", "и", "«i do bezmyślenia» — и по бездумью"),
    ("tak", "так; да", "«tak za tak» — «да» за «да»"),
    ("nie", "не; нет", "«nie wiem» — не знаю; «nie za nie» — «нет» за «нет»"),
    ("jeszcze", "ещё", "«Tęskno mi jeszcze» — тоскую ещё"),
    ("już", "уже", "«już nie wiem» — уже не знаю"),
])

# 5 ---------------------------------------------------------------
lesson(5, "Настоящее время: -am, -asz", "ref-pres", """
<p>У глагола шесть форм, и окончание само говорит, кто действует. Первый тип — на <b>-am, -asz</b>:</p>
<p>mieć (иметь): <b>mam, masz, ma, mamy, macie, mają</b>.</p>
<p>Так же: mieszkać (жить — от этого глагола слово mieszkanie), kochać (любить).</p>
<p>У Норвида: «Do tych, co <b>mają</b> tak za tak» — к тем, кто считает «да» за «да». <i>Mieć coś za coś</i> — считать что-то чем-то.</p>
""")
meanings(5, [("mieć", "иметь", "«co mają tak za tak» — кто считает «да» за «да»"),
             ("mieszkać", "жить (проживать)", "от него — mieszkanie, жилище"),
             ("kochać", "любить", "kocham — я люблю")], topics=("lex",))
tb(5, "Проспрягай в настоящем времени: <b>mieć</b>", conj_rows(VERB["mieć"]["pres"]), "иметь",
   "Тип -am, -asz: окончания -m, -sz, -, -my, -cie, -ją.", ["pres"])
for b, ans, a, inf, ru in [
    ("(ja) ", "mam", " chleb.", "mieć", "У меня есть хлеб."), ("(ty) ", "masz", " dar.", "mieć", "У тебя есть дар."),
    ("(on) ", "ma", " gniazdo.", "mieć", "У него есть гнездо."), ("(my) ", "mamy", " mieszkanie.", "mieć", "У нас есть квартира."),
    ("(wy) ", "macie", " chleb.", "mieć", "У вас есть хлеб."),
    ("(ja) ", "mieszkam", " tu.", "mieszkać", "Я живу здесь."), ("(ona) ", "mieszka", " tu.", "mieszkać", "Она живёт здесь."),
    ("(oni) ", "mieszkają", " tu.", "mieszkać", "Они живут здесь."),
    ("(ja) ", "kocham", " ten kraj.", "kochać", "Я люблю эту страну."), ("(my) ", "kochamy", " ten kraj.", "kochać", "Мы любим эту страну."),
    ("(wy) ", "kochacie", " niebo.", "kochać", "Вы любите небо.")]:
    cl(5, b + B(ans, inf) + a, ru, "%s: %s." % (inf, ", ".join(VERB[inf]["pres"])), ["pres"])

# 6 ---------------------------------------------------------------
lesson(6, "Настоящее время: -ę, -isz", "ref-pres", """
<p>Второй тип — на <b>-ę, -isz</b>: podnosić (поднимать): <b>podnoszę, podnosisz, podnosi, podnosimy, podnosicie, podnoszą</b>.</p>
<ul><li>После cz, sz, ż, rz вместо i пишется y: służ<b>y</b>sz, leż<b>y</b>sz.</li>
<li>В формах ja и oni часто чередование: podno<b>sz</b>ę, podno<b>sz</b>ą (s → sz), mu<b>sz</b>ę, mu<b>sz</b>ą.</li>
<li>stać (стоять) — особый: stoję, stoisz, stoi, stoimy, stoicie, stoją.</li></ul>
<p>Из стиха: «<b>Podnoszą</b> z ziemi», «wszystkim <b>służą</b>», «gdzie <b>leży</b> mieszkanie», «któż o mnie <b>stoi</b>», «tak być <b>musi</b>».</p>
""")
meanings(6, [("podnosić", "поднимать", "«Podnoszą z ziemi» — поднимают с земли"),
             ("służyć", "служить", "«Bo wszystkim służą» — потому что всем служат"),
             ("tęsknić", "тосковать", "«Tęskno mi» — тоскливо мне, от того же корня"),
             ("leżeć", "лежать; находиться", "«gdzie leży mieszkanie» — где находится жилище"),
             ("musieć", "быть должным", "«tak być musi» — так быть должно"),
             ("stać", "стоять", "«któż o mnie stoi» — старинное: кто обо мне печётся"),
             ("chwalić", "хвалить", "от него — «pochwalony»: восхвалённый, благословенный")], topics=("lex",))
for b, ans, a, inf, ru in [
    ("(ja) ", "podnoszę", " chleb.", "podnosić", "Я поднимаю хлеб."), ("(ty) ", "podnosisz", " chleb.", "podnosić", "Ты поднимаешь хлеб."),
    ("(ja) ", "służę", ".", "służyć", "Я служу."), ("(my) ", "służymy", ".", "służyć", "Мы служим."),
    ("(ja) ", "tęsknię", ".", "tęsknić", "Я тоскую."), ("(oni) ", "tęsknią", ".", "tęsknić", "Они тоскуют."),
    ("Chleb ", "leży", " tu.", "leżeć", "Хлеб лежит здесь."), ("(ty) ", "leżysz", " tu.", "leżeć", "Ты лежишь здесь."),
    ("(ja) ", "muszę", " tęsknić.", "musieć", "Я должен тосковать."), ("(ona) ", "musi", " tęsknić.", "musieć", "Она должна тосковать."),
    ("(ja) ", "stoję", " tu.", "stać", "Я стою здесь."), ("(on) ", "stoi", " tu.", "stać", "Он стоит здесь."),
    ("(ja) ", "chwalę", " ten kraj.", "chwalić", "Я хвалю эту страну."), ("(wy) ", "chwalicie", " ten kraj.", "chwalić", "Вы хвалите эту страну.")]:
    cl(6, b + B(ans, inf) + a, ru, "%s: %s." % (inf, ", ".join(VERB[inf]["pres"])), ["pres"])
tb(6, "Проспрягай в настоящем времени: <b>stać</b>", conj_rows(VERB["stać"]["pres"]), "стоять",
   "Основа меняется: stać → stoję, stoisz…", ["pres"])

# 7 ---------------------------------------------------------------
lesson(7, "Настоящее время: -ę, -esz и -em; отрицание", "ref-pres", """
<p>Третий тип — на <b>-ę, -esz</b>: psuć (портить): <b>psuję, psujesz, psuje, psujemy, psujecie, psują</b>.</p>
<p>И особые на <b>-em</b>: wiedzieć (знать): <b>wiem, wiesz, wie, wiemy, wiecie, wiedzą</b> — у oni своя форма.</p>
<p><b>Отрицание</b> — nie перед глаголом, как в русском: <i>nie wiem</i> — не знаю, <i>nie mam</i> — не имею. У Норвида: «już <b>nie wiem</b>, gdzie leży mieszkanie».</p>
""")
meanings(7, [("psuć", "портить", "сов. вид popsuć; у Норвида старое «popsować» — разорить (гнездо)"),
             ("wiedzieć", "знать", "«już nie wiem» — уже не знаю")], topics=("lex",))
for b, ans, a, inf, ru in [
    ("(ja) ", "psuję", " gniazdo.", "psuć", "Я порчу гнездо."), ("(ty) ", "psujesz", " gniazdo.", "psuć", "Ты портишь гнездо."),
    ("(oni) ", "psują", " gniazdo.", "psuć", "Они портят гнездо."),
    ("(ty) ", "wiesz", ".", "wiedzieć", "Ты знаешь."), ("(my) ", "wiemy", ".", "wiedzieć", "Мы знаем."),
    ("(oni) ", "wiedzą", ".", "wiedzieć", "Они знают.")]:
    cl(7, b + B(ans, inf) + a, ru, "%s: %s." % (inf, ", ".join(VERB[inf]["pres"])), ["pres"])
tb(7, "Проспрягай в настоящем времени: <b>wiedzieć</b>", conj_rows(VERB["wiedzieć"]["pres"]), "знать",
   "Особый глагол: wiem, wiesz… но oni wiedzą.", ["pres"])
tb(7, "Проспрягай в настоящем времени: <b>psuć</b>", conj_rows(VERB["psuć"]["pres"]), "портить",
   "Тип -ę, -esz: psuję, psujesz…", ["pres"])
ch(7, "«Я не знаю»<br>Как по-польски?", ["Nie wiem", "Wiem nie", "Nie wiedzę"], "Nie wiem",
   "nie ставится перед глаголом: nie wiem. Форма «я знаю» — wiem.", topics=["pres"])

# 8 ---------------------------------------------------------------
lesson(8, "Падежи. Biernik: женский и средний род", "ref-acc", """
<p>В польском семь падежей: шесть русских и звательный. Начнём с <b>Biernik</b> (винительный): кого? что? — прямое дополнение.</p>
<ul><li>женский род на -a → <b>-ę</b>: kruszyna → kruszyn<b>ę</b>, ziemia → ziemi<b>ę</b>;</li>
<li>женский на согласный не меняется: rzecz, przyjaźń;</li>
<li>средний род не меняется: gniazdo, uszanowanie.</li></ul>
<p>ta → <b>tę</b>, прилагательное ж.р. → <b>-ą</b>: Widzę tę dużą gruszę. Предлог <b>przez</b> всегда с Biernik: «przez uszanowanie».</p>
<p>Новый глагол: widzieć — видеть (widzę, widzisz…). У Норвида: «gdzie <b>kruszynę</b> chleba podnoszą», «Popsować <b>gniazdo</b>».</p>
""")
for b, noun, a, ru in [("Podnoszę ", "kruszyna", ".", "Я поднимаю крошку."), ("Kocham ", "ziemia", ".", "Я люблю землю."),
                       ("Widzę ", "grusza", ".", "Я вижу грушу."), ("Chwalę ", "przyjaźń", ".", "Я хвалю дружбу."),
                       ("Kocham ", "tęsknota", ".", "Я люблю тоску."), ("Mam ", "rzecz", ".", "У меня есть вещь.")]:
    f = N(noun, "acc")
    cl(8, b + B(f, noun) + a, ru,
       ("Ж.р. на -a → -ę: %s → %s." % (noun, f)) if f != noun else ("Ж.р. на согласный не меняется: %s." % f), ["acc"])
for b, adj, noun, a, ru in [("Widzę ", "ten", "rzecz", ".", "Я вижу эту вещь."), ("Widzę ", "duży", "grusza", ".", "Я вижу большую грушу."),
                            ("Chwalę ", "mój", "ziemia", ".", "Я хвалю мою землю."), ("Widzę ", "inny", "rzecz", ".", "Я вижу другую вещь.")]:
    cl(8, b + B(NP(adj, noun, "acc"), lemma(adj, noun)) + a, ru,
       "Ж.р. в Biernik: ta → tę, прилагательное -a → -ą.", ["acc", "adj"])
ch(8, "Mam ___ (mieszkanie)<br>Какая форма?", ["mieszkanie", "mieszkanię", "mieszkania"], "mieszkanie",
   "Средний род: Biernik = Mianownik.", "У меня есть квартира.", ["acc"])
ch(8, "Podnoszą kruszynę.<br>Почему kruszyn<b>ę</b>?", ["Biernik: что поднимают?", "Dopełniacz: чего?", "Mianownik: кто?"],
   "Biernik: что поднимают?", "Прямое дополнение → Biernik, ж.р. -a → -ę.", "Поднимают крошку.", ["acc"])

# 9 ---------------------------------------------------------------
lesson(9, "Biernik: мужской род", "ref-acc", """
<p>Мужской род в Biernik зависит от одушевлённости — как в русском:</p>
<ul><li><b>неодушевлённые</b> не меняются: Kocham ten kraj, Mam chleb, Mam dar;</li>
<li><b>одушевлённые</b> (люди и животные) получают <b>-a</b>, как в Dopełniacz: Chwalę Pan<b>a</b>, Widzę bocian<b>a</b>, Wyznaję Chrystus<b>a</b>.</li></ul>
<p>Прилагательное у одушевлённых тоже как в Dopełniacz: Widzę <b>tego</b> bociana, Kocham <b>mojego</b> brata.</p>
<p>Новые глаголы: wyznawać — исповедовать (wyznaję, от него wyznanie), widzieć — видеть.</p>
""")
for b, noun, a, ru in [("Chwalę ", "Pan", ".", "Я хвалю Господа."), ("Widzę ", "bocian", ".", "Я вижу аиста."),
                       ("Wyznaję ", "Chrystus", ".", "Я исповедую Христа."), ("Kocham ", "brat", ".", "Я люблю брата.")]:
    cl(9, b + B(N(noun, "acc"), noun) + a, ru, "Одушевлённый м.р. → -a: %s → %s." % (noun, N(noun, "acc")), ["acc"])
for b, adj, noun, a, ru in [("Widzę ", "ten", "bocian", ".", "Я вижу этого аиста."),
                            ("Kocham ", "mój", "brat", ".", "Я люблю моего брата.")]:
    cl(9, b + B(NP(adj, noun, "acc"), lemma(adj, noun)) + a, ru, "Одушевлённый: прилагательное тоже -ego.", ["acc", "adj"])
ch(9, "Kocham ___ (ten kraj)<br>Какая форма?", ["ten kraj", "tego kraju", "tego kraja"], "ten kraj",
   "kraj неодушевлённый → Biernik = Mianownik.", "Я люблю эту страну.", ["acc"])
ch(9, "Mam ___ (chleb)<br>Какая форма?", ["chleb", "chleba", "chlebem"], "chleb",
   "Неодушевлённый → не меняется. (chleba — это «нет хлеба», урок 10.)", "У меня есть хлеб.", ["acc"])
ch(9, "Widzę ___ (bocian)<br>Какая форма?", ["bociana", "bocian", "bocianu"], "bociana",
   "Аист — одушевлённый → -a, как «вижу аиста».", "Я вижу аиста.", ["acc"])
ch(9, "Mam ___ (dar)<br>Какая форма?", ["dar", "dara", "daru"], "dar",
   "Неодушевлённый → не меняется.", "У меня есть дар.", ["acc"])

# 10 --------------------------------------------------------------
lesson(10, "Dopełniacz: существительные", "ref-gen", """
<p><b>Dopełniacz</b> (родительный): кого? чего? Нужен:</p>
<ul><li>для части и принадлежности: kruszyna <b>chleba</b>, dar <b>nieba</b>, <b>Chrystusa</b> wyznanie, gniazdo <b>bociana</b>;</li>
<li>при <b>отрицании</b> вместо Biernik: Mam chleb → Nie mam <b>chleba</b>;</li>
<li>после do, z («из, с»), bez, dla, u: do <b>kraju</b>, z <b>ziemi</b>, bez <b>światłocienia</b>.</li></ul>
<p>Окончания: м.р. <b>-a</b> или <b>-u</b> (chleba, Pana / kraju, daru — правила нет, запоминаем); ж.р. <b>-y</b> / <b>-i</b> (kruszyny, winy / ziemi, rzeczy, przyjaźni); ср.р. <b>-a</b> (nieba, gniazda).</p>
<p>Норвид сам сложил слова с bez-: <b>beztęsknota</b> (жизнь без тоски), <b>bezmyślenie</b> (без раздумий): «Do beztęsknoty i do bezmyślenia».</p>
""")
for b, noun, a, ru in [("Nie mam ", "mieszkanie", ".", "У меня нет квартиры."), ("Nie ma ", "przyjaźń", ".", "Нет дружбы."),
                       ("Nie widzę ", "bocian", ".", "Я не вижу аиста."), ("Nie ma ", "uszanowanie", ".", "Нет уважения."),
                       ("Idę do ", "mieszkanie", ".", "Я иду в квартиру."), ("Jestem bez ", "wina", ".", "Я без вины."),
                       ("To dar dla ", "Pan", ".", "Это дар для Господа."), ("Wracam z ", "kraj", ".", "Я возвращаюсь из страны."),
                       ("To gniazdo ", "bocian", ".", "Это гнездо аиста."), ("Tęsknię do ", "ziemia", ".", "Я тоскую по земле.")]:
    cl(10, b + B(N(noun, "gen"), noun) + a, ru, "Dopełniacz: %s → %s." % (noun, N(noun, "gen")), ["gen"])
for noun, right, wrong in [("kraj", "kraju", "kraja"), ("ukłon", "ukłonu", "ukłona"), ("dar", "daru", "dara"), ("chleb", "chleba", "chlebu")]:
    ch(10, "Dopełniacz от <b>%s</b>?" % noun, [right, wrong], right,
       "У мужского рода в Dopełniacz -a или -u, правила нет — запоминаем: %s → %s." % (noun, right), topics=["gen"])

# 11 --------------------------------------------------------------
lesson(11, "Dopełniacz: прилагательные и ten", "ref-adj", """
<p>Прилагательные и ten в Dopełniacz:</p>
<ul><li>мужской и средний род — <b>-ego</b>: tego, innego, pierwszego, mojego;</li>
<li>женский — <b>-ej</b>: tej, innej, niewinnej, mojej.</li></ul>
<p>У Норвида прилагательное часто после существительного: «Do kraju <b>tego</b>» = do tego kraju; «Tęskno mi… do rzeczy <b>innej</b>… równie <b>niewinnej</b>» = по другой, столь же невинной вещи.</p>
""")
for b, adj, noun, a, ru in [("Idę do ", "ten", "ziemia", ".", "Я иду к этой земле."),
                            ("Nie mam ", "inny", "mieszkanie", ".", "У меня нет другой квартиры."),
                            ("Jestem bez ", "duży", "wina", ".", "Я без большой вины."),
                            ("Wracam z ", "ten", "kraj", ".", "Я возвращаюсь из этой страны."),
                            ("To dar dla ", "mój", "przyjaźń", ".", "Это дар для моей дружбы."),
                            ("Nie widzę ", "ten", "gniazdo", ".", "Я не вижу этого гнезда.")]:
    cl(11, b + B(NP(adj, noun, "gen"), lemma(adj, noun)) + a, ru,
       "Dopełniacz: м.р. и ср.р. -ego, ж.р. -ej.", ["gen", "adj"])
ch(11, "do rzeczy <b>innej</b><br>Почему innej?", ["прилагательное ж.р. в Dopełniacz", "прилагательное ж.р. в Mianownik", "наречие"],
   "прилагательное ж.р. в Dopełniacz", "rzecz — ж.р.; do + Dopełniacz → rzeczy innej.", "по другой вещи", ["gen", "adj"])

# 12 --------------------------------------------------------------
lesson(12, "Narzędnik", "ref-instr", """
<p><b>Narzędnik</b> (творительный): кем? чем? Нужен:</p>
<ul><li>после <b>być + существительное</b>: Chleb jest <b>darem</b> nieba; у Норвида «gdzie <b>winą</b> jest <b>dużą</b>» — где большой виной является…;</li>
<li>после z в значении «вместе с»: z Panem;</li>
<li>после tęsknić za (тосковать по): tęsknię za ziemią;</li>
<li>после pod, nad, przed, za, między на вопрос «где?»: pod gruszą.</li></ul>
<p>Окончания: м.р. и ср.р. <b>-em</b> (darem, niebem, mieszkaniem), ж.р. <b>-ą</b> (ziemią, winą, przyjaźnią); прилагательные -ym / -ą.</p>
""")
for b, noun, a, ru in [("Chleb jest ", "dar", " nieba.", "Хлеб — дар неба."), ("Ukłon jest ", "wyznanie", ".", "Поклон — это признание."),
                       ("Tęsknię za ", "ziemia", ".", "Я тоскую по земле."), ("Tęsknię za ", "przyjaźń", ".", "Я тоскую по дружбе."),
                       ("Bocian siedzi pod ", "grusza", ".", "Аист сидит под грушей."), ("Interesuję się ", "światłocień", ".", "Я интересуюсь светотенью."),
                       ("Rozmawiam z ", "brat", ".", "Я разговариваю с братом.")]:
    cl(12, b + B(N(noun, "instr"), noun) + a, ru, "Narzędnik: %s → %s." % (noun, N(noun, "instr")), ["instr"])
cl(12, "Przyjaźń jest " + B(NP("niewinny", "rzecz", "instr"), lemma("niewinny", "rzecz")) + ".", "Дружба — невинная вещь.",
   "być + существительное → Narzędnik, и прилагательное с ним: niewinną rzeczą.", ["instr", "adj"])

# 13 --------------------------------------------------------------
lesson(13, "Miejscownik и чередования", "ref-loc", """
<p><b>Miejscownik</b> (предложный) бывает только с предлогами <b>w, na, o, przy, po</b>: na gruszy, o niebie, w kraju.</p>
<p>Окончание <b>-e</b> смягчает основу: dar → dar<b>ze</b>, niebo → nieb<b>ie</b>, gniazdo → gnieźdz<b>ie</b>, kruszyna → kruszyn<b>ie</b>, tęsknota → tęskno<b>cie</b>, Chrystus → Chrystus<b>ie</b>.</p>
<p>Окончание <b>-u</b>: после k, g, ch и мягких, и у некоторых слов: kraj → kraju, Pan → Panu, mieszkanie → mieszkaniu. Женский на мягкий — <b>-i</b>: ziemi, gruszy, rzeczy, przyjaźni.</p>
<p>Где? — na gruszy (Miejscownik). Куда? — na gruszę (Biernik). У Норвида: «na <b>gruszy</b>», «o <b>mnie</b>».</p>
""")
for b, noun, a, ru in [("Myślę o ", "przyjaźń", ".", "Я думаю о дружбе."), ("Mówię o ", "dar", ".", "Я говорю о даре."),
                       ("Myślę o ", "Chrystus", ".", "Я думаю о Христе."), ("Mówię o ", "ukłon", ".", "Я говорю о поклоне."),
                       ("Mieszkam w ", "kraj", ".", "Я живу в стране."), ("Mówię o ", "wina", ".", "Я говорю о вине."),
                       ("W ", "mieszkanie", " jest chleb.", "В квартире есть хлеб."), ("Myślę o ", "tęsknota", ".", "Я думаю о тоске."),
                       ("Kruszyna leży na ", "stół", ".", "Крошка лежит на столе.")]:
    cl(13, b + B(N(noun, "loc"), noun) + a, ru, "Miejscownik: %s → %s." % (noun, N(noun, "loc")), ["loc"])
cl(13, "Myślę o " + B(NP("ten", "rzecz", "loc"), "ta rzecz") + ".", "Я думаю об этой вещи.",
   "Ж.р. в Miejscownik: ta → tej, rzecz → rzeczy.", ["loc", "adj"])

# 14 --------------------------------------------------------------
lesson(14, "Celownik", "ref-dat", """
<p><b>Celownik</b> (дательный): кому? чему? Нужен после służyć (служить кому), dziękować (благодарить кого — по-польски «кому»!), pomagać, и в безличных: <b>tęskno mi</b>, zimno mi.</p>
<p>Окончания: м.р. <b>-owi</b> (krajowi, bocianowi, Chrystusowi; но Panu), ж.р. как в Miejscownik (kruszynie, ziemi, przyjaźni), ср.р. <b>-u</b> (niebu, gniazdu, mieszkaniu).</p>
<p>Местоимения: mi, ci, mu, jej, nam, wam, im. У Норвида: «Tęskno <b>mi</b>», «Bo <b>wszystkim</b> służą», «<b>Przyjaźni mojéj</b>» — моей дружбе (é — старое написание, сейчас mojej).</p>
""")
for b, noun, a, ru in [("Służę ", "kraj", ".", "Я служу стране."), ("Służę ", "Chrystus", ".", "Я служу Христу."),
                       ("Służymy ", "przyjaźń", ".", "Мы служим дружбе."), ("Przyglądam się ", "bocian", ".", "Я присматриваюсь к аисту."),
                       ("Przyglądam się ", "niebo", ".", "Я присматриваюсь к небу.")]:
    cl(14, b + B(N(noun, "dat"), noun) + a, ru, "Celownik: %s → %s." % (noun, N(noun, "dat")), ["dat"])
for p, ans, ru in [("ty", "ci", "Тебе тоскливо."), ("on", "mu", "Ему тоскливо."), ("my", "nam", "Нам тоскливо."), ("ona", "jej", "Ей тоскливо.")]:
    cl(14, "Tęskno " + B(ans, p) + ".", ru, "Celownik местоимений: mi, ci, mu, jej, nam, wam, im.", ["dat", "pron"])

# 15 --------------------------------------------------------------
lesson(15, "Wołacz и всё склонение ед. ч.", "ref-voc", """
<p><b>Wołacz</b> — форма обращения, как русское «Господи»:</p>
<ul><li>м.р. <b>-e</b> / <b>-u</b>: Pan → Pan<b>ie</b>, bocian → bocian<b>ie</b>, kraj → kraj<b>u</b>; особое: Chrystus → <b>Chryste</b>;</li>
<li>ж.р. <b>-o</b>: ziemia → ziemi<b>o</b>, tęsknota → tęsknot<b>o</b>; на мягкий согласный — <b>-i</b>: przyjaźń → przyjaźn<b>i</b>;</li>
<li>ср.р. как Mianownik: niebo!</li></ul>
<p>Ловушка из стиха: «gniazdo <b>bocianie</b>» — это прилагательное (аистиное), а «<b>Bocianie</b>!» — обращение к аисту.</p>
<p>Дальше — таблицы: все падежи ед. ч. разом.</p>
""")
for b, noun, a, ru in [("", "ziemia", ", tęskno mi!", "Земля, тоскливо мне!"), ("", "przyjaźń", " moja!", "Дружба моя!"),
                       ("", "Chrystus", "!", "Христе!"), ("", "bocian", ", gdzie jesteś?", "Аист, где ты?"),
                       ("", "kraj", " mój!", "Страна моя!"), ("", "tęsknota", " moja!", "Тоска моя!")]:
    v = N(noun, "voc")
    cl(15, b + B(v[0].upper() + v[1:], noun) + a, ru, "Wołacz: %s → %s." % (noun, v), ["voc"])
ch(15, "gniazdo <b>bocianie</b><br>Что такое bocianie здесь?", ["прилагательное: аистиное", "Wołacz: «аист!»"],
   "прилагательное: аистиное", "bociani (аистиный) в ср.р. — bocianie, как «gniazdo». Обращение к аисту выглядит так же — смотри по смыслу.",
   "аистиное гнездо", ["adj", "voc"])
tb(15, "Просклоняй: <b>przyjaźń</b>", decl_rows("przyjaźń"), "дружба",
   "Ж.р. на мягкий согласный: почти везде przyjaźni, Narzędnik przyjaźnią.", ["decl"])
tb(15, "Просклоняй: <b>rzecz</b>", decl_rows("rzecz"), "вещь", "Как przyjaźń: rzeczy почти везде, Narzędnik rzeczą.", ["decl"])
tb(15, "Просклоняй: <b>bocian</b>", decl_rows("bocian"), "аист", "Одушевлённый м.р.: Biernik = Dopełniacz (bociana).", ["decl"])
tb(15, "Просклоняй: <b>mieszkanie</b>", decl_rows("mieszkanie"), "жилище", "Ср.р. на -anie: -a, -u, -em, -u.", ["decl"])
tb(15, "Просклоняй: <b>pierwszy ukłon</b>", decl_rows("ukłon", adj="pierwszy", voc=False), "первый поклон",
   "Неодушевлённый м.р.: Biernik = Mianownik.", ["decl", "adj"])

# 16 --------------------------------------------------------------
lesson(16, "Множественное число: Mianownik и Biernik", "ref-mos", """
<p>Мн. ч. в Mianownik: м.р. и ж.р. <b>-y / -i / -e</b> (dary, ukłony, kraje, grusze, rzeczy), ср.р. <b>-a</b> (gniazda, mieszkania).</p>
<p><b>Мужско-личная форма:</b> если речь о мужчинах — oni, wszyscy, pierwsi, panowie. Обо всём остальном (женщины, животные, вещи) — one, wszystkie, <b>pierwsze ukłony</b>, bociany.</p>
<p>Biernik мн. ч. = Mianownik, кроме мужчин: widzę bociany, но widzę panów. У Норвида: «gdzie <b>pierwsze ukłony</b> / <b>Są</b> jak…».</p>
""")
for b, noun, a, ru in [("Na gruszy są ", "gniazdo", ".", "На груше гнёзда."), ("To są ", "dar", " nieba.", "Это дары неба."),
                       ("", "bocian", " są tu.", "Аисты здесь."), ("Widzę ", "bocian", ".", "Я вижу аистов."),
                       ("Widzę ", "pan", ".", "Я вижу господ.")]:
    c = "acc" if b.startswith("Widzę") else "nom"
    f = N(noun, c, True)
    cl(16, b + B(f[0].upper() + f[1:] if not b else f, noun + ", мн. ч.") + a, ru,
       "Мн. ч.: %s → %s." % (noun, f) + (" Мужчины: Biernik = Dopełniacz." if noun in MEN and c == "acc" else ""), ["acc" if c == "acc" else "nom", "mos"])
for adj, noun, b, ru in [("inny", "rzecz", "To są ", "Это другие вещи."), ("duży", "grusza", "To są ", "Это большие груши.")]:
    cl(16, b + B(NP(adj, noun, "nom", True), lemma(adj, noun) + ", мн. ч.") + ".", ru,
       "Не о мужчинах → прилагательное на -e.", ["nom", "adj", "mos"])
ch(16, "pierwsze ukłony<br>Почему pierwsz<b>e</b>, а не pierwsi?", ["поклоны — не люди", "это ед. ч.", "так в стихах"],
   "поклоны — не люди", "pierwsi — только о мужчинах; обо всём остальном — pierwsze.", "первые поклоны", ["adj", "mos"])
ch(16, "Bociany są tu. Аисты — oni или one?", ["one", "oni"], "one", "Животные — не мужско-личная группа: one.", topics=["pron", "mos"])

# 17 --------------------------------------------------------------
lesson(17, "Множественное число: остальные падежи", "ref-nouns", """
<p>Три падежа мн. ч. одинаковы у всех родов: Celownik <b>-om</b>, Narzędnik <b>-ami</b>, Miejscownik <b>-ach</b>: krajom, darami, o ukłonach.</p>
<p>Dopełniacz мн. ч.: м.р. <b>-ów</b> (darów, ukłonów, bocianów), ж.р. и ср.р. часто <b>без окончания</b> (kruszyn, gniazd), мягкие на <b>-i</b> (rzeczy, przyjaźni).</p>
<p>ten во мн. ч.: tych, tym, tymi. У Норвида: «Dla <b>darów</b> nieba», «Do <b>tych</b>, co mają…» — к тем, кто…</p>
""")
for b, noun, c, a, ru in [("Nie ma ", "gniazdo", "gen", ".", "Нет гнёзд."), ("To dla ", "bocian", "gen", ".", "Это для аистов."),
                          ("Myślę o ", "ukłon", "loc", ".", "Я думаю о поклонах."), ("Służę ", "kraj", "dat", ".", "Я служу странам."),
                          ("Interesuję się ", "rzecz", "instr", ".", "Я интересуюсь вещами."), ("Mówię o ", "dar", "loc", ".", "Я говорю о дарах."),
                          ("Nie ma ", "kruszyna", "gen", ".", "Нет крошек."), ("Jestem bez ", "ukłon", "gen", ".", "Я без поклонов.")]:
    cl(17, b + B(N(noun, c, True), noun + ", мн. ч.") + a, ru,
       "Мн. ч., %s: %s." % ({"gen": "Dopełniacz", "dat": "Celownik", "instr": "Narzędnik", "loc": "Miejscownik"}[c], N(noun, c, True)), [c])

# 18 --------------------------------------------------------------
lesson(18, "Прошедшее время", "ref-past", """
<p>Основа — инфинитив без -ć плюс <b>-ł</b>: tęskni-ć → tęsknił, być → był. Дальше окончания по роду и лицу:</p>
<p>ja: tęskniłem / tęskniłam; ty: tęskniłeś / tęskniłaś; on, ona, ono: tęsknił, tęskniła, tęskniło; my: tęskniliśmy / tęskniłyśmy; oni / one: tęsknili / tęskniły.</p>
<p><b>-li</b> — только о мужчинах, обо всём остальном <b>-ły</b>: bociany służyły. У глаголов на -eć e → a: leżeć → leżał, но leżeli.</p>
<p>Безличное — в ср.р.: tęskno mi <b>było</b>.</p>
""")
for b, ans, a, inf, ru in [
    ("Wczoraj (ja, м.р.) ", "tęskniłem", ".", "tęsknić", "Вчера я тосковал."),
    ("Wczoraj (ja, ж.р.) ", "tęskniłam", ".", "tęsknić", "Вчера я тосковала."),
    ("Chleb ", "leżał", " na ziemi.", "leżeć", "Хлеб лежал на земле."),
    ("Gniazdo ", "było", " na gruszy.", "być", "Гнездо было на груше."),
    ("Bociany ", "stały", " na ziemi.", "stać", "Аисты стояли на земле."),
    ("(ona) ", "wiedziała", ".", "wiedzieć", "Она знала."),
    ("(my, мужчины) ", "służyliśmy", " krajowi.", "służyć", "Мы служили стране."),
    ("(ja, м.р.) ", "musiałem", " tęsknić.", "musieć", "Я должен был тосковать."),
    ("(ty, ж.р.) ", "chwaliłaś", " Pana.", "chwalić", "Ты хвалила Господа.")]:
    cl(18, b + B(ans, inf) + a, ru, "Прошедшее время: %s → %s." % (inf, ans), ["past"])

# 19 --------------------------------------------------------------
lesson(19, "Будущее время и вид глагола", "ref-fut", """
<p>Как в русском, глаголы парные: несов. вид — процесс (psuć — портить), сов. вид — результат (popsuć — испортить).</p>
<ul><li>Будущее <b>несов.</b> вида: będę + инфинитив (или форма на -ł): będę tęsknić = będę tęsknił.</li>
<li>Будущее <b>сов.</b> вида — его «настоящие» формы: popsuję (испорчу), pochwalę (похвалю).</li></ul>
<p>У Норвида: «choć się tak nie <b>stanie</b>» — хоть так и не станется: stać się (стать, случиться) — сов. вид, stanie — будущее. И «Popsować gniazdo» — старая форма popsuć.</p>
""")
cl(19, "Jutro (ja) " + B("będę tęsknić / będę tęsknił / będę tęskniła", "tęsknić, буд.") + ".", "Завтра я буду тосковать.",
   "Несов. вид: będę + инфинитив или + форма на -ł.", ["fut"])
cl(19, "Jutro (my) " + B("będziemy", "być") + " w kraju.", "Завтра мы будем в стране.",
   "Будущее от być: będę, będziesz, będzie, będziemy, będziecie, będą.", ["fut"])
cl(19, "Jutro (on) " + B("popsuje", "popsuć") + " gniazdo.", "Завтра он испортит гнездо.",
   "popsuć — сов. вид: popsuję, popsujesz, popsuje… = будущее.", ["fut", "aspect"])
cl(19, "Jutro (ja) " + B("pochwalę", "pochwalić") + " Pana.", "Завтра я похвалю Господа.",
   "pochwalić — сов. вид к chwalić: pochwalę = похвалю.", ["fut", "aspect"])
ch(19, "«Он испортит гнездо»<br>Какая форма?", ["popsuje", "psuje"], "popsuje",
   "Результат в будущем → сов. вид popsuć: popsuje. psuje — «портит» сейчас.", topics=["aspect"])
ch(19, "«Он портит гнездо (сейчас)»<br>Какая форма?", ["psuje", "popsuje"], "psuje",
   "Сейчас, процесс → несов. вид psuć: psuje.", topics=["aspect"])
tb(19, "Будущее время (сов. вид): <b>stać się</b>",
   conj_rows(["stanę się", "staniesz się", "stanie się", "staniemy się", "staniecie się", "staną się"]), "стать, случиться",
   "Сов. вид: «się tak nie stanie» — так не случится.", ["fut", "aspect"])

# 20 --------------------------------------------------------------
lesson(20, "Повелительное наклонение", "ref-imper", """
<p>Берём форму «on» и отбрасываем окончание: on chwali → <b>chwal!</b>, on kocha → <b>kochaj!</b>; для нескольких -cie: chwalcie!, kochajcie!; «давайте» — -my: chwalmy!</p>
<p>Особые: być → <b>bądź</b>, stać → <b>stój</b>. Запрет — с nie, обычно несов. вид: nie psuj!</p>
<p>«Пусть» — <b>niech</b>: «Niech będzie pochwalony Jezus Chrystus» — старое польское приветствие, ответ: «Na wieki wieków. Amen». У Норвида оно звучит как «<b>Bądź</b> pochwalony!» — будь благословен.</p>
""")
for b, ans, a, inf, ru in [("", "Chwal", " Pana!", "chwalić, ty", "Хвали Господа!"),
                           ("", "Kochajcie", " ten kraj!", "kochać, wy", "Любите эту страну!"),
                           ("", "Nie psuj", " gniazda!", "psuć, ty, запрет", "Не порти гнезда!"),
                           ("", "Stój", "!", "stać, ty", "Стой!")]:
    cl(20, b + B(ans, inf) + a, ru, "Повелительное: %s." % ans + (" После запрета — Dopełniacz: gniazda." if "psuj" in ans else ""), ["imper"])
cl(20, "Niech " + B("będzie", "być") + " pochwalony Jezus Chrystus.", "Да будет благословен Иисус Христос.",
   "niech + будущее/настоящее = «пусть». Ответ на приветствие: Na wieki wieków. Amen.", ["imper"])

# 21 --------------------------------------------------------------
lesson(21, "Условное наклонение", "ref-cond", """
<p>Прошедшее время + <b>by</b> + окончание лица: tęsknił + by + m → <b>tęskniłbym</b> (я тосковал бы), tęskniła + by + m → tęskniłabym.</p>
<p>by может уйти к союзу: <b>gdybym</b> wiedział — если бы я знал; вежливо: <b>chciałbym</b> — я хотел бы.</p>
""")
for b, ans, a, inf, ru in [("(ja, м.р.) ", "tęskniłbym", ".", "tęsknić", "Я тосковал бы."),
                           ("(ona) ", "służyłaby", " krajowi.", "służyć", "Она служила бы стране."),
                           ("(my, мужчины) ", "mieszkalibyśmy", " w tym kraju.", "mieszkać", "Мы жили бы в этой стране."),
                           ("(ja, ж.р.) ", "chciałabym", " wiedzieć.", "chcieć", "Я хотела бы знать.")]:
    cl(21, b + B(ans, inf) + a, ru, "Условное: форма на -ł + by + окончание.", ["cond"])
cl(21, "Gdybym " + B("wiedział", "wiedzieć, ja м.р.") + ", gdzie leży mieszkanie…", "Если бы я знал, где находится жилище…",
   "gdyby + m → gdybym, а глагол — в прошедшем: wiedział.", ["cond"])

# 22 --------------------------------------------------------------
lesson(22, "który, kto, co; частица -ż; się", "ref-sie", """
<p><b>który</b> склоняется как прилагательное: który, która, które; którego, której… У Норвида: «do rzeczy innej, / <b>Której</b>, już nie wiem, gdzie leży mieszkanie» — по вещи, чьё жилище, уже не знаю, где.</p>
<p><b>co</b> в книжной речи значит «который, кто»: «Do tych, <b>co</b> mają…» — к тем, кто… <b>któż</b> = kto + <b>-ż</b> («кто же»).</p>
<p><b>się</b> — как русское -ся, отдельным словом: stać się — стать, случиться. Может стоять перед глаголом: «choć <b>się</b> tak nie stanie».</p>
<p>И последние слова стиха: ówdzie, równie, choć.</p>
""")
meanings(22, [("ówdzie", "там, в другом месте", "«Tęskno mi ówdzie» — тоскую там"),
              ("równie", "столь же, так же", "«Równie niewinnej» — столь же невинной"),
              ("choć", "хотя", "«choć się tak nie stanie» — хоть так и не станется"),
              ("któż", "кто же", "«gdzie któż o mnie stoi?» — где кто же обо мне печётся?")])
for b, adj_g, a, ru, note in [("To rzecz, ", ("który", "f", "nom"), " leży tu.", "Это вещь, которая лежит здесь.", "rzecz — ж.р. → która."),
                              ("To gniazdo, ", ("który", "n", "nom"), " jest na gruszy.", "Это гнездо, которое на груше.", "gniazdo — ср.р. → które."),
                              ("To bocian, ", ("który", "ma", "acc"), " widzę.", "Это аист, которого я вижу.", "Biernik одушевлённого → którego.")]:
    cl(22, b + B(A(*adj_g), "który") + a, ru, note, ["pron"])

# ---------------------------------------------------------------- стих
POEM = [
    ["Do kraju tego, gdzie kruszynę chleba", "В ту страну, где крошку хлеба"],
    ["Podnoszą z ziemi przez uszanowanie", "поднимают с земли из уважения"],
    ["Dla darów nieba,", "к дарам неба,"],
    ["Tęskno mi, Panie.", "тоскую я, Господи."],
    ["", ""],
    ["Do kraju tego, gdzie winą jest dużą", "В ту страну, где большой виной считается"],
    ["Popsować gniazdo na gruszy bocianie,", "разорить аистиное гнездо на груше,"],
    ["Bo wszystkim służą,", "потому что они служат всем,"],
    ["Tęskno mi, Panie.", "тоскую я, Господи."],
    ["", ""],
    ["Do kraju tego, gdzie pierwsze ukłony", "В ту страну, где первые поклоны"],
    ["Są jak odwieczne Chrystusa wyznanie:", "как извечное исповедание Христа:"],
    ["«Bądź pochwalony!»", "«Будь благословен!»"],
    ["Tęskno mi, Panie.", "тоскую я, Господи."],
    ["", ""],
    ["Tęskno mi jeszcze i do rzeczy innej,", "Тоскую я ещё и по другой вещи,"],
    ["Której, już nie wiem, gdzie leży mieszkanie,", "чьё жилище — уже не знаю, где,"],
    ["Równie niewinnej...", "столь же невинной…"],
    ["Tęskno mi, Panie.", "тоскую я, Господи."],
    ["", ""],
    ["Do beztęsknoty i do bezmyślenia,", "По жизни без тоски и без раздумий,"],
    ["Do tych, co mają tak za tak, nie za nie —", "по тем, у кого «да» — это «да», а «нет» — это «нет»,"],
    ["Bez światłocienia,", "без светотени,"],
    ["Tęskno mi, Panie.", "тоскую я, Господи."],
    ["", ""],
    ["Tęskno mi ówdzie, gdzie któż o mnie stoi?", "Тоскую там, где — кто же обо мне печётся?"],
    ["I tak być musi, choć się tak nie stanie", "И так быть должно, хоть так и не станется"],
    ["Przyjaźni mojéj!", "с моей дружбой!"],
    ["Tęskno mi, Panie.", "тоскую я, Господи."],
]


def main():
    ns = sorted({c["lesson"] for c in CARDS})
    assert ns == list(range(1, len(LESSONS) + 1)), ns
    course = {"title": "Польский по стихам", "lessons": LESSONS,
              "poem": {"title": "Moja piosnka [II]", "author": "Cyprian Kamil Norwid", "year": 1854, "lines": POEM}}
    (ROOT / "packs" / "course.json").write_text(json.dumps(course, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    order = ["type", "level", "lesson", "text", "q", "tr", "options", "answer", "rows", "note", "topics"]
    lines = [json.dumps({k: c[k] for k in order if k in c and c[k] not in ("", [])}, ensure_ascii=False) for c in CARDS]
    pack = '{\n  "title": "Курс · уроки по Норвиду",\n  "source": "упражнения уроков, собраны make_course.py",\n  "items": [\n    ' + \
           ",\n    ".join(lines) + "\n  ]\n}\n"
    (ROOT / "packs" / "norwid-kurs.json").write_text(pack, encoding="utf-8")
    per = {}
    for c in CARDS:
        per[c["lesson"]] = per.get(c["lesson"], 0) + 1
    print("уроков:", len(LESSONS), "упражнений:", len(CARDS))
    print(" ".join("%d:%d" % (k, per[k]) for k in sorted(per)))


if __name__ == "__main__":
    main()
