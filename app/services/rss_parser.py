import asyncio
import os
import feedparser
from datetime import datetime
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


RSS_URL = os.getenv("RSS_URL")
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "24"))
RSS_KEYWORDS = os.getenv(
    "RSS_KEYWORDS",
    "Октябрьский,Тульская"
).split(",")

# Ключевые слова для фильтрации новостей
KEYWORDS = [keyword.strip() for keyword in RSS_KEYWORDS if keyword.strip()]

class RSSParserBot:
    def __init__(self, bot: Bot, chat_id: int):
        
        self.bot = bot
        self.chat_id = chat_id
        self.keywords = [kw.lower() for kw in KEYWORDS]
        self.check_interval = CHECK_INTERVAL_HOURS * 3600  # переводим в секунды
        self.seen_links = set()  # для хранения уже обработанных новостей
        self.rss_url = RSS_URL

    async def parse_rss(self):
        """Парсинг RSS-ленты и фильтрация новостей"""
        try:
            # Парсим RSS ленту
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo:  # если есть ошибки парсинга
                print(f"Ошибка парсинга RSS: {feed.bozo_exception}")
                return []

            filtered_news = []
            for item in feed.entries:
                # Проверяем, не обрабатывали ли уже эту новость
                if item.link in self.seen_links:
                    continue

                title = item.get('title', '').lower()
                
                # Проверяем наличие ключевых слов в заголовке
                if any(keyword in title for keyword in self.keywords):
                    filtered_news.append({
                        'title': item.get('title', 'Без заголовка'),
                        'link': item.get('link', '#'),
                        'description': self.clean_description(item.get('description', '')),
                        'pubDate': item.get('pubDate', '')
                    })
                    self.seen_links.add(item.link)
            
            return filtered_news
            
        except Exception as e:
            print(f"Ошибка при парсинге RSS: {e}")
            return []

    def clean_description(self, description):
        """Очистка HTML-тегов из описания"""
        import re
        # Удаляем HTML теги
        clean = re.sub(r'<[^>]+>', '', description)
        # Заменяем множественные пробелы на один
        clean = re.sub(r'\s+', ' ', clean)
        # Обрезаем слишком длинные описания
        if len(clean) > 500:
            clean = clean[:497] + "..."
        return clean.strip()

    async def send_news_notification(self, news_item):
        """Отправка уведомления о новости пользователю"""
        message = (
            f"🔔 <b>Новость по ключевому слову!</b>\n\n"
            f"📌 <b>Заголовок:</b> {news_item['title']}\n\n"
            f"📝 <b>Описание:</b>\n{news_item['description']}\n\n"
            f"🔗 <b>Ссылка:</b> {news_item['link']}\n"
            f"📅 <b>Дата публикации:</b> {news_item['pubDate']}"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            print(f"Отправлено уведомление: {news_item['title']}")
        except TelegramAPIError as e:
            print(f"Ошибка отправки сообщения: {e}")

    async def run_background_task(self):
        """Фоновая задача для периодической проверки RSS"""
        print(f"Запущен фоновый парсер RSS. Проверка каждые {self.check_interval // 3600} часов")
        
        while True:
            print(f"[{datetime.now()}] Проверка RSS-ленты...")
            
            news_list = await self.parse_rss()
            
            if news_list:
                print(f"Найдено {len(news_list)} новых релевантных новостей")
                for news in news_list:
                    await self.send_news_notification(news)
            else:
                print("Новых релевантных новостей не найдено")
            
            # Ждем до следующей проверки
            await asyncio.sleep(self.check_interval)


# Функция для запуска фоновой задачи вместе с ботом
async def start_background_parser(bot: Bot, chat_id: int):
    """
    Запускает фоновый парсер RSS
    
    bot: экземпляр Bot
    chat_id: ID чата для уведомлений
    """
    parser = RSSParserBot(bot, chat_id)
    asyncio.create_task(parser.run_background_task())