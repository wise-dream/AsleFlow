# Интеграция AsleFlow с N8N

## Обзор

AsleFlow предоставляет API endpoints для интеграции с N8N для автоматической публикации постов в Telegram и других социальных сетях.

## API Endpoints

### 1. Получение постов готовых к публикации

**URL:** `GET /api/n8n/posts/pending`

**Параметры:**
- `limit` (опционально): Максимальное количество постов (по умолчанию 10)

**Пример запроса:**
```bash
curl "http://localhost:8001/api/n8n/posts/pending?limit=5"
```

**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "post_id": 123,
      "topic": "Как инвестировать в ETF",
      "content": "💰 **Как инвестировать в ETF**\n\n🔍 В мире финансов важно понимать основы...",
      "media_type": "text",
      "media_url": null,
      "scheduled_time": "2024-01-15T10:00:00Z",
      "platform": "telegram",
      "channel_id": "@my_channel",
      "channel_name": "Мой канал",
      "telegram_chat_id": "-1001234567890",
      "access_token": null,
      "user_id": 1,
      "workflow_id": 1,
      "workflow_name": "Финансовые советы"
    }
  ],
  "count": 1
}
```

### 2. Пометить пост как опубликованный

**URL:** `POST /api/n8n/posts/{post_id}/mark-published`

**Параметры:**
- `post_id`: ID поста
- `external_id` (опционально): Внешний ID поста (например, ID в Telegram)

**Пример запроса:**
```bash
curl -X POST "http://localhost:8001/api/n8n/posts/123/mark-published" \
  -H "Content-Type: application/json" \
  -d '{"external_id": "456789"}'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Post 123 marked as published",
  "post_id": 123
}
```

### 3. Пометить пост как неудачный

**URL:** `POST /api/n8n/posts/{post_id}/mark-failed`

**Параметры:**
- `post_id`: ID поста
- `error_message` (опционально): Сообщение об ошибке

**Пример запроса:**
```bash
curl -X POST "http://localhost:8001/api/n8n/posts/123/mark-failed" \
  -H "Content-Type: application/json" \
  -d '{"error_message": "Channel not found"}'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Post 123 marked as failed",
  "post_id": 123,
  "error_message": "Channel not found"
}
```

### 4. Получить статистику постов

**URL:** `GET /api/n8n/posts/stats`

**Параметры:**
- `user_id` (опционально): ID пользователя для фильтрации

**Пример запроса:**
```bash
curl "http://localhost:8001/api/n8n/posts/stats?user_id=1"
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "pending": 5,
    "scheduled": 3,
    "published": 25,
    "failed": 1,
    "total": 34
  }
}
```

### 5. Проверка здоровья API

**URL:** `GET /api/n8n/health`

**Пример запроса:**
```bash
curl "http://localhost:8001/api/n8n/health"
```

**Ответ:**
```json
{
  "success": true,
  "status": "healthy",
  "service": "AsleFlow N8N API",
  "version": "1.0.0"
}
```

## Настройка N8N Workflow

### 1. Создание workflow

1. Создайте новый workflow в N8N
2. Добавьте триггер "Cron" для запуска каждые 5 минут
3. Добавьте HTTP Request node для получения постов

### 2. HTTP Request для получения постов

**Настройки:**
- Method: GET
- URL: `http://localhost:8001/api/n8n/posts/pending`
- Query Parameters: `limit: 10`

### 3. Telegram Bot node

**Настройки:**
- Bot Token: Ваш Telegram Bot Token
- Chat ID: `{{$json.telegram_chat_id}}`
- Text: `{{$json.content}}`
- Parse Mode: HTML

### 4. HTTP Request для обновления статуса

**Успешная публикация:**
- Method: POST
- URL: `http://localhost:8001/api/n8n/posts/{{$json.post_id}}/mark-published`
- Body: `{"external_id": "{{$json.message_id}}"}`

**Неудачная публикация:**
- Method: POST
- URL: `http://localhost:8001/api/n8n/posts/{{$json.post_id}}/mark-failed`
- Body: `{"error_message": "{{$json.error}}"}`

## Пример полного workflow

```json
{
  "name": "AsleFlow Post Publisher",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "minute",
              "expression": "*/5"
            }
          ]
        }
      },
      "id": "cron-trigger",
      "name": "Cron Trigger",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "http://localhost:8001/api/n8n/posts/pending",
        "options": {
          "queryParameters": {
            "parameters": [
              {
                "name": "limit",
                "value": "10"
              }
            ]
          }
        }
      },
      "id": "get-posts",
      "name": "Get Posts",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "operation": "sendMessage",
        "chatId": "={{$json.telegram_chat_id}}",
        "text": "={{$json.content}}",
        "additionalFields": {
          "parse_mode": "HTML"
        }
      },
      "id": "telegram-send",
      "name": "Send to Telegram",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1,
      "position": [680, 300]
    },
    {
      "parameters": {
        "url": "=http://localhost:8001/api/n8n/posts/{{$json.post_id}}/mark-published",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "external_id",
              "value": "={{$json.message_id}}"
            }
          ]
        }
      },
      "id": "mark-published",
      "name": "Mark as Published",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [900, 300]
    }
  ],
  "connections": {
    "Cron Trigger": {
      "main": [
        [
          {
            "node": "Get Posts",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Get Posts": {
      "main": [
        [
          {
            "node": "Send to Telegram",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send to Telegram": {
      "main": [
        [
          {
            "node": "Mark as Published",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Запуск API сервера

```bash
# Установка зависимостей
pip install fastapi uvicorn

# Запуск сервера
python api/n8n_endpoints.py
```

Или через uvicorn:

```bash
uvicorn api.n8n_endpoints:app --host 0.0.0.0 --port 8001
```

## Безопасность

- API работает только с локальными запросами
- Для продакшена рекомендуется добавить аутентификацию
- Используйте HTTPS в продакшене
- Ограничьте доступ к API через firewall

## Мониторинг

- Используйте endpoint `/api/n8n/health` для мониторинга
- Логируйте все запросы к API
- Отслеживайте статистику публикаций через `/api/n8n/posts/stats` 