"""Load and persist RSS filter keywords from a text file."""

from collections.abc import Callable
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEYWORDS_PATH = _PROJECT_ROOT / "data" / "rss_keywords.txt"
DEFAULT_KEYWORDS_EXAMPLE = _PROJECT_ROOT / "data" / "rss_keywords.example.txt"


class KeywordsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_KEYWORDS_PATH
        self._on_change: Callable[[list[str]], None] | None = None

    def set_on_change(self, callback: Callable[[list[str]], None] | None) -> None:
        self._on_change = callback

    def _notify_change(self, keywords: list[str]) -> None:
        if self._on_change is not None:
            self._on_change(keywords)

    def reload(self) -> list[str]:
        """Read keywords from disk and notify subscribers (e.g. RSS parser)."""
        keywords = self.load()
        self._notify_change(keywords)
        return keywords

    def _ensure_keywords_file(self) -> None:
        if self.path.is_dir():
            raise RuntimeError(
                f"{self.path} is a directory, not a file. "
                "Remove it on the host and create data/rss_keywords.txt "
                "(copy from data/rss_keywords.example.txt)."
            )

        if self.path.exists():
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        if DEFAULT_KEYWORDS_EXAMPLE.exists():
            self.path.write_text(
                DEFAULT_KEYWORDS_EXAMPLE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            return

        raise RuntimeError(
            f"Keywords file not found: {self.path}. "
            "Create data/rss_keywords.txt with one keyword per line."
        )

    def load(self) -> list[str]:
        self._ensure_keywords_file()

        keywords: list[str] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            word = line.strip()
            if word and not word.startswith("#"):
                keywords.append(word)

        if not keywords:
            raise RuntimeError(
                f"Keywords file {self.path} must contain at least one keyword"
            )

        return keywords

    def save(self, keywords: list[str]) -> None:
        self._ensure_keywords_file()
        self.path.write_text(
            "\n".join(keywords) + "\n",
            encoding="utf-8",
        )

    def add(self, word: str) -> tuple[bool, str]:
        word = word.strip()
        if not word:
            return False, "Укажите слово после команды."

        keywords = self.load()
        if any(existing.lower() == word.lower() for existing in keywords):
            return False, f"Слово «{word}» уже есть в списке."

        keywords.append(word)
        self.save(keywords)
        self._notify_change(keywords)
        return True, f"Добавлено: «{word}». Всего слов: {len(keywords)}."

    def delete(self, word: str) -> tuple[bool, str]:
        word = word.strip()
        if not word:
            return False, "Укажите слово после команды."

        keywords = self.load()
        lowered = word.lower()
        match_index = next(
            (i for i, existing in enumerate(keywords) if existing.lower() == lowered),
            None,
        )
        if match_index is None:
            return False, f"Слово «{word}» не найдено в списке."

        if len(keywords) == 1:
            return False, "Нельзя удалить последнее ключевое слово."

        removed = keywords.pop(match_index)
        self.save(keywords)
        self._notify_change(keywords)
        return True, f"Удалено: «{removed}». Осталось слов: {len(keywords)}."
