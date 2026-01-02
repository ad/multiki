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
    """
    cartoons = []
    
    # Сначала попробуем извлечь из таблицы с правильными названиями
    cartoons = parse_table_format(html, base_url)
    
    # Если таблица не найдена, используем оригинальный метод
    if not cartoons:
        cartoons = parse_simple_links(html, base_url)
    
    return cartoons


def parse_table_format(html: str, base_url: str) -> List[Cartoon]:
    """Парсинг таблицы с правильными названиями."""
    cartoons = []
    
    # Найти строки таблицы
    row_pattern = r'<tr class="[oe]">(.*?)</tr>'
    rows = re.findall(row_pattern, html, re.DOTALL | re.IGNORECASE)
    
    for row in rows:
        # Извлечь название
        title_match = re.search(r'<td class="l"><a href="[^"]*">([^<]+)</a></td>', row, re.IGNORECASE)
        if not title_match:
            continue
            
        title = title_match.group(1).strip()
        
        # Извлечь ссылку на видеофайл
        video_match = re.search(r'href="([^"]*multiki/[^"]+\.(?:avi|mp4|mkv|flv))"', row, re.IGNORECASE)
        if not video_match:
            continue
            
        video_url = video_match.group(1)
        
        # Если ссылка относительная, сделать абсолютной
        if video_url.startswith('/'):
            video_url = 'https://multiki.arjlover.net' + video_url
        elif not video_url.startswith('http'):
            video_url = urllib.parse.urljoin(base_url, video_url)
        
        _, extension = os.path.splitext(video_url)
        
        cartoon = Cartoon(
            title=title,
            url=video_url,
            extension=extension,
            thumbnail=""
        )
        cartoons.append(cartoon)
    
    return cartoons


def parse_simple_links(html: str, base_url: str) -> List[Cartoon]:
    """Оригинальный метод парсинга - извлечение из ссылок на файлы."""
    cartoons = []
    
    # Найти все ссылки на видеофайлы
    link_pattern = r'href="([^"]+\.(?:avi|mp4|mkv|flv))"'
    video_matches = re.findall(link_pattern, html, re.IGNORECASE)
    
    for video_file in video_matches:
        _, extension = os.path.splitext(video_file)
        
        # Построить полный URL
        if video_file.startswith('/'):
            full_url = 'https://multiki.arjlover.net' + video_file
        elif video_file.startswith('http'):
            full_url = video_file
        else:
            full_url = urllib.parse.urljoin(base_url, video_file)
        
        # Декодировать название из имени файла
        filename = os.path.basename(video_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Попробуем найти читаемое название в HTML рядом с этой ссылкой
        readable_title = find_readable_title(html, video_file)
        if readable_title:
            title = readable_title
        else:
            # Fallback: декодируем из имени файла и улучшаем
            title = urllib.parse.unquote(name_without_ext, encoding='utf-8')
            title = improve_title(title)
        
        cartoon = Cartoon(
            title=title,
            url=full_url,
            extension=extension,
            thumbnail=""
        )
        cartoons.append(cartoon)
    
    return cartoons


def find_readable_title(html: str, video_file: str) -> str:
    """Попытаться найти читаемое название рядом со ссылкой на видео."""
    # Извлечь имя файла без пути
    filename = os.path.basename(video_file)
    base_name = os.path.splitext(filename)[0]
    
    # Поискать ссылку на info страницу с тем же именем
    info_pattern = rf'<a href="[^"]*{re.escape(base_name)}[^"]*\.html">([^<]+)</a>'
    match = re.search(info_pattern, html, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    return ""


def improve_title(title: str) -> str:
    """Улучшить название, заменив точки на пробелы и исправив известные сокращения."""
    # Заменить точки на пробелы
    title = title.replace('.', ' ')
    
    # Исправить известные сокращения
    replacements = {
        'pljus': '+',
        'ravno': '=',
        'pervyj': 'первый',
        'den': 'день',
        'dekabrya': 'декабря',
        'popugaev': 'попугаев',
        'reis': 'рейс',
        'babushka': 'бабушка',
        'udava': 'удава',
        'velikoe': 'великое',
        'zakrytie': 'закрытие',
        'zavtra': 'завтра',
        'budet': 'будет',
        'zaraydka': 'зарядка',
        'dlya': 'для',
        'hvosta': 'хвоста',
        'kak': 'как',
        'lechit': 'лечить',
        'kuda': 'куда',
        'idet': 'идет',
        'slonenok': 'слоненок',
        'nenaglyadnoe': 'наглядное',
        'posobie': 'пособие',
        'privet': 'привет',
        'martyshke': 'мартышке',
        'vdrug': 'вдруг',
        'poluchitsya': 'получится',
    }
    
    words = title.split()
    improved_words = []
    
    for word in words:
        # Попробовать найти замену
        lower_word = word.lower()
        if lower_word in replacements:
            improved_words.append(replacements[lower_word])
        else:
            improved_words.append(word)
    
    return ' '.join(improved_words)


def parse_direct_links(html: str, base_url: str) -> List[Cartoon]:
    """Парсинг прямых ссылок если таблица не найдена."""
    cartoons = []
    
    # Найти все ссылки на видеофайлы
    video_pattern = r'href="([^"]*multiki/[^"]+\.(?:avi|mp4|mkv|flv))"[^>]*>([^<]*)</a>'
    matches = re.findall(video_pattern, html, re.IGNORECASE)
    
    for video_url, link_text in matches:
        if 'http' in link_text.lower():  # Пропустить ссылки типа "http"
            continue
            
        # Если ссылка относительная, сделать абсолютной
        if video_url.startswith('/'):
            video_url = 'https://multiki.arjlover.net' + video_url
        elif not video_url.startswith('http'):
            video_url = urllib.parse.urljoin(base_url, video_url)
        
        # Получить название из имени файла если текст ссылки пустой
        if not link_text.strip():
            filename = os.path.basename(video_url)
            title = os.path.splitext(filename)[0]
            title = urllib.parse.unquote(title, encoding='utf-8')
        else:
            title = link_text.strip()
        
        _, extension = os.path.splitext(video_url)
        
        cartoon = Cartoon(
            title=title,
            url=video_url,
            extension=extension,
            thumbnail=""
        )
        cartoons.append(cartoon)
    
    return cartoons

def fetch_catalog(base_url: str) -> str:
    """
    Загрузить HTML страницу каталога.
    """
    try:
        with urllib.request.urlopen(base_url, timeout=30) as response:
            raw_content = response.read()
            
            # Сначала попробуем windows-1251, так как это кодировка сайта
            try:
                html_content = raw_content.decode('windows-1251')
                return html_content
            except UnicodeDecodeError:
                pass
            
            # Затем другие кодировки
            for encoding in ['cp1251', 'utf-8', 'iso-8859-1']:
                try:
                    html_content = raw_content.decode(encoding)
                    return html_content
                except UnicodeDecodeError:
                    continue
            
            # Fallback с игнорированием ошибок
            html_content = raw_content.decode('windows-1251', errors='ignore')
            return html_content
    
    except urllib.error.URLError as e:
        raise ConnectionError(f"Не удалось загрузить каталог: {e}")
    except Exception as e:
        raise ConnectionError(f"Ошибка при загрузке каталога: {e}")