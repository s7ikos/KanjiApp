import sqlite3
from typing import List, Optional
from entities import Kanji, Word


class DatabaseManager:
    """
    Класс для низкоуровневых операций с базой данных.

    Обеспечивает CRUD операции для кандзи и словаря без бизнес-логики.
    Все методы работают только с одной таблицей за раз.

    Attributes:
        db_name (str): Имя файла базы данных SQLite.
    """

    def __init__(self, db_name: str = "kanji.db") -> None:
        """
        Инициализирует менеджер базы данных.

        Args:
            db_name: Имя файла базы данных. По умолчанию "kanji.db".
        """
        self.db_name = db_name

    def initialize_database(self) -> None:
        """
        Инициализирует базу данных и создает таблицы если они не существуют.

        Создает следующие таблицы:
        - vocabulary: слова японского языка
        - kanji: иероглифы кандзи
        - kanji_variants: варианты написания кандзи
        - vocabulary_kanji: связь слов с кандзи
        - kanji_components: связь кандзи с компонентами

        Также создает индексы для ускорения поиска.
        """
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Таблица слов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    japanese TEXT NOT NULL,
                    reading TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    notes TEXT DEFAULT ''
                )
            ''')

            # Основная таблица кандзи
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kanji (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character TEXT UNIQUE NOT NULL,
                    meaning TEXT NOT NULL,
                    on_readings TEXT,
                    kun_readings TEXT,
                    jlpt_level INTEGER,
                    is_complex BOOLEAN DEFAULT TRUE,
                    notes TEXT DEFAULT ''
                )
            ''')

            # Таблица для вариантов написания
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kanji_variants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kanji_id INTEGER NOT NULL,
                    variant_form TEXT NOT NULL,
                    FOREIGN KEY (kanji_id) REFERENCES kanji (id) ON DELETE CASCADE
                )
            ''')

            # Связь слова с кандзи
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vocabulary_kanji (
                    vocabulary_id INTEGER NOT NULL,
                    kanji_id INTEGER NOT NULL,
                    PRIMARY KEY (vocabulary_id, kanji_id),
                    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary (id) ON DELETE CASCADE,
                    FOREIGN KEY (kanji_id) REFERENCES kanji (id) ON DELETE CASCADE
                )
            ''')

            # Таблица связи кандзи с его компонентами
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kanji_components (
                    kanji_id INTEGER NOT NULL,
                    component_id INTEGER NOT NULL,
                    PRIMARY KEY (kanji_id, component_id),
                    FOREIGN KEY (kanji_id) REFERENCES kanji (id) ON DELETE CASCADE,
                    FOREIGN KEY (component_id) REFERENCES kanji (id) ON DELETE CASCADE
                )
            ''')

            # Индексы для ускорения поиска
            conn.execute('CREATE INDEX IF NOT EXISTS idx_kanji_character ON kanji(character)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_vocabulary_japanese ON vocabulary(japanese)')

    def get_kanji_by_id(self, kanji_id: int) -> Optional[Kanji]:
        """
        Получает кандзи по его идентификатору.

        Args:
            kanji_id: Уникальный идентификатор кандзи.

        Returns:
            Объект Kanji если найден, иначе None.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM kanji WHERE id = ?', (kanji_id,))
            row = cursor.fetchone()
            if row:
                return Kanji(
                    id=row[0], character=row[1], meaning=row[2],
                    on_readings=row[3], kun_readings=row[4],
                    jlpt_level=row[5], is_complex=bool(row[6]), notes=row[7]
                )
            return None

    def get_kanji_by_character(self, character: str) -> Optional[Kanji]:
        """
        Получает кандзи по символу.

        Args:
            character: Символ кандзи для поиска.

        Returns:
            Объект Kanji если найден, иначе None.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM kanji WHERE character = ?', (character,))
            row = cursor.fetchone()
            if row:
                return Kanji(
                    id=row[0], character=row[1], meaning=row[2],
                    on_readings=row[3], kun_readings=row[4],
                    jlpt_level=row[5], is_complex=bool(row[6]), notes=row[7]
                )
            return None

    def search_kanji_basic(self, query: str) -> List[Kanji]:
        """
        Выполняет базовый поиск кандзи по различным полям.

        Ищет совпадения в:
        - точном совпадении символа
        - частичном совпадении в значении
        - частичном совпадении в он-чтениях
        - частичном совпадении в кун-чтениях
        - уровне JLPT (если запрос число)

        Args:
            query: Строка поискового запроса.

        Returns:
            Список объектов Kanji, удовлетворяющих запросу.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM kanji
                WHERE character = ? 
                   OR meaning LIKE ? 
                   OR on_readings LIKE ? 
                   OR kun_readings LIKE ?
                   OR jlpt_level = ?
            ''', (query, f"%{query}%", f"%{query}%", f"%{query}%",
                  query if query.isdigit() else -1))

            results = []
            for row in cursor.fetchall():
                kanji = Kanji(
                    id=row[0], character=row[1], meaning=row[2],
                    on_readings=row[3], kun_readings=row[4],
                    jlpt_level=row[5], is_complex=bool(row[6]), notes=row[7]
                )
                results.append(kanji)
            return results

    def search_vocabulary_basic(self, query: str) -> List[Word]:
        """
        Выполняет базовый поиск слов по различным полям.

        Ищет совпадения в:
        - японском написании
        - чтении (ромадзи)
        - переводе

        Args:
            query: Строка поискового запроса.

        Returns:
            Список объектов Word, удовлетворяющих запросу.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, japanese, reading, translation, notes
                FROM vocabulary
                WHERE japanese LIKE ? 
                   OR reading LIKE ?
                   OR translation LIKE ?
            ''', (f"%{query}%", f"%{query}%", f"%{query}%"))

            results = []
            for row in cursor.fetchall():
                word = Word(
                    id=row[0], japanese=row[1], reading=row[2],
                    translation=row[3], notes=row[4]
                )
                results.append(word)
            return results

    def add_kanji(self, kanji: Kanji) -> Optional[int]:
        """
        Добавляет новое кандзи в базу данных.

        Args:
            kanji: Объект Kanji с данными для добавления.

        Returns:
            ID добавленного кандзи в случае успеха, иначе None.

        Raises:
            sqlite3.IntegrityError: Если кандзи с таким символом уже существует.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO kanji (character, meaning, on_readings, kun_readings,
                                     jlpt_level, is_complex, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (kanji.character, kanji.meaning, kanji.on_readings,
                      kanji.kun_readings, kanji.jlpt_level,
                      kanji.is_complex, kanji.notes))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"Ошибка при добавлении кандзи: {e}")
            return None

    def update_kanji(self, kanji: Kanji) -> bool:
        """
        Обновляет данные существующего кандзи.

        Args:
            kanji: Объект Kanji с обновленными данными (должен содержать id).

        Returns:
            True если обновление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE kanji
                    SET character = ?, meaning = ?, on_readings = ?, kun_readings = ?,
                        jlpt_level = ?, is_complex = ?, notes = ?
                    WHERE id = ?
                ''', (kanji.character, kanji.meaning, kanji.on_readings,
                      kanji.kun_readings, kanji.jlpt_level,
                      kanji.is_complex, kanji.notes, kanji.id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении кандзи: {e}")
            return False

    def delete_kanji(self, kanji_id: int) -> bool:
        """
        Удаляет кандзи из базы данных по идентификатору.

        Args:
            kanji_id: ID кандзи для удаления.

        Returns:
            True если удаление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM kanji WHERE id = ?', (kanji_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при удалении кандзи: {e}")
            return False

    def get_word_by_id(self, word_id: int) -> Optional[Word]:
        """
        Получает слово по его идентификатору.

        Args:
            word_id: Уникальный идентификатор слова.

        Returns:
            Объект Word если найден, иначе None.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM vocabulary WHERE id = ?', (word_id,))
            row = cursor.fetchone()
            if row:
                return Word(
                    id=row[0], japanese=row[1], reading=row[2],
                    translation=row[3], notes=row[4]
                )
            return None

    def add_vocabulary(self, word: Word) -> Optional[int]:
        """
        Добавляет новое слово в базу данных.

        Args:
            word: Объект Word с данными для добавления.

        Returns:
            ID добавленного слова в случае успеха, иначе None.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO vocabulary (japanese, reading, translation, notes)
                    VALUES (?, ?, ?, ?)
                ''', (word.japanese, word.reading, word.translation, word.notes))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка при добавлении слова: {e}")
            return None

    def update_vocabulary(self, word: Word) -> bool:
        """
        Обновляет данные существующего слова.

        Args:
            word: Объект Word с обновленными данными (должен содержать id).

        Returns:
            True если обновление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE vocabulary
                    SET japanese = ?, reading = ?, translation = ?, notes = ?
                    WHERE id = ?
                ''', (word.japanese, word.reading, word.translation, word.notes, word.id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении слова: {e}")
            return False

    def delete_vocabulary(self, word_id: int) -> bool:
        """
        Удаляет слово из базы данных по идентификатору.

        Args:
            word_id: ID слова для удаления.

        Returns:
            True если удаление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM vocabulary WHERE id = ?', (word_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при удалении слова: {e}")
            return False

    def get_kanji_variants(self, kanji_id: int) -> List[str]:
        """
        Получает варианты написания кандзи.

        Args:
            kanji_id: ID кандзи для которого ищутся варианты.

        Returns:
            Список строк с вариантами написания.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT variant_form FROM kanji_variants WHERE kanji_id = ?', (kanji_id,))
            return [row[0] for row in cursor.fetchall()]

    def add_kanji_variant(self, kanji_id: int, variant_form: str) -> bool:
        """
        Добавляет вариант написания для кандзи.

        Args:
            kanji_id: ID кандзи.
            variant_form: Вариант написания символа.

        Returns:
            True если добавление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO kanji_variants (kanji_id, variant_form)
                    VALUES (?, ?)
                ''', (kanji_id, variant_form))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении варианта: {e}")
            return False

    def delete_kanji_variants(self, kanji_id: int) -> bool:
        """
        Удаляет все варианты написания для указанного кандзи.

        Args:
            kanji_id: ID кандзи, варианты которого нужно удалить.

        Returns:
            True если удаление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM kanji_variants WHERE kanji_id = ?', (kanji_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при удалении вариантов: {e}")
            return False

    def get_kanji_components(self, kanji_id: int) -> List[Kanji]:
        """
        Получает компоненты (радикалы) из которых состоит кандзи.

        Args:
            kanji_id: ID сложного кандзи.

        Returns:
            Список объектов Kanji, являющихся компонентами.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT k.* FROM kanji k
                JOIN kanji_components kc ON k.id = kc.component_id
                WHERE kc.kanji_id = ?
            ''', (kanji_id,))

            components = []
            for row in cursor.fetchall():
                kanji = Kanji(
                    id=row[0], character=row[1], meaning=row[2],
                    on_readings=row[3], kun_readings=row[4],
                    jlpt_level=row[5], is_complex=bool(row[6]), notes=row[7]
                )
                components.append(kanji)
            return components

    def add_kanji_component(self, kanji_id: int, component_id: int) -> bool:
        """
        Добавляет связь между кандзи и его компонентом.

        Args:
            kanji_id: ID сложного кандзи.
            component_id: ID компонента-радикала.

        Returns:
            True если связь добавлена успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO kanji_components (kanji_id, component_id)
                    VALUES (?, ?)
                ''', (kanji_id, component_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении компонента: {e}")
            return False

    def delete_kanji_components(self, kanji_id: int) -> bool:
        """
        Удаляет все компоненты для указанного кандзи.

        Args:
            kanji_id: ID кандзи, компоненты которого нужно удалить.

        Returns:
            True если удаление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM kanji_components WHERE kanji_id = ?', (kanji_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при удалении компонентов: {e}")
            return False

    def get_word_kanji(self, word_id: int) -> List[Kanji]:
        """
        Получает кандзи, входящие в состав слова.

        Args:
            word_id: ID слова.

        Returns:
            Список объектов Kanji, используемых в слове.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT k.* FROM kanji k
                JOIN vocabulary_kanji vk ON k.id = vk.kanji_id
                WHERE vk.vocabulary_id = ?
            ''', (word_id,))

            kanji_list = []
            for row in cursor.fetchall():
                kanji = Kanji(
                    id=row[0], character=row[1], meaning=row[2],
                    on_readings=row[3], kun_readings=row[4],
                    jlpt_level=row[5], is_complex=bool(row[6]), notes=row[7]
                )
                kanji_list.append(kanji)
            return kanji_list

    def add_vocabulary_kanji(self, word_id: int, kanji_id: int) -> bool:
        """
        Добавляет связь между словом и кандзи.

        Args:
            word_id: ID слова.
            kanji_id: ID кандзи.

        Returns:
            True если связь добавлена успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO vocabulary_kanji (vocabulary_id, kanji_id)
                    VALUES (?, ?)
                ''', (word_id, kanji_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении связи слова с кандзи: {e}")
            return False

    def delete_vocabulary_kanji(self, word_id: int) -> bool:
        """
        Удаляет все связи слова с кандзи.

        Args:
            word_id: ID слова, связи которого нужно удалить.

        Returns:
            True если удаление прошло успешно, иначе False.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM vocabulary_kanji WHERE vocabulary_id = ?', (word_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при удалении связей слова: {e}")
            return False

    def update_notes(self, item_id: int, new_notes: str, is_kanji: bool) -> bool:
        """
        Обновляет поле заметок для кандзи или слова.

        Args:
            item_id: ID элемента (кандзи или слова).
            new_notes: Новый текст заметки.
            is_kanji: True если элемент - кандзи, False если слово.

        Returns:
            True если обновление прошло успешно, иначе False.
        """
        table_name = "kanji" if is_kanji else "vocabulary"
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE {table_name} SET notes = ? WHERE id = ?
                ''', (new_notes, item_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении заметок: {e}")
            return False
