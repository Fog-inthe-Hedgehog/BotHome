import asyncio
import html
import re
import urllib.request
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
    def __init__(
        self,
        bot: Bot,
        chat_id: int,
        settings: Settings,
        keywords: list[str],
    ) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self.settings = settings
        self.set_keywords(keywords)
        self.check_interval = settings.check_interval_hours * 3600
        self.seen_links: set[str] = set()
        self.rss_url = settings.rss_url

    def set_keywords(self, keywords: list[str]) -> None:
        self.keywords = [keyword.lower() for keyword in keywords]

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

    def _entry_search_text(self, item) -> str:
        title = item.get("title", "").lower()
        description = self.clean_description(item.get("description", "")).lower()
        return f"{title} {description}"

    def _matching_keywords(self, item) -> list[str]:
        text = self._entry_search_text(item)
        return [keyword for keyword in self.keywords if keyword in text]

    def _matches_keywords(self, item) -> bool:
        return bool(self._matching_keywords(item))

    async def _fetch_raw_rss(self) -> str:
        def fetch() -> str:
            with urllib.request.urlopen(self.rss_url, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")

        return await asyncio.to_thread(fetch)

    async def _log_feed_debug(self, feed, *, ignore_seen: bool = False) -> None:
        if not self.settings.debug:
            return

        logger.debug("RSS debug: url={}", self.rss_url)
        logger.debug("RSS debug: active keywords={}", self.keywords)
        logger.debug("RSS debug: seen links in memory={}", len(self.seen_links))
        logger.debug("RSS debug: ignore_seen={}", ignore_seen)

        try:
            raw = await self._fetch_raw_rss()
            preview = raw if len(raw) <= 12000 else raw[:12000] + "\n... [truncated]"
            logger.debug(
                "RSS debug: raw response ({} bytes):\n{}",
                len(raw),
                preview,
            )
        except Exception:
            logger.exception("RSS debug: failed to fetch raw feed body")

        entries = getattr(feed, "entries", None) or []
        logger.debug("RSS debug: parsed entries={}", len(entries))

        for index, item in enumerate(entries, start=1):
            link = item.get("link", "")
            title = item.get("title", "")
            matched = self._matching_keywords(item)
            seen = bool(link and link in self.seen_links)
            description_preview = self.clean_description(item.get("description", ""))[:200]

            logger.debug(
                "RSS debug: entry {} title={!r} link={!r} seen={} "
                "keywords={} description_preview={!r}",
                index,
                title,
                link,
                seen,
                matched or "—",
                description_preview,
            )

    async def parse_rss(self, *, ignore_seen: bool = False) -> list[NewsItem]:
        try:
            feed = await self._fetch_feed()
            await self._log_feed_debug(feed, ignore_seen=ignore_seen)
            filtered_news: list[NewsItem] = []

            for item in feed.entries:
                link = item.get("link")
                if not link:
                    if self.settings.debug:
                        logger.debug(
                            "RSS debug: skip entry without link: {!r}",
                            item.get("title", ""),
                        )
                    continue

                if not ignore_seen and link in self.seen_links:
                    if self.settings.debug:
                        logger.debug("RSS debug: skip seen link: {}", link)
                    continue

                if ignore_seen and link in self.seen_links and self.settings.debug:
                    logger.debug("RSS debug: seen link ignored for check: {}", link)

                if not self._matches_keywords(item):
                    if self.settings.debug:
                        logger.debug(
                            "RSS debug: skip no keyword match: {} ({!r})",
                            link,
                            item.get("title", ""),
                        )
                    continue

                if self.settings.debug:
                    logger.debug(
                        "RSS debug: matched new entry: {} keywords={} title={!r}",
                        link,
                        self._matching_keywords(item),
                        item.get("title", ""),
                    )

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

    async def check_and_notify(self, *, ignore_seen: bool = False) -> int:
        news_list = await self.parse_rss(ignore_seen=ignore_seen)

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
