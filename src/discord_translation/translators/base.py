from abc import ABC, abstractmethod

import requests


class BaseTranslator(ABC):
    def __init__(
        self,
        base_url: str,
        source: str = "auto",
        target: str = "en",
        **url_params,
    ):
        self._base_url = base_url
        self._supported_languages = self._get_supported_languages()
        self._source, self._target = self._map_language_to_code(source, target)
        super().__init__()

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, lang):
        self._source = lang

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, lang):
        self._target = lang

    def _map_language_to_code(self, *languages):
        return [
            self._supported_languages[lang] if lang != "auto" else "auto"
            for lang in languages
        ]

    @property
    def _same_source_target(self):
        return self._source == self._target

    def _get_supported_languages(self) -> dict:
        response = requests.get(f"{self._base_url}languages").json()
        supported = {}
        for lang in response:
            supported[lang.get("name")] = lang.get("code")
            supported[lang.get("code")] = lang.get("name")
        return supported

    def is_language_supported(self, language: str) -> bool:
        return language in [lang.name for lang in self._supported_languages]

    @abstractmethod
    def translate(self, text: str) -> str:
        return NotImplemented(
            "Translate must be implemented to be a valid translator. Duh."
        )

    def _translate_batch(self, batch: list[str]) -> list[str]:
        return [self.translate(text) for text in batch]
