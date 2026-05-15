"""Load and persist RSS filter keywords from a text file."""

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEYWORDS_PATH = _PROJECT_ROOT / "rss_keywords.txt"


class KeywordsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_KEYWORDS_PATH

    def load(self) -> list[str]:
        if not self.path.exists():
            raise RuntimeError(
                f"Keywords file not found: {self.path}. "
                "Create rss_keywords.txt with one keyword per line."
            )

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
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
        return True, f"Удалено: «{removed}». Осталось слов: {len(keywords)}."
