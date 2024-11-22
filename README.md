# testElvis
Тестовое задание для ЭЛВИС, в виде API сервера
Подробная документация API находится в папке [docs](https://github.com/github.com/No4vick/testElvis/tree/main/docs), а также на запущенном сервере по адресу `http://server_domain/docs`

# Запуск прокета в Docker
Для того, чтобы запустить сервер с его компонентами требуется `docker-compose`.
Для запуска следует склонировать проект:
```
git clone https://github.com/No4vick/testElvis.git
```
После чего перейти в директорию с git репозиторием и запустить с помощью
```
docker-compose up -d
```

# Используемые технологии
В проекте используется `FastAPI` для самого API сервера.
В качестве базы данных используется `PostgreSQL`.
В качестве reverse-proxy использован `nginx`.