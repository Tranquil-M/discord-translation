import os
import re
import time

import requests

from discord_translation.translators.base import BaseTranslator


class LibreTranslator(BaseTranslator):
    def __init__(
        self,
        source: str = "en",
        target: str = "es",
        api_key: str | None = os.getenv("LIBRE_API"),
        custom_url: str = "http://localhost:5000/",
    ):
        self.api_key = api_key
        super().__init__(
            base_url=custom_url.rstrip("/") + "/", source=source, target=target
        )

    def _fetch_translation(self, text: str) -> str:
        if self._same_source_target or not text:
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

        last_error = None
        for attempt in range(3):
            try:
                response = requests.post(
                    f"{self._base_url}translate",
                    data=params,
                    timeout=(10, 240),  # connect timeout, response timeout
                )
                response.raise_for_status()
                result = response.json()
                translated = result.get("translatedText")
                if not isinstance(translated, str):
                    raise ValueError(f"Unexpected LibreTranslate response: {result!r}")
                return translated
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1 * (2**attempt))

        raise RuntimeError("LibreTranslate failed after 3 attempts") from last_error

    def translate(self, text: str) -> str:
        print(text)
        return "".join(
            (
                part
                if re.fullmatch(
                    r"( ?<[^<>]*> ?|(?<!\w)(?:@everyone|@here|-#)(?!\w))", part
                )
                else self._fetch_translation(part)
            )
            for part in re.split(r"( ?<[^<>]*> ?)", text)
        )
