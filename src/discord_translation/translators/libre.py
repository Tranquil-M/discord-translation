import os

import requests

from discord_translation.base import BaseTranslator


class LibreTranslator(BaseTranslator):
    def __init__(
        self,
        source: str = "en",
        target: str = "es",
        api_key: str | None = os.getenv("LIBRE_API", None),
        use_free_api: bool = True,
        custom_url: str | None = "localhost:5000/",
    ):
        if not api_key and not use_free_api:
            raise ValueError(
                "An API key must be provided to use paid versions of Libre Translate"
            )

        self.api_key = api_key
        super().__init__(
            base_url=custom_url,
            source=source,
            target=target,
        )

    def translate(self, text: str, **kwargs) -> str:
        if self._same_source_target() or not text:
            return text

        translate_endpoint = "translate"
        params = {
            "q": text,
            "source": self._source,
            "target": self._target,
            "format": "text",
            "alternatives": 0,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        response = requests.post(self._base_url + translate_endpoint, params=params)

        res = response.json()
        if not res:
            return ""

        return res["translatedText"]
