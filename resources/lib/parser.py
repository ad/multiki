from dataclasses import dataclass
from typing import List
import urllib.request
import urllib.parse
import re
import os


@dataclass
class Cartoon:
    """Представление мультфильма."""
    title: str      # Название (декодированное из URL)
    url: str        # Полный URL видеофайла
    extension: str  # Расширение файла (.avi, .mp4, etc)
    thumbnail: str  # URL изображения-превью (если доступно)


def decode_filename(encoded: str) -> str:
    """
    Декодировать URL-encoded имя файла в читаемое название.
    
    Args:
        encoded: URL-encoded строка (например, "%D0%9C%D0%B0%D1%88%D0%B0")
    
    Returns:
        Декодированная строка на русском языке
    """
    # URL-decode с UTF-8
    decoded = urllib.parse.unquote(encoded, encoding='utf-8')
    
    # Удаление расширения файла из названия только если есть расширение
    name, ext = os.path.splitext(decoded)
    if ext:
        return name
    else:
        return decoded


def parse_catalog(html: str, base_url: str) -> List[Cartoon]:
    """
    Распарсить HTML и извлечь список мультфильмов.
    
    Args:
        html: HTML содержимое страницы
        base_url: базовый URL для построения полных ссылок
    
    Returns:
        Список объектов Cartoon
    """
    cartoons = []
    
    # Поддерживаемые видео расширения
    video_extensions = {'.avi', '.mp4', '.mkv', '.flv'}
    
    # Поддерживаемые расширения изображений для thumbnail
    image_extensions = {'.jpg', '.png'}
    
    # Найти все ссылки на файлы
    # Ищем href="filename.ext" в HTML
    link_pattern = r'href="([^"]+\.(?:avi|mp4|mkv|flv))"'
    video_matches = re.findall(link_pattern, html, re.IGNORECASE)
    
    # Также найти все изображения для быстрого поиска thumbnail
    img_pattern = r'href="([^"]+\.(?:jpg|png))"'
    image_matches = set(re.findall(img_pattern, html, re.IGNORECASE))
    
    for video_file in video_matches:
        # Получить расширение файла
        _, extension = os.path.splitext(video_file)
        
        # Проверить, что это видео файл
        if extension.lower() in video_extensions:
            # Построить полный URL
            full_url = urllib.parse.urljoin(base_url, video_file)
            
            # Декодировать название из имени файла
            title = decode_filename(video_file)
            
            # Поиск соответствующего thumbnail
            thumbnail_url = ""
            base_name = os.path.splitext(video_file)[0]
            
            # Проверить наличие изображений с тем же базовым именем
            for img_ext in image_extensions:
                img_filename = base_name + img_ext
                if img_filename in image_matches:
                    thumbnail_url = urllib.parse.urljoin(base_url, img_filename)
                    break
            
            cartoon = Cartoon(
                title=title,
                url=full_url,
                extension=extension,
                thumbnail=thumbnail_url
            )
            cartoons.append(cartoon)
    
    return cartoons

def fetch_catalog(base_url: str) -> str:
    """
    Загрузить HTML страницу каталога.
    
    Args:
        base_url: URL каталога (https://multiki.arjlover.net/multiki/)
    
    Returns:
        HTML содержимое страницы
    
    Raises:
        ConnectionError: если сайт недоступен
    """
    try:
        # HTTP GET запрос с urllib
        with urllib.request.urlopen(base_url, timeout=30) as response:
            # Читаем содержимое и пробуем разные кодировки
            raw_content = response.read()
            
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'windows-1251', 'cp1251', 'iso-8859-1']:
                try:
                    html_content = raw_content.decode(encoding)
                    return html_content
                except UnicodeDecodeError:
                    continue
            
            # Если ничего не сработало, используем errors='ignore'
            html_content = raw_content.decode('utf-8', errors='ignore')
            return html_content
    
    except urllib.error.URLError as e:
        raise ConnectionError(f"Не удалось загрузить каталог: {e}")
    except Exception as e:
        raise ConnectionError(f"Ошибка при загрузке каталога: {e}")