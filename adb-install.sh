#!/bin/bash

# Универсальный скрипт установки плагина в Kodi через ADB

set -e

PLUGIN_NAME="plugin.video.arjlover"

# Возможные пути к папке аддонов Kodi
KODI_PATHS=(
    "/storage/emulated/0/Android/data/org.xbmc.kodi/files/.kodi/addons"
    "/sdcard/Android/data/org.xbmc.kodi/files/.kodi/addons"
    "/storage/emulated/0/.kodi/addons"
    "/sdcard/.kodi/addons"
)

echo "🔌 Установка плагина $PLUGIN_NAME в Kodi через ADB"

# Проверить ADB
if ! command -v adb &> /dev/null; then
    echo "❌ ADB не установлен"
    echo "💡 Установите: brew install android-platform-tools (macOS)"
    exit 1
fi

# Проверить подключение
echo "📱 Проверка подключения..."
DEVICES=$(adb devices | grep -c "device$" || true)
if [ "$DEVICES" -eq 0 ]; then
    echo "❌ Устройство не подключено"
    echo "💡 Включите USB отладку и подключите Android TV"
    exit 1
elif [ "$DEVICES" -gt 1 ]; then
    echo "⚠️  Подключено несколько устройств:"
    adb devices
    echo "💡 Используйте: adb -s DEVICE_ID shell"
    exit 1
fi

DEVICE=$(adb devices | grep "device$" | head -1 | cut -f1)
echo "✅ Подключено: $DEVICE"

# Найти путь Kodi
echo "🔍 Поиск папки Kodi..."
KODI_PATH=""
for path in "${KODI_PATHS[@]}"; do
    if adb shell "[ -d '$path' ]" 2>/dev/null; then
        KODI_PATH="$path"
        echo "✅ Найдена папка: $KODI_PATH"
        break
    fi
done

if [ -z "$KODI_PATH" ]; then
    echo "❌ Папка Kodi не найдена"
    echo "💡 Проверьте что Kodi установлен и запускался"
    echo "🔍 Проверенные пути:"
    for path in "${KODI_PATHS[@]}"; do
        echo "   - $path"
    done
    exit 1
fi

# Собрать плагин
if [ ! -f "$PLUGIN_NAME-"*.zip ]; then
    echo "🔨 Сборка плагина..."
    ./build.sh
fi

ZIP_FILE=$(ls $PLUGIN_NAME-*.zip | head -1)
echo "📦 Файл: $ZIP_FILE"

# Установка
echo "📂 Установка плагина..."
TEMP_PATH="/storage/emulated/0/Download"

# Копировать ZIP
adb push "$ZIP_FILE" "$TEMP_PATH/"

# Удалить старую версию если есть
adb shell "rm -rf '$KODI_PATH/$PLUGIN_NAME'" 2>/dev/null || true

# Извлечь новую версию
adb shell "cd '$KODI_PATH' && unzip -o '$TEMP_PATH/$(basename "$ZIP_FILE")'"

# Проверить
if adb shell "[ -f '$KODI_PATH/$PLUGIN_NAME/addon.xml' ]"; then
    VERSION=$(adb shell "grep 'version=' '$KODI_PATH/$PLUGIN_NAME/addon.xml'" | sed 's/.*version="\([^"]*\)".*/\1/')
    echo "✅ Плагин установлен! Версия: $VERSION"
    
    # ZIP файл оставляем в Download для удобства
    
    echo ""
    echo "🎉 Готово!"
    echo "📺 В Kodi: Видео → Дополнения → ArjLover Cartoons"
    echo "🔄 Может потребоваться перезапуск Kodi"
else
    echo "❌ Ошибка установки"
    exit 1
fi