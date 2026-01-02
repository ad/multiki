#!/usr/bin/env python3
"""
Утилита для управления версиями плагина Kodi ArjLover
"""

import argparse
import xml.etree.ElementTree as ET
import sys
import subprocess
import re

def get_current_version():
    """Получить текущую версию из addon.xml"""
    try:
        tree = ET.parse('addon.xml')
        root = tree.getroot()
        return root.get('version')
    except Exception as e:
        print(f"Ошибка чтения addon.xml: {e}")
        return None

def set_version(new_version):
    """Установить новую версию в addon.xml"""
    try:
        tree = ET.parse('addon.xml')
        root = tree.getroot()
        root.set('version', new_version)
        tree.write('addon.xml', encoding='utf-8', xml_declaration=True)
        return True
    except Exception as e:
        print(f"Ошибка записи addon.xml: {e}")
        return False

def bump_version(version, bump_type):
    """Увеличить версию согласно семантическому версионированию"""
    try:
        # Парсинг версии (major.minor.patch)
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$', version)
        if not match:
            raise ValueError(f"Неверный формат версии: {version}")
        
        major, minor, patch = map(int, match.groups()[:3])
        
        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        elif bump_type == 'patch':
            patch += 1
        else:
            raise ValueError(f"Неверный тип обновления: {bump_type}")
        
        return f"{major}.{minor}.{patch}"
    
    except Exception as e:
        print(f"Ошибка обновления версии: {e}")
        return None

def create_git_tag(version):
    """Создать Git тег для версии"""
    try:
        tag_name = f"v{version}"
        subprocess.run(['git', 'tag', tag_name], check=True)
        print(f"Создан тег: {tag_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка создания тега: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Управление версиями плагина Kodi ArjLover')
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда show
    subparsers.add_parser('show', help='Показать текущую версию')
    
    # Команда set
    set_parser = subparsers.add_parser('set', help='Установить конкретную версию')
    set_parser.add_argument('version', help='Новая версия (например, 1.2.3)')
    
    # Команда bump
    bump_parser = subparsers.add_parser('bump', help='Увеличить версию')
    bump_parser.add_argument('type', choices=['major', 'minor', 'patch'], 
                           help='Тип обновления версии')
    bump_parser.add_argument('--tag', action='store_true', 
                           help='Создать Git тег после обновления')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    current_version = get_current_version()
    if not current_version:
        return 1
    
    if args.command == 'show':
        print(f"Текущая версия: {current_version}")
        return 0
    
    elif args.command == 'set':
        if set_version(args.version):
            print(f"Версия обновлена: {current_version} → {args.version}")
            return 0
        return 1
    
    elif args.command == 'bump':
        new_version = bump_version(current_version, args.type)
        if not new_version:
            return 1
        
        if set_version(new_version):
            print(f"Версия обновлена: {current_version} → {new_version}")
            
            if args.tag:
                create_git_tag(new_version)
            
            return 0
        return 1
    
    return 1

if __name__ == '__main__':
    sys.exit(main())