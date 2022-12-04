## Foodgram - сайт «Продуктовый помощник»

На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

### Технологии

- [Python]
- [Django] - веб-фреймворк на Python.
- [Django REST framework] - инструментарий для создания веб-API.
- [PostgreSQL] - система управления базами данных (СУБД).
- [Nginx] - веб-сервер.
- [Gunicorn] - HTTP-сервер с интерфейсом шлюза веб-сервера Python.
- [Docker] - автоматизация развёртывания и управления приложениями в средах с поддержкой контейнеризации, контейнеризатор приложений.
- [GitHubActions] - функция Github, позволяющая автоматизировать рабочий процесс.
- [Yandex.Cloud] - облачная платформа от Яндекс.

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/shlenskov/foodgram-project-react
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv && . venv/bin/activate
```

Установить pip и зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

### Шаблон наполнения env-файла:

```
DB_ENGINE
DB_NAME
POSTGRES_USER
POSTGRES_PASSWORD
DB_HOST
DB_PORT

```

### Развертывание контейнеров и заполнение БД

```

Сборка и развёртывание контейнеров в «фоновом режиме»:

docker-compose up -d --build

Выполнение миграций:

docker-compose exec web python manage.py migrate

Запуск загрузки ингредиентов:

docker-compose exec backend python manage.py load_ingrs

Запуск загрузки загрузки тегов:

docker-compose exec backend python manage.py load_tags

Создание суперпользователя:

docker-compose exec web python manage.py createsuperuser

Сборка статики:

docker-compose exec web python manage.py collectstatic --no-input

Зайдите на сайт по ссылке: http://.....

Создание дампа (резервную копию) базы данных:

docker-compose exec web python manage.py dumpdata > fixtures.json 

Останавка контейнеров:

docker-compose down -v

```

## Разработчики

- Владимир Шленсков
- Команда Яндекс.Практикум

[//]: #

   [Django REST framework]: <https://www.django-rest-framework.org/>