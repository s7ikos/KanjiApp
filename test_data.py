# test_data.py
import sqlite3
import os
from database import DatabaseManager
from entities import Kanji, Word
from controller import KanjiController


def populate_sample_data():
    """
    Заполняет базу данных тестовыми данными для демонстрации работы приложения.
    Запустите этот файл двойным кликом чтобы добавить тестовые данные в базу.
    """
    print("=== ДОБАВЛЕНИЕ ТЕСТОВЫХ ДАННЫХ ===")

    # Инициализация базы данных
    db = DatabaseManager("kanji.db")
    db.initialize_database()
    controller = KanjiController("kanji.db")

    print("1. Добавление базовых кандзи...")

    # Базовые кандзи (радикалы) - ВКЛЮЧАЕМ "言" который отсутствовал
    basic_kanji = [
        ("一", "one", "イチ, イツ", "ひと-, ひと.つ", 5, False),
        ("二", "two", "ニ", "ふた, ふた.つ, ふたた.び", 5, False),
        ("三", "three", "サン", "み, み.つ, みっ.つ", 5, False),
        ("人", "person", "ジン, ニン", "ひと, -り, -と", 5, False),
        ("口", "mouth", "コウ, ク", "くち", 5, False),
        ("日", "day, sun", "ニチ, ジツ", "ひ, -び, -か", 5, False),
        ("月", "moon, month", "ゲツ, ガツ", "つき", 5, False),
        ("火", "fire", "カ", "ひ, -び, ほ-", 5, False),
        ("水", "water", "スイ", "みず", 5, False),
        ("木", "tree", "ボク, モク", "き, こ-", 5, False),
        ("金", "gold, money", "キン, コン", "かね, かな-", 5, False),
        ("土", "earth", "ド, ト", "つち", 5, False),
        ("大", "big", "ダイ, タイ", "おお-, おお.きい, -おお.いに", 5, False),
        ("小", "small", "ショウ", "ちい.さい, こ-, お-", 5, False),
        ("中", "middle", "チュウ", "なか, うち, あた.る", 5, False),
        ("言", "speech, word", "ゲン, ゴン", "い.う, こと", 3, False),  # ДОБАВЛЕНО!
        ("五", "five", "ゴ", "いつ, いつ.つ", 5, False),  # ДОБАВЛЕНО!
    ]

    kanji_ids = {}
    for char, meaning, on_read, kun_read, level, is_complex in basic_kanji:
        kanji = Kanji(character=char, meaning=meaning, on_readings=on_read,
                      kun_readings=kun_read, jlpt_level=level, is_complex=is_complex)
        kanji_id = db.add_kanji(kanji)
        kanji_ids[char] = kanji_id

    print(f"   Добавлено {len(basic_kanji)} базовых кандзи")

    # Сложные кандзи
    print("2. Добавление сложных кандзи...")

    complex_kanji = [
        ("語", "language, word", "ゴ", "かた.る, かた.らう", 3, True),
        ("休", "rest", "キュウ", "やす.む, やす.まる, やす.める", 4, True),
        ("明", "bright", "メイ, ミョウ", "あ.かり, あ.かるい, あ.かるむ, あ.からむ", 4, True),
        ("校", "school", "コウ", None, 4, True),
        ("生", "life", "セイ, ショウ", "い.きる, い.かす, い.ける, う.まれる", 4, True),
        ("年", "year", "ネン", "とし", 5, True),
        ("食", "eat", "ショク, ジキ", "く.う, く.らう, た.べる", 4, True),
        ("飲", "drink", "イン", "の.む", 4, True),
        ("車", "car", "シャ", "くるま", 4, True),
        ("電", "electricity", "デン", None, 4, True),
        ("本", "book, origin", "ホン", "もと", 5, True),  # ДОБАВЛЕНО!
    ]

    for char, meaning, on_read, kun_read, level, is_complex in complex_kanji:
        kanji = Kanji(character=char, meaning=meaning, on_readings=on_read,
                      kun_readings=kun_read, jlpt_level=level, is_complex=is_complex)
        kanji_id = db.add_kanji(kanji)
        kanji_ids[char] = kanji_id

    print(f"   Добавлено {len(complex_kanji)} сложных кандзи")

    # Установка связей между кандзи
    print("3. Установка связей между кандзи...")

    # 語 = 言 + 五 + 口 (теперь все эти кандзи есть в basic_kanji)
    db.add_kanji_component(kanji_ids["語"], kanji_ids["言"])
    db.add_kanji_component(kanji_ids["語"], kanji_ids["五"])
    db.add_kanji_component(kanji_ids["語"], kanji_ids["口"])
    print("   Установлены связи для 語: 言, 五, 口")

    # 休 = 人 + 木
    db.add_kanji_component(kanji_ids["休"], kanji_ids["人"])
    db.add_kanji_component(kanji_ids["休"], kanji_ids["木"])
    print("   Установлены связи для 休: 人, 木")

    # 明 = 日 + 月
    db.add_kanji_component(kanji_ids["明"], kanji_ids["日"])
    db.add_kanji_component(kanji_ids["明"], kanji_ids["月"])
    print("   Установлены связи для 明: 日, 月")

    # 校 = 木 + 交
    # Сначала добавим 交 если его нет
    if "交" not in kanji_ids:
        kanji_交 = Kanji(character="交", meaning="mix, exchange", on_readings="コウ",
                         kun_readings="まじ.わる, まじ.える", jlpt_level=2, is_complex=False)
        kanji_id_交 = db.add_kanji(kanji_交)
        kanji_ids["交"] = kanji_id_交
        print("   Добавлен кандзи 交")

    db.add_kanji_component(kanji_ids["校"], kanji_ids["木"])
    db.add_kanji_component(kanji_ids["校"], kanji_ids["交"])
    print("   Установлены связи для 校: 木, 交")

    print("   Все связи между кандзи установлены")

    # Добавление вариантов написания
    print("4. Добавление вариантов написания...")

    variant_data = [
        ("人", "亻"),  # Вариант человека как радикала
        ("水", "氵"),  # Вариант воды как радикала
        ("言", "訁"),  # Вариант речи как радикала
        ("言", "讠"),  # Упрощенный китайский вариант
        ("食", "飠"),  # Вариант еды как радикала
        ("食", "饣"),  # Упрощенный китайский вариант
    ]

    for kanji_char, variant in variant_data:
        if kanji_char in kanji_ids:
            db.add_kanji_variant(kanji_ids[kanji_char], variant)
            print(f"   Добавлен вариант {variant} для {kanji_char}")

    print("   Все варианты написания добавлены")

    # Добавление словарного запаса
    print("5. Добавление слов...")

    vocabulary_data = [
        # Базовые слова
        ("一", "いち", "один"),
        ("二", "に", "два"),
        ("三", "さん", "три"),
        ("人", "ひと", "человек"),
        ("口", "くち", "рот"),
        ("日", "ひ", "день, солнце"),
        ("月", "つき", "луна, месяц"),
        ("火", "ひ", "огонь"),
        ("水", "みず", "вода"),
        ("木", "き", "дерево"),
        ("言う", "いう", "говорить"),
        ("五", "ご", "пять"),

        # Сложные слова
        ("日本語", "にほんご", "японский язык"),
        ("休む", "やすむ", "отдыхать"),
        ("明日", "あした", "завтра"),
        ("学校", "がっこう", "школа"),
        ("学生", "がくせい", "студент"),
        ("一年", "いちねん", "один год"),
        ("食べる", "たべる", "есть (кушать)"),
        ("飲む", "のむ", "пить"),
        ("車", "くるま", "машина"),
        ("電気", "でんき", "электричество"),
        ("本", "ほん", "книга"),

        # Дополнительные слова
        ("大きい", "おおきい", "большой"),
        ("小さい", "ちいさい", "маленький"),
        ("中", "なか", "середина"),
        ("金", "きん", "золото, деньги"),
        ("土", "つち", "земля"),
    ]

    word_kanji_associations = {
        "日本語": ["日", "本", "語"],
        "休む": ["休"],
        "明日": ["明", "日"],
        "学校": ["学", "校"],
        "学生": ["学", "生"],
        "一年": ["一", "年"],
        "食べる": ["食"],
        "飲む": ["飲"],
        "大きい": ["大"],
        "小さい": ["小"],
        "電気": ["電", "気"],
        "言う": ["言"],
    }

    # Добавим недостающие кандзи для слов
    missing_kanji = {
        "学": ("学", "study", "ガク", "まな.ぶ", 5, True),
        "気": ("気", "spirit", "キ, ケ", "いき", 4, True),
    }

    for char, data in missing_kanji.items():
        if char not in kanji_ids:
            kanji = Kanji(character=data[0], meaning=data[1], on_readings=data[2],
                          kun_readings=data[3], jlpt_level=data[4], is_complex=data[5])
            kanji_id = db.add_kanji(kanji)
            kanji_ids[char] = kanji_id
            print(f"   Добавлен недостающий кандзи: {char}")

    vocabulary_ids = {}
    for japanese, reading, translation in vocabulary_data:
        word = Word(japanese=japanese, reading=reading, translation=translation)
        vocab_id = db.add_vocabulary(word)
        vocabulary_ids[japanese] = vocab_id

        # Связываем слово с кандзи
        if japanese in word_kanji_associations:
            for kanji_char in word_kanji_associations[japanese]:
                if kanji_char in kanji_ids:
                    db.add_vocabulary_kanji(vocab_id, kanji_ids[kanji_char])
        else:
            # Для однокандзиевых слов связываем с соответствующим кандзи
            for char in japanese:
                if char in kanji_ids:
                    db.add_vocabulary_kanji(vocab_id, kanji_ids[char])

    print(f"   Добавлено {len(vocabulary_data)} слов")

    print("\n=== ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО ДОБАВЛЕНЫ ===")
    print("Теперь вы можете запустить основное приложение для работы с данными.")

    # Небольшая демонстрация что данные работают
    print("\n--- ДЕМОНСТРАЦИЯ ---")

    # Поиск кандзи 語
    results = controller.search_kanji("語")
    if results:
        kanji_info = controller.get_kanji_info(results[0].id)
        if kanji_info:
            print(f"Кандзи: {kanji_info.character}")
            print(f"Значение: {kanji_info.meaning}")
            print(f"Компоненты: {[comp.kanji.character for comp in kanji_info.radicals]}")

    # Поиск слова 日本語
    results = controller.search_vocabulary("日本語")
    if results:
        word_info = controller.get_word_info(results[0].id)
        if word_info:
            print(f"Слово: {word_info.japanese}")
            print(f"Перевод: {word_info.translation}")
            print(f"Кандзи в слове: {[k.character for k in word_info.kanji_vocabulary]}")


if __name__ == "__main__":
    populate_sample_data()