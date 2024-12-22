# C++ Code Execution Server

## Основные функции

- **POST /post_code**: Эндпоинт для выполнения переданного C++ кода.
  - Проверяет наличие `return` в переданном коде.
  - Поддерживает выполнение шаблонных функций с различными возвращаемыми типами (`int`, `double`, `string`, `bool`).
  - Возвращает результат выполнения кода или сообщение об ошибке.

---

## Установка

### Шаги установки

1. **Клонирование репозитория**:
   ```
   bash
   git clone 
   cd parser
   ```

2. **Создание виртуального окружения (рекомендуется):**:
   ```
    python3 -m venv venv
    source venv/bin/activate  # Для Linux/MacOS
    venv\Scripts\activate     # Для Windows
   ```

3. **Установка зависимостей:**:
   ```
   pip install -r requirements.txt
   ```

4. **Запуск сервера:**:
    ```
    uvicorn server:app --reload
    ```

## Использование API


### Запрос

- **URL**: `/post_code`
- **Метод**: `POST`
- **Тело запроса (JSON)**:
  ```json
  {
      "code": "string s = \"hello\"; return s;",
      "return_type": "string"
  }
  ```


### Ответы

- **HTTP статус: 200 OK**:
  ```json
    {
        "received_json": {
            "status": "success",
            "result": "hello"
        }
    }
  ```

- **HTTP статус: 400 Bad Request**:
  ```json
    {
        "detail": "The provided code does not contain a 'return' statement."
    }
  ```

- **HTTP статус: 400 Bad Request**:
  ```json
    {
        "detail": "Invalid return_type string."
    }
  ```


- **HTTP статус: 500 Internal Server Error**:
  ```json
    {
        "detail": "Internal error: <описание_ошибки>"
    }
  ```
