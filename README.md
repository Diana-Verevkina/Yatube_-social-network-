# Социальная сеть Yatube
hw05_final

 <img src="img_5.png" style="height: 220pt">

## Описание 
Данный проект представляет из себя социальную сеть. 
Она дает пользователям следующие возможности:

- Создать учетную запись,
- Изменить пароль,
- Публиковать записи,
- Просматривать записи других пользователей,
- Подписываться на любимых авторов,
- Отмечать понравившиеся записи,
- Комментировать записи.

## Технологии 
Python, Django, Git, HTML, CSS, SQLite, PostgreSQL, pytest, Docker, NginX, Яндекс.Облако, Gunicorn, Linux, Bootstrap, WSGI

## Запуск проекта в dev-режиме
- Клонирование репозитория
```python
git clone git@github.com:Diana-Verevkina/Yatube_-social-network-.git
cd hw05_final
```
- Установка и активация виртуального окружения
```python
python -m venv venv
source venv/bin/activate
```
- Установка зависимостей
```python
pip install -r requirements.txt
```
- Выполнить миграции
```python
python3 manage.py migrate
```
- Запуск проект
В папке с файлом manage.py выполните команду:
```python
python3 manage.py runserver
```