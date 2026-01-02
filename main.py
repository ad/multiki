#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import urllib.parse
from urllib.parse import parse_qsl

import xbmcplugin
import xbmcgui
import xbmcaddon


def router(paramstring):
    """
    Роутер для обработки URL параметров от Kodi.
    
    Args:
        paramstring: URL query string с параметрами действия
    
    Actions:
        - "" (empty): показать главное меню
        - "listing": показать список мультфильмов
        - "play": воспроизвести видео
        - "refresh": принудительно обновить кэш
    """
    try:
        params = dict(parse_qsl(paramstring))
        
        if params:
            if params['action'] == 'listing':
                list_videos()
            elif params['action'] == 'play':
                play_video(params['path'])
            elif params['action'] == 'refresh':
                refresh_cache()
            else:
                raise ValueError(f'Invalid paramstring: {paramstring}')
        else:
            list_categories()
            
    except Exception as e:
        # Общая обработка ошибок роутера
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Ошибка плагина',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
        # Логировать ошибку для отладки
        try:
            import xbmc
            xbmc.log(f"ArjLover Plugin Error: {str(e)}", xbmc.LOGERROR)
        except ImportError:
            pass


def list_categories():
    """Показать главное меню с категориями."""
    addon = xbmcaddon.Addon()
    addon_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    
    # Пункт "Все мультфильмы"
    url = f'{addon_url}?action=listing'
    li = xbmcgui.ListItem('Все мультфильмы')
    li.setInfo('video', {'title': 'Все мультфильмы', 'genre': 'Мультфильмы'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    
    # Пункт "Обновить каталог"
    url = f'{addon_url}?action=refresh'
    li = xbmcgui.ListItem('Обновить каталог')
    li.setInfo('video', {'title': 'Обновить каталог', 'plot': 'Принудительно обновить список мультфильмов'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
    
    xbmcplugin.endOfDirectory(addon_handle)


def list_videos():
    """Показать список мультфильмов из каталога."""
    addon = xbmcaddon.Addon()
    addon_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    
    try:
        # Импорт модулей из resources/lib
        sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))
        from cache import load_cache, save_cache
        from parser import fetch_catalog, parse_catalog
        
        # Попытка загрузить из кэша
        cartoons = load_cache()
        
        if cartoons is None:
            # Кэш недоступен или устарел, загружаем с сайта
            try:
                base_url = 'https://multiki.arjlover.net/multiki/'
                html = fetch_catalog(base_url)
                cartoons = parse_catalog(html, base_url)
                
                # Сохранить в кэш
                save_cache(cartoons)
                
            except ConnectionError as e:
                # Показать ошибку пользователю
                xbmcgui.Dialog().notification(
                    'ArjLover Plugin', 
                    'Сайт недоступен. Проверьте подключение к интернету.',
                    xbmcgui.NOTIFICATION_ERROR,
                    5000
                )
                xbmcplugin.endOfDirectory(addon_handle, succeeded=False)
                return
        
        # Создать ListItem для каждого мультфильма
        for cartoon in cartoons:
            url = f'{addon_url}?action=play&path={urllib.parse.quote(cartoon.url)}'
            li = xbmcgui.ListItem(cartoon.title)
            
            # Установить информацию о видео
            li.setInfo('video', {
                'title': cartoon.title,
                'genre': 'Мультфильмы',
                'mediatype': 'movie'
            })
            
            # Установить thumbnail если доступен
            if cartoon.thumbnail:
                li.setArt({'thumb': cartoon.thumbnail})
            
            # Указать что это воспроизводимый элемент
            li.setProperty('IsPlayable', 'true')
            
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, 
                url=url, 
                listitem=li, 
                isFolder=False
            )
        
        xbmcplugin.endOfDirectory(addon_handle)
        
    except Exception as e:
        # Общая обработка ошибок
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Ошибка загрузки каталога',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
        xbmcplugin.endOfDirectory(addon_handle, succeeded=False)


def play_video(path):
    """
    Начать воспроизведение видео.
    
    Args:
        path: URL видеофайла
    """
    try:
        # Декодировать URL если он был закодирован
        video_url = urllib.parse.unquote(path)
        
        # Создать ListItem для воспроизведения
        li = xbmcgui.ListItem(path=video_url)
        
        # Передать URL в Kodi player
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
        
    except Exception as e:
        # Обработка ошибок воспроизведения
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Видео недоступно',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())


def refresh_cache():
    """Принудительно обновить кэш каталога."""
    try:
        # Импорт модулей из resources/lib
        sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))
        from cache import clear_cache, save_cache
        from parser import fetch_catalog, parse_catalog
        
        # Очистить существующий кэш
        clear_cache()
        
        # Загрузить свежие данные с сайта
        base_url = 'https://multiki.arjlover.net/multiki/'
        html = fetch_catalog(base_url)
        cartoons = parse_catalog(html, base_url)
        
        # Сохранить в кэш
        save_cache(cartoons)
        
        # Показать уведомление об успехе
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Каталог успешно обновлен',
            xbmcgui.NOTIFICATION_INFO,
            3000
        )
        
    except ConnectionError as e:
        # Ошибка сети
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Сайт недоступен. Проверьте подключение к интернету.',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
    except Exception as e:
        # Общая ошибка
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Ошибка обновления каталога',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )


if __name__ == '__main__':
    router(sys.argv[2][1:])