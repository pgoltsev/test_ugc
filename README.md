### Тестовый проект опросов

#### Запуск

1. Устанавливаем [Docker](https://docs.docker.com/).
2. Клонируем репозиторий, идем в корневую папку.
3. Запускаем базу:
   ```shell
   docker compose up -d db
   ```
4. Делаем первоначальную настройку:
   ```shell
   docker compose up --build setup
   ```
5. Запускаем сервер:
   ```shell
   docker compose up --build app
   ```
6. Админка доступна по [http://localhost:8000/admin](http://localhost:8000/admin). Входим по имени и паролю `test`.

#### Результат выполнения

При первом посещении страниц может понадобиться авторизация, введите имя и пароль `test`.

1. Открываем в браузере:
    - [http://localhost:8000/surveys/1/questions/](http://localhost:8000/surveys/1/questions/) - список вопросов для
      опроса c id = 1.
    - [http://localhost:8000/surveys/1/questions/1/](http://localhost:8000/surveys/1/questions/1/) - вопрос с id = 1 для
      опроса с id = 1.
2. Также опрос можно пройти по ссылке [http://localhost:8000/surveys/1/](http://localhost:8000/surveys/1/). Вместо 1
   можно подставить любой другой id и пройти другой опрос.