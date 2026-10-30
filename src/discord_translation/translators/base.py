from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    def __init__(
        self,
        base_url: str,
        source: str = "auto",
        target: str = "en",
        **url_params,
    ):
        self._base_url = base_url
        self._supported_languages = _get_supported_languages()
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
        pass

    @property
    def _same_source_target(self):
        return self._source == self._target

    def _get_supported_languages(self) -> list | dict:
        pass

    def is_language_supported(self, language: str) -> bool:
        pass

    @abstractmethod
    def translate(self, text: str) -> str:
        return NotImplemented(
            "Translate must be implemented to be a valid translator. Duh."
        )

    def _translate_batch(self, batch: list[str]) -> list[str]:
        return [self.translate(text) for text in batch]
