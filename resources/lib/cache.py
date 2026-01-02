import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

try:
    from .parser import Cartoon
except ImportError:
    # Fallback for testing
    from parser import Cartoon

CACHE_DURATION_HOURS = 24


def get_cache_path() -> str:
    """Получить путь к файлу кэша в userdata плагина."""
    try:
        # Попытка использовать Kodi API для получения пути userdata
        import xbmcvfs
        import xbmcaddon
        
        addon = xbmcaddon.Addon()
        addon_id = addon.getAddonInfo('id')
        userdata_path = xbmcvfs.translatePath(f'special://userdata/addon_data/{addon_id}/')
        
        # Создать директорию если не существует
        if not xbmcvfs.exists(userdata_path):
            xbmcvfs.mkdirs(userdata_path)
        
        return os.path.join(userdata_path, 'catalog_cache.json')
    
    except ImportError:
        # Fallback для тестирования без Kodi
        cache_dir = os.path.expanduser('~/.kodi_arjlover_cache')
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, 'catalog_cache.json')


def save_cache(cartoons: List[Cartoon]) -> None:
    """
    Сохранить список мультфильмов в кэш.
    
    Args:
        cartoons: список мультфильмов для сохранения
    """
    cache_path = get_cache_path()
    
    # Подготовить данные для сохранения
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'cartoons': [
            {
                'title': cartoon.title,
                'url': cartoon.url,
                'extension': cartoon.extension,
                'thumbnail': cartoon.thumbnail
            }
            for cartoon in cartoons
        ]
    }
    
    try:
        # Сохранить в JSON файл
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    except (OSError, IOError) as e:
        # Логировать предупреждение, но не прерывать выполнение
        try:
            import xbmc
            xbmc.log(f"ArjLover: Не удалось сохранить кэш: {e}", xbmc.LOGWARNING)
        except ImportError:
            # Fallback для тестирования
            print(f"Warning: Не удалось сохранить кэш: {e}")


def load_cache() -> Optional[List[Cartoon]]:
    """
    Загрузить список мультфильмов из кэша.
    
    Returns:
        Список мультфильмов или None если кэш невалиден/отсутствует
    """
    if not is_cache_valid():
        return None
    
    cache_path = get_cache_path()
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Восстановить объекты Cartoon из JSON
        cartoons = []
        for cartoon_data in cache_data.get('cartoons', []):
            cartoon = Cartoon(
                title=cartoon_data['title'],
                url=cartoon_data['url'],
                extension=cartoon_data['extension'],
                thumbnail=cartoon_data['thumbnail']
            )
            cartoons.append(cartoon)
        
        return cartoons
    
    except (OSError, IOError, json.JSONDecodeError, KeyError) as e:
        # Кэш поврежден или недоступен
        try:
            import xbmc
            xbmc.log(f"ArjLover: Ошибка чтения кэша: {e}", xbmc.LOGWARNING)
        except ImportError:
            # Fallback для тестирования
            print(f"Warning: Ошибка чтения кэша: {e}")
        
        return None


def is_cache_valid() -> bool:
    """
    Проверить валидность кэша (не истёк ли срок).
    
    Returns:
        True если кэш существует и не старше CACHE_DURATION_HOURS
    """
    cache_path = get_cache_path()
    
    # Проверить существование файла
    if not os.path.exists(cache_path):
        return False
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Получить timestamp из кэша
        timestamp_str = cache_data.get('timestamp')
        if not timestamp_str:
            return False
        
        # Парсить timestamp
        cache_time = datetime.fromisoformat(timestamp_str)
        current_time = datetime.now()
        
        # Проверить, не истёк ли срок
        time_diff = current_time - cache_time
        return time_diff < timedelta(hours=CACHE_DURATION_HOURS)
    
    except (OSError, IOError, json.JSONDecodeError, ValueError, KeyError):
        # Любая ошибка означает невалидный кэш
        return False


def clear_cache() -> None:
    """Удалить файл кэша."""
    cache_path = get_cache_path()
    
    try:
        if os.path.exists(cache_path):
            os.remove(cache_path)
    
    except OSError as e:
        try:
            import xbmc
            xbmc.log(f"ArjLover: Не удалось удалить кэш: {e}", xbmc.LOGWARNING)
        except ImportError:
            # Fallback для тестирования
            print(f"Warning: Не удалось удалить кэш: {e}")