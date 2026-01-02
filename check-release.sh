#!/bin/bash

# Скрипт проверки готовности к релизу

set -e

echo "🔍 Проверка готовности к релизу..."

# Проверить, что мы на main ветке
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo "❌ Релизы создаются только с main/master ветки (текущая: $CURRENT_BRANCH)"
    exit 1
fi

# Проверить, что нет незафиксированных изменений
if ! git diff-index --quiet HEAD --; then
    echo "❌ Есть незафиксированные изменения"
    git status --porcelain
    exit 1
fi

# Запустить тесты
echo "🧪 Запуск тестов..."
python3 -m pytest tests/ -v --tb=short

# Проверить структуру плагина
echo "📁 Проверка структуры плагина..."
test -f addon.xml || { echo "❌ Отсутствует addon.xml"; exit 1; }
test -f main.py || { echo "❌ Отсутствует main.py"; exit 1; }
test -d resources/lib || { echo "❌ Отсутствует resources/lib/"; exit 1; }
test -f resources/lib/__init__.py || { echo "❌ Отсутствует resources/lib/__init__.py"; exit 1; }
test -f resources/lib/parser.py || { echo "❌ Отсутствует resources/lib/parser.py"; exit 1; }
test -f resources/lib/cache.py || { echo "❌ Отсутствует resources/lib/cache.py"; exit 1; }

# Проверить addon.xml
echo "📋 Проверка addon.xml..."
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('addon.xml')
root = tree.getroot()
assert root.get('id') == 'plugin.video.arjlover'
assert root.get('version') is not None
print(f'✅ Plugin ID: {root.get(\"id\")}')
print(f'✅ Version: {root.get(\"version\")}')
"

# Проверить импорты
echo "📦 Проверка импортов..."
cd resources/lib
python3 -c "
import sys
sys.path.insert(0, '.')
import parser
import cache
print('✅ Все модули импортируются успешно')
"
cd ../..

# Тестовая сборка
echo "🔨 Тестовая сборка..."
./build.sh > /dev/null
if [ -f "plugin.video.arjlover-"*.zip ]; then
    echo "✅ Сборка успешна"
    rm plugin.video.arjlover-*.zip
else
    echo "❌ Ошибка сборки"
    exit 1
fi

echo ""
echo "✅ Все проверки пройдены! Готов к релизу."
echo ""
echo "🚀 Для создания релиза:"
echo "   1. Локально: python version.py bump [patch|minor|major]"
echo "   2. GitHub Actions: Actions → Build and Release → Run workflow"