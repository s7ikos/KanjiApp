from typing import List, Optional
from database import DatabaseManager
from entities import Kanji, Word, KanjiComponent


class KanjiController:
    """
    Контроллер для бизнес-логики приложения.
    Координирует сложные операции, используя DatabaseManager.
    """

    def __init__(self, db_name: str = "kanji.db"):
        self.db_name = db_name
        self.db_manager = DatabaseManager(db_name)

    def search_kanji(self, query: str) -> List[Kanji]:
        """Поиск кандзи"""
        return self.db_manager.search_kanji_basic(query)

    def search_vocabulary(self, query: str) -> List[Word]:
        """Поиск слов"""
        return self.db_manager.search_vocabulary_basic(query)

    def get_kanji_info(self, kanji_id: int) -> Optional[Kanji]:
        """
        Получить полную информацию о кандзи.
        Собирает данные из нескольких таблиц.
        """
        # 1. Получаем базовую информацию о кандзи
        kanji = self.db_manager.get_kanji_by_id(kanji_id)
        if not kanji:
            return None

        # 2. Получаем варианты написания
        variants = self.db_manager.get_kanji_variants(kanji_id)
        kanji.variations = variants

        # 3. Если кандзи сложный, получаем компоненты
        if kanji.is_complex:
            components = self.db_manager.get_kanji_components(kanji_id)
            # Преобразуем в KanjiComponent объекты
            for component in components:
                # Получаем вариант написания для этого компонента в контексте текущего кандзи
                component_variants = self.db_manager.get_kanji_variants(component.id)
                variant_form = component_variants[0] if component_variants else None

                component_info = KanjiComponent(kanji=component, variant_form=variant_form)
                kanji.radicals.append(component_info)

        return kanji

    def get_word_info(self, word_id: int) -> Optional[Word]:
        """Получить полную информацию о слове с кандзи"""
        word = self.db_manager.get_word_by_id(word_id)
        if not word:
            return None

        # Получаем связанные кандзи
        kanji_list = self.db_manager.get_word_kanji(word_id)
        word.kanji_vocabulary = kanji_list

        return word

    def add_kanji_with_details(self, kanji_obj: Kanji, variants: List[str] = None,
                               components: List[str] = None) -> Optional[int]:
        """
        Добавить кандзи со всеми деталями (бизнес-логика).
        Координирует несколько операций с БД.
        """
        try:
            # 1. Добавляем основное кандзи
            kanji_id = self.db_manager.add_kanji(kanji_obj)
            if not kanji_id:
                return None

            # 2. Добавляем варианты написания
            if variants:
                for variant in variants:
                    self.db_manager.add_kanji_variant(kanji_id, variant)

            # 3. Добавляем компоненты
            if components and kanji_obj.is_complex:
                for char in components:
                    component_kanji = self.db_manager.get_kanji_by_character(char)
                    if component_kanji:
                        self.db_manager.add_kanji_component(kanji_id, component_kanji.id)

            return kanji_id

        except Exception as e:
            print(f"Ошибка при добавлении кандзи с деталями: {e}")
            return None

    def add_vocabulary_with_details(self, word_obj: Word, kanji_chars: List[str] = None) -> Optional[int]:
        """Добавить слово со связанными кандзи"""
        try:
            # 1. Добавляем слово
            word_id = self.db_manager.add_vocabulary(word_obj)
            if not word_id:
                return None

            # 2. Связываем с кандзи
            if kanji_chars:
                for char in kanji_chars:
                    kanji = self.db_manager.get_kanji_by_character(char)
                    if kanji:
                        self.db_manager.add_vocabulary_kanji(word_id, kanji.id)

            return word_id

        except Exception as e:
            print(f"Ошибка при добавлении слова с деталями: {e}")
            return None

    def update_kanji_full(self, kanji_obj: Kanji, new_variants: List[str] = None,
                          new_components: List[str] = None) -> bool:
        """
        Полное обновление кандзи со всеми связями.
        Бизнес-логика: атомарное обновление.
        """
        try:
            # 1. Обновляем основную информацию
            if not self.db_manager.update_kanji(kanji_obj):
                return False

            # 2. Обновляем варианты написания
            if new_variants is not None:  # None означает "не обновлять"
                self.db_manager.delete_kanji_variants(kanji_obj.id)
                for variant in new_variants:
                    self.db_manager.add_kanji_variant(kanji_obj.id, variant)

            # 3. Обновляем компоненты
            if new_components is not None and kanji_obj.is_complex:
                self.db_manager.delete_kanji_components(kanji_obj.id)
                for char in new_components:
                    component_kanji = self.db_manager.get_kanji_by_character(char)
                    if component_kanji:
                        self.db_manager.add_kanji_component(kanji_obj.id, component_kanji.id)

            return True

        except Exception as e:
            print(f"Ошибка при полном обновлении кандзи: {e}")
            return False

    def update_vocabulary_full(self, word_obj: Word, new_kanji_chars: List[str] = None) -> bool:
        """Полное обновление слова со связями"""
        try:
            # 1. Обновляем основную информацию
            if not self.db_manager.update_vocabulary(word_obj):
                return False

            # 2. Обновляем связанные кандзи
            if new_kanji_chars is not None:
                self.db_manager.delete_vocabulary_kanji(word_obj.id)
                for char in new_kanji_chars:
                    kanji = self.db_manager.get_kanji_by_character(char)
                    if kanji:
                        self.db_manager.add_vocabulary_kanji(word_obj.id, kanji.id)

            return True

        except Exception as e:
            print(f"Ошибка при полном обновлении слова: {e}")
            return False

    def delete_kanji_cascade(self, kanji_id: int) -> bool:
        """Удалить кандзи и все его связи."""
        # Проверка на то используется ли кандзи в словах
        word_usage = self.db_manager.get_word_kanji(kanji_id)
        if word_usage:
            print(f"Предупреждение: кандзи используется в {len(word_usage)} словах")

        return self.db_manager.delete_kanji(kanji_id)

    def delete_vocabulary_cascade(self, word_id: int) -> bool:
        """Удалить слово и все его связи"""
        return self.db_manager.delete_vocabulary(word_id)

    def update_notes(self, item_id: int, new_notes: str, is_kanji: bool) -> bool:
        """Обновить заметки"""
        return self.db_manager.update_notes(item_id, new_notes, is_kanji)

    def get_kanji_by_character(self, character: str) -> Optional[Kanji]:
        """Получить кандзи по символу (с возможностью кэширования)"""
        return self.db_manager.get_kanji_by_character(character)