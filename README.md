# Crypto Pulse Bot

Crypto Pulse Bot — Telegram-бот для оперативного мониторинга цена криптовалют.

## Возможности
- Выбор монет для отслеживания (до 3 без премиума, до 10 в версии Premium);
- Получение актуальных цен и динамики за 24ч;
- Настройка периодических уведомлений;
- Два языка: русский и английский;
- Поддержка Premium-аккаунтов и реферальная программа.

## Ссылка на бота
[CrypoProPulseBot](https://t.me/CryptoProPulseBot) — просто нажмите для запуска.

## Быстрый старт
1. Скопируйте репозиторий:
```bash
git clone <ваш url>
cd crypto-pulse-bot
```
2. Создайте `.env` файл с переменными:
```
TELEGRAM_TOKEN=your-bot-token
SHOP_ID=your-yookassa-shop-id
YOOKASSA_API_KEY=your-yookassa-key
```
3. Установите зависимости и запустите бота:
```bash
pip install -r requirements.txt
python main.py
```

### Docker
```bash
docker build -t cryptopulsebot .
docker run -d --name cryptopulsebot -v cryptopulsebot_data:/app/data cryptopulsebot
```

Данные бота хранятся в volume `cryptopulsebot_data`.

## Основные команды
- `/start` — первое знакомство с ботом и выбор языка;
- `/choice_coin` — выбор монет для мониторинга;
- `/price` — актуальные цены выбранных монет;
- `/change_interval` — частота уведомлений;
- `/get_premium` — покупка Premium-доступа.
