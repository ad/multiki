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
    
    # Найти все строки таблицы с названиями мультфильмов
    # Паттерн для поиска строк с названиями: <td class="l"><a href="...">Название</a></td>
    title_pattern = r'<td class="l"><a href="[^"]*">([^<]+)</a></td>'
    title_matches = re.findall(title_pattern, html, re.IGNORECASE)
    
    # Найти все ссылки на видеофайлы для скачивания
    # Паттерн для поиска прямых ссылок на видео: href="http://multiki.arjlover.net/multiki/filename.ext"
    video_pattern = r'href="(http://multiki\.arjlover\.net/multiki/[^"]+\.(?:avi|mp4|mkv|flv))"'
    video_matches = re.findall(video_pattern, html, re.IGNORECASE)
    
    # Найти строки таблицы целиком для сопоставления названий и ссылок
    # Паттерн для поиска полных строк таблицы
    row_pattern = r'<tr class="[oe]">(.*?)</tr>'
    rows = re.findall(row_pattern, html, re.DOTALL | re.IGNORECASE)
    
    for row in rows:
        # Извлечь название из строки
        title_match = re.search(r'<td class="l"><a href="[^"]*">([^<]+)</a></td>', row, re.IGNORECASE)
        if not title_match:
            continue
            
        title = title_match.group(1).strip()
        
        # Извлечь ссылку на видеофайл из той же строки
        video_match = re.search(r'href="(http://multiki\.arjlover\.net/multiki/[^"]+\.(?:avi|mp4|mkv|flv))"', row, re.IGNORECASE)
        if not video_match:
            continue
            
        video_url = video_match.group(1)
        
        # Получить расширение файла
        _, extension = os.path.splitext(video_url)
        
        # Поиск thumbnail (пока оставим пустым, так как в данной структуре их нет)
        thumbnail_url = ""
        
        cartoon = Cartoon(
            title=title,
            url=video_url,
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