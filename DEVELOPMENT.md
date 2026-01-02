# Разработка плагина

## Быстрый старт

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/ad/multiki.git
   cd multiki
   ```

2. **Создайте виртуальное окружение**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # или
   venv\Scripts\activate     # Windows
   ```

3. **Установите зависимости для разработки**:
   ```bash
   pip install pytest hypothesis
   ```

## Запуск тестов

```bash
# Все тесты
python -m pytest tests/ -v

# Только property-based тесты
python -m pytest tests/ -k "round_trip or extraction" -v

# С покрытием кода
pip install pytest-cov
python -m pytest tests/ --cov=resources.lib --cov-report=html
```

## Сборка для установки

```bash
# Создать ZIP файл для Kodi
./build.sh
```

## Структура проекта

### Файлы для Kodi
- `addon.xml` - метаданные плагина
- `main.py` - точка входа и роутинг
- `resources/lib/` - основная логика

### Файлы разработки
- `tests/` - тесты (не устанавливаются в Kodi)
- `README.md` - документация пользователя
- `BUILD.md` - инструкции по сборке
- `build.sh` - скрипт сборки

## Архитектура

```
main.py (Kodi interface)
    ↓
parser.py (HTML parsing)
    ↓
cache.py (Local storage)
```

## Тестирование

Проект использует:
- **Unit tests**: конкретные примеры
- **Property-based tests**: проверка на случайных данных
- **Integration tests**: проверка взаимодействия компонентов

## Добавление новых функций

1. Обновите требования в `.kiro/specs/*/requirements.md`
2. Обновите дизайн в `.kiro/specs/*/design.md`
3. Добавьте задачи в `.kiro/specs/*/tasks.md`
4. Реализуйте функциональность
5. Добавьте тесты
6. Обновите документацию