from langchain_core.documents import Document
from langchain_unstructured import UnstructuredLoader
from unstructured.cleaners.core import clean
from unstructured.documents.elements import Text
from unstructured.partition.text import partition_text


class DocumentLoader(UnstructuredLoader):
    def __init__(self, **kwargs):
        """
        # TODO написать примеры
        chunking_strategy="basic",
        max_characters=1000000,
        """
        super().__init__(**kwargs)

    def __call__(self) -> list[Document]:
        docs = []
        for doc in self.lazy_load():
            docs.append(doc)
        return docs


class StringLoader:
    def __init__(self, cleaning_options=None):
        """
        Инициализация загрузчика
        
        :param cleaning_options: Словарь с опциями очистки текста
        """
        self.cleaning_options = cleaning_options or {
            "bullets": True,
            "extra_whitespace": True,
            "dashes": True,
            "trailing_punctuation": True
        }

    def load(self, text_string):
        """
        Загрузка и обработка текстовой строки
        
        :param text_string: Входная текстовая строка
        :return: Список обработанных текстовых элементов
        """
        # Применяем базовую очистку текста
        cleaned_text = clean(text_string, **self.cleaning_options)
        
        # Разбиваем текст на элементы
        elements = partition_text(text=cleaned_text)
        
        # Дополнительная обработка элементов
        processed_elements = []
        for element in elements:
            if isinstance(element, Text):
                processed_text = clean(element.text, **self.cleaning_options)
                processed_elements.append(Text(processed_text))
        
        return processed_elements

