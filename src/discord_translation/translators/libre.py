import os

import requests

from discord_translation.translators.base import BaseTranslator


class LibreTranslator(BaseTranslator):
    def __init__(
        self,
        source: str = "en",
        target: str = "es",
        api_key: str | None = os.getenv("LIBRE_API", None),
        custom_url: str = "libretranslator.de/",
    ):
        self.api_key = api_key
        super().__init__(
            base_url=custom_url,
            source=source,
            target=target,
        )

    def translate(self, text: str) -> str:
        if self._same_source_target or len(text) <= 0:
            return text

        params = {
            "q": text,
            "source": self._source,
            "target": self._target,
            "format": "text",
            "alternatives": 0,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        response = requests.post(f"{self._base_url}translate", data=params)

        if response.status_code == 403:
            raise ValueError("You must provide and API key to use this service.")

        res = response.json()
        if not res:
            return ""

        return res["translatedText"]

    def translate_batch(self, batch: list[str]) -> list[str]:
        return [self.translate(text) for text in batch]
