#!/bin/sh
# Проверяет колоду, пересобирает packs/index.json и выкладывает изменения на хостинг.
set -e
cd "$(dirname "$0")"
python3 build_packs.py
git add -A
if git diff --cached --quiet; then
  echo "Изменений нет."
  exit 0
fi
git commit -q -m "${1:-Обновление колоды}"
if git remote get-url origin >/dev/null 2>&1; then
  git push -q
  echo "Опубликовано. На телефоне: «Колода → Проверить обновления» (или просто открой приложение)."
else
  echo "Закоммичено локально, хостинг ещё не подключён."
fi
