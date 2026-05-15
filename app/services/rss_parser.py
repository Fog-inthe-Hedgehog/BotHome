import asyncio
import html
import re
from dataclasses import dataclass

import feedparser
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.logger import logger
from app.settings import Settings


@dataclass
class NewsItem:
    title: str
    link: str
    description: str
    pub_date: str


class RSSParserBot:
    def __init__(self, bot: Bot, chat_id: int, settings: Settings) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self.settings = settings
        self.keywords = [keyword.lower() for keyword in settings.rss_keywords]
        self.check_interval = settings.check_interval_hours * 3600
        self.seen_links: set[str] = set()
        self.rss_url = settings.rss_url

    async def warm_up(self) -> int:
        """Mark all current feed entries as seen without sending notifications."""
        feed = await self._fetch_feed()
        marked = 0

        for item in feed.entries:
            link = item.get("link")
            if not link or link in self.seen_links:
                continue
            self.seen_links.add(link)
            marked += 1

        logger.info("RSS warm-up completed: {} links marked as seen", marked)
        return marked

    async def _fetch_feed(self):
        feed = await asyncio.to_thread(feedparser.parse, self.rss_url)

        if feed.bozo:
            logger.warning("RSS parse warning: {}", feed.bozo_exception)

        if not getattr(feed, "entries", None):
            logger.warning("RSS feed has no entries: {}", self.rss_url)

        return feed

    def _matches_keywords(self, item) -> bool:
        title = item.get("title", "").lower()
        description = self.clean_description(item.get("description", "")).lower()
        text = f"{title} {description}"
        return any(keyword in text for keyword in self.keywords)

    async def parse_rss(self) -> list[NewsItem]:
        try:
            feed = await self._fetch_feed()
            filtered_news: list[NewsItem] = []

            for item in feed.entries:
                link = item.get("link")
                if not link or link in self.seen_links:
                    continue

                if not self._matches_keywords(item):
                    continue

                filtered_news.append(
                    NewsItem(
                        title=item.get("title", "Без заголовка"),
                        link=link,
                        description=self.clean_description(
                            item.get("description", "")
                        ),
                        pub_date=item.get("published", item.get("pubDate", "")),
                    )
                )
                self.seen_links.add(link)

            return filtered_news

        except Exception:
            logger.exception("Failed to parse RSS feed")
            return []

    def clean_description(self, description: str) -> str:
        clean = re.sub(r"<[^>]+>", "", description)
        clean = re.sub(r"\s+", " ", clean)
        if len(clean) > 500:
            clean = clean[:497] + "..."
        return clean.strip()

    async def send_news_notification(self, news_item: NewsItem) -> None:
        message = (
            "🔔 <b>Новость по ключевому слову!</b>\n\n"
            f"📌 <b>Заголовок:</b> {html.escape(news_item.title)}\n\n"
            f"📝 <b>Описание:</b>\n{html.escape(news_item.description)}\n\n"
            f'🔗 <b>Ссылка:</b> <a href="{html.escape(news_item.link, quote=True)}">'
            f"{html.escape(news_item.link)}</a>\n"
            f"📅 <b>Дата публикации:</b> {html.escape(news_item.pub_date)}"
        )

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML",
            )
            logger.info("Notification sent: {}", news_item.title)
        except TelegramAPIError:
            logger.exception("Failed to send notification")

    async def check_and_notify(self) -> int:
        news_list = await self.parse_rss()

        if not news_list:
            logger.info("No new relevant news found")
            return 0

        logger.info("Found {} new relevant news items", len(news_list))
        for news in news_list:
            await self.send_news_notification(news)

        return len(news_list)

    async def run_background_task(self) -> None:
        logger.info(
            "Background RSS parser started (interval: {} h)",
            self.settings.check_interval_hours,
        )

        while True:
            await self.check_and_notify()
            await asyncio.sleep(self.check_interval)


def start_background_parser(parser: RSSParserBot) -> asyncio.Task[None]:
    return asyncio.create_task(parser.run_background_task())
