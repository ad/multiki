#!/bin/bash

# Скрипт для установки плагина в Kodi через ADB

set -e

PLUGIN_NAME="plugin.video.arjlover"
KODI_ADDONS_PATH="/storage/emulated/0/Android/data/org.xbmc.kodi/files/.kodi/addons"

echo "🔌 Установка плагина $PLUGIN_NAME в Kodi через ADB"

# Проверить подключение ADB
echo "📱 Проверка подключения ADB..."
if ! adb devices | grep -q "device$"; then
    echo "❌ Устройство не подключено или ADB не настроен"
    echo "💡 Убедитесь что:"
    echo "   - USB отладка включена на Android TV"
    echo "   - Устройство подключено и авторизовано"
    echo "   - ADB установлен (brew install android-platform-tools)"
    exit 1
fi

DEVICE=$(adb devices | grep "device$" | head -1 | cut -f1)
echo "✅ Подключено к устройству: $DEVICE"

# Собрать плагин если нужно
if [ ! -f "$PLUGIN_NAME-"*.zip ]; then
    echo "🔨 Сборка плагина..."
    ./build.sh
fi

# Найти ZIP файл
ZIP_FILE=$(ls $PLUGIN_NAME-*.zip | head -1)
if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ ZIP файл плагина не найден"
    exit 1
fi

echo "📦 Найден файл: $ZIP_FILE"

# Создать временную папку на устройстве
TEMP_PATH="/sdcard/Download"
echo "📁 Копирование в $TEMP_PATH..."
adb push "$ZIP_FILE" "$TEMP_PATH/"

# Проверить существование папки аддонов Kodi
echo "🔍 Проверка папки Kodi..."
if ! adb shell "[ -d '$KODI_ADDONS_PATH' ]"; then
    echo "❌ Папка Kodi не найдена: $KODI_ADDONS_PATH"
    echo "💡 Убедитесь что Kodi установлен и запускался хотя бы раз"
    exit 1
fi

# Извлечь плагин в папку аддонов
echo "📂 Установка плагина..."
adb shell "cd '$KODI_ADDONS_PATH' && unzip -o '$TEMP_PATH/$ZIP_FILE'"

# Проверить установку
if adb shell "[ -d '$KODI_ADDONS_PATH/$PLUGIN_NAME' ]"; then
    echo "✅ Плагин успешно установлен!"
    echo "📁 Путь: $KODI_ADDONS_PATH/$PLUGIN_NAME"
    
    # Показать содержимое
    echo "📋 Содержимое плагина:"
    adb shell "ls -la '$KODI_ADDONS_PATH/$PLUGIN_NAME/'"
    
    # Очистить временный файл
    adb shell "rm '$TEMP_PATH/$ZIP_FILE'"
    
    echo ""
    echo "🎉 Установка завершена!"
    echo "📺 Перезапустите Kodi и найдите плагин в:"
    echo "   Видео → Дополнения → ArjLover Cartoons"
    
else
    echo "❌ Ошибка установки плагина"
    exit 1
fi