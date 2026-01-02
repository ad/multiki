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
    """Роутер для обработки URL параметров от Kodi."""
    try:
        params = dict(parse_qsl(paramstring))
        
        if params:
            action = params.get('action', '')
            
            if action == 'listing':
                list_videos()
            elif action == 'search':
                search_videos()
            elif action == 'play':
                play_video(params.get('path', ''))
            elif action == 'refresh':
                refresh_cache()
            else:
                raise ValueError(f'Invalid action: {action}')
        else:
            list_categories()
            
    except Exception as e:
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            f'Ошибка: {str(e)[:50]}',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )


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
    
    # Пункт "Поиск"
    url = f'{addon_url}?action=search'
    li = xbmcgui.ListItem('Поиск')
    li.setInfo('video', {'title': 'Поиск', 'plot': 'Поиск мультфильмов по названию'})
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
            
            li.setInfo('video', {
                'title': cartoon.title,
                'genre': 'Мультфильмы',
                'mediatype': 'movie',
                'plot': cartoon.plot,
                'duration': cartoon.duration
            })
            
            if cartoon.thumbnail:
                li.setArt({
                    'thumb': cartoon.thumbnail,
                    'poster': cartoon.thumbnail,
                    'fanart': cartoon.thumbnail
                })
            
            li.setProperty('IsPlayable', 'true')
            
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, 
                url=url, 
                listitem=li, 
                isFolder=False
            )
        
        # Установить тип контента и вид отображения
        xbmcplugin.setContent(addon_handle, 'movies')
        xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        
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
    """Начать воспроизведение видео."""
    try:
        video_url = urllib.parse.unquote(path)
        li = xbmcgui.ListItem(path=video_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
        
    except Exception as e:
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Видео недоступно',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())


def search_videos():
    """Поиск мультфильмов по названию."""
    addon_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    
    # Показать диалог ввода
    keyboard = xbmcgui.Dialog()
    query = keyboard.input('Поиск мультфильмов', type=xbmcgui.INPUT_ALPHANUM)
    
    if not query:
        xbmcplugin.endOfDirectory(addon_handle, succeeded=False)
        return
    
    query_lower = query.lower()
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))
        from cache import load_cache, save_cache
        from parser import fetch_catalog, parse_catalog
        
        cartoons = load_cache()
        
        if cartoons is None:
            try:
                base_url = 'https://multiki.arjlover.net/multiki/'
                html = fetch_catalog(base_url)
                cartoons = parse_catalog(html, base_url)
                save_cache(cartoons)
            except ConnectionError:
                xbmcgui.Dialog().notification(
                    'ArjLover Plugin', 
                    'Сайт недоступен',
                    xbmcgui.NOTIFICATION_ERROR,
                    5000
                )
                xbmcplugin.endOfDirectory(addon_handle, succeeded=False)
                return
        
        # Фильтруем по запросу
        results = [c for c in cartoons if query_lower in c.title.lower()]
        
        if not results:
            xbmcgui.Dialog().notification(
                'ArjLover Plugin', 
                f'Ничего не найдено: {query}',
                xbmcgui.NOTIFICATION_INFO,
                3000
            )
            xbmcplugin.endOfDirectory(addon_handle, succeeded=False)
            return
        
        # Показать результаты
        for cartoon in results:
            url = f'{addon_url}?action=play&path={urllib.parse.quote(cartoon.url)}'
            li = xbmcgui.ListItem(cartoon.title)
            
            li.setInfo('video', {
                'title': cartoon.title,
                'genre': 'Мультфильмы',
                'mediatype': 'movie',
                'plot': cartoon.plot,
                'duration': cartoon.duration
            })
            
            if cartoon.thumbnail:
                li.setArt({
                    'thumb': cartoon.thumbnail,
                    'poster': cartoon.thumbnail,
                    'fanart': cartoon.thumbnail
                })
            
            li.setProperty('IsPlayable', 'true')
            
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, 
                url=url, 
                listitem=li, 
                isFolder=False
            )
        
        xbmcplugin.setContent(addon_handle, 'movies')
        xbmcplugin.endOfDirectory(addon_handle)
        
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            f'Найдено: {len(results)}',
            xbmcgui.NOTIFICATION_INFO,
            2000
        )
        
    except Exception as e:
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Ошибка поиска',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
        xbmcplugin.endOfDirectory(addon_handle, succeeded=False)


def refresh_cache():
    """Принудительно обновить кэш каталога."""
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))
        from cache import clear_cache, save_cache
        from parser import fetch_catalog, parse_catalog
        
        clear_cache()
        
        base_url = 'https://multiki.arjlover.net/multiki/'
        html = fetch_catalog(base_url)
        cartoons = parse_catalog(html, base_url)
        save_cache(cartoons)
        
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            f'Каталог обновлен: {len(cartoons)} мультфильмов',
            xbmcgui.NOTIFICATION_INFO,
            3000
        )
        
    except ConnectionError:
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Сайт недоступен',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
    except Exception:
        xbmcgui.Dialog().notification(
            'ArjLover Plugin', 
            'Ошибка обновления',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )


if __name__ == '__main__':
    router(sys.argv[2][1:])