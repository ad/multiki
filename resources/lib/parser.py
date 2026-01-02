from dataclasses import dataclass
from typing import List
import urllib.request
import urllib.parse
import re
import os


@dataclass
class Cartoon:
    title: str
    url: str
    extension: str
    thumbnail: str
    info_url: str = ""  # URL страницы с подробностями
    duration: str = ""
    year: str = ""
    plot: str = ""


@dataclass
class CartoonDetails:
    title: str
    duration: str
    size: str
    video_format: str
    audio_format: str
    thumbnail: str
    plot: str = ""


def parse_catalog(html: str, base_url: str) -> List[Cartoon]:
    """Распарсить HTML и извлечь список мультфильмов."""
    cartoons = []
    
    # Найти строки таблицы <tr class=e> или <tr class=o>
    row_pattern = r'<tr class=[eo]>(.*?)</tr>'
    rows = re.findall(row_pattern, html, re.DOTALL | re.IGNORECASE)
    
    for row in rows:
        # Извлечь название и URL страницы подробностей
        title_match = re.search(r'<td class=l><a href="([^"]*)"[^>]*>([^<]+)</a></td>', row, re.IGNORECASE)
        if not title_match:
            continue
        
        info_url = title_match.group(1)
        title = title_match.group(2).strip()
        
        if info_url.startswith('/'):
            info_url = 'https://multiki.arjlover.net' + info_url
        
        # Извлечь URL видео
        url_match = re.search(r'href="([^"]*multiki/[^"]+\.(?:avi|mp4|mkv|flv))"', row, re.IGNORECASE)
        if not url_match:
            continue
        
        video_url = url_match.group(1)
        
        if video_url.startswith('/'):
            video_url = 'https://multiki.arjlover.net' + video_url
        elif not video_url.startswith('http'):
            video_url = urllib.parse.urljoin(base_url, video_url)
        
        _, extension = os.path.splitext(video_url)
        
        # Сформировать URL thumbnail
        filename = os.path.basename(video_url)
        thumbnail = f"https://multiki.arjlover.net/ap/{filename}/{filename}.thumb1.jpg"
        
        # Извлечь размер файла (третья ячейка <td class=r>)
        size_match = re.search(r'<td class=r>([0-9.]+)</td>', row, re.IGNORECASE)
        size_str = ""
        if size_match:
            try:
                size_bytes = int(size_match.group(1).replace('.', ''))
                size_mb = size_bytes / (1024 * 1024)
                size_str = f"{size_mb:.0f} МБ"
            except:
                pass
        
        # Извлечь длительность (пятая ячейка, формат 00:09:44)
        duration_match = re.search(r'<td>(\d{2}:\d{2}:\d{2})</td>', row, re.IGNORECASE)
        duration = duration_match.group(1) if duration_match else ""
        
        # Сформировать описание
        plot_parts = []
        if duration:
            plot_parts.append(f"Длительность: {duration}")
        if size_str:
            plot_parts.append(f"Размер: {size_str}")
        plot = "\n".join(plot_parts)
        
        cartoons.append(Cartoon(
            title=title,
            url=video_url,
            extension=extension,
            thumbnail=thumbnail,
            info_url=info_url,
            duration=duration,
            plot=plot
        ))
    
    return cartoons


def fetch_details(info_url: str) -> CartoonDetails:
    """Загрузить и распарсить страницу с подробностями мультфильма."""
    try:
        with urllib.request.urlopen(info_url, timeout=60) as response:
            raw_content = response.read()
            html = raw_content.decode('windows-1251', errors='ignore')
        
        # Извлечь название
        title_match = re.search(r'<h1>([^<]+)</h1>', html)
        title = title_match.group(1).strip() if title_match else ""
        
        # Извлечь продолжительность
        duration_match = re.search(r'<strong>Продолжительность:</strong></td><td>([^<]+)</td>', html)
        duration = duration_match.group(1).strip() if duration_match else ""
        
        # Извлечь размер
        size_match = re.search(r'<strong>Размер:</strong></td><td>([^<]+)</td>', html)
        size = size_match.group(1).strip() if size_match else ""
        
        # Извлечь видеоформат
        video_match = re.search(r'<strong>Видеоформат:</strong></td><td>([^<]+)</td>', html)
        video_format = video_match.group(1).strip() if video_match else ""
        
        # Извлечь аудиоформат
        audio_match = re.search(r'<strong>Аудиоформат:</strong></td><td>([^<]+)</td>', html)
        audio_format = audio_match.group(1).strip() if audio_match else ""
        
        # Извлечь thumbnail
        thumb_match = re.search(r'src="([^"]*thumb1\.jpg)"', html)
        thumbnail = ""
        if thumb_match:
            thumbnail = thumb_match.group(1)
            if thumbnail.startswith('/'):
                thumbnail = 'https://multiki.arjlover.net' + thumbnail
        
        return CartoonDetails(
            title=title,
            duration=duration,
            size=size,
            video_format=video_format,
            audio_format=audio_format,
            thumbnail=thumbnail
        )
    
    except Exception as e:
        return CartoonDetails(title="", duration="", size="", video_format="", audio_format="", thumbnail="")


def fetch_catalog(base_url: str) -> str:
    """Загрузить HTML страницу каталога."""
    try:
        with urllib.request.urlopen(base_url, timeout=60) as response:
            raw_content = response.read()
            
            # Сначала windows-1251, так как это кодировка сайта
            try:
                return raw_content.decode('windows-1251')
            except UnicodeDecodeError:
                pass
            
            for encoding in ['cp1251', 'utf-8', 'iso-8859-1']:
                try:
                    return raw_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            return raw_content.decode('windows-1251', errors='ignore')
    
    except urllib.error.URLError as e:
        raise ConnectionError(f"Не удалось загрузить каталог: {e}")
    except Exception as e:
        raise ConnectionError(f"Ошибка при загрузке каталога: {e}")