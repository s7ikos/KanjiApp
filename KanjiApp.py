# KanjiApp.py
import sys
import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QPushButton, QLabel, \
    QLineEdit, QListWidget, QListWidgetItem, QComboBox, QHBoxLayout, QTextEdit, QMessageBox
from controller import KanjiController
from entities import Kanji, Word
from PySide6.QtCore import QFile, QTextStream

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class StartPage(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        layout = QVBoxLayout()
        layout.addStretch()

        title_label = QLabel("Добро пожаловать в приложение Kanji")
        title_label.setProperty("class", "title")  # Добавлено свойство для стиля
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        start_button = QPushButton("Поиск кандзи")
        start_button.clicked.connect(self.go_to_search)

        add_button = QPushButton("Добавить кандзи/слово")
        add_button.clicked.connect(self.go_to_add)

        button_layout.addWidget(start_button)
        button_layout.addWidget(add_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

        self.setLayout(layout)

    def go_to_search(self):
        search_page = SearchPage(self.parent_window, self.parent_window.kanji_controller)
        self.parent_window.add_page_to_stack(search_page)
        self.parent_window.show_current_page()

    def go_to_add(self):
        add_page = AddItemPage(self.parent_window, self.parent_window.kanji_controller)
        self.parent_window.add_page_to_stack(add_page)
        self.parent_window.show_current_page()


class SearchPage(QWidget):
    def __init__(self, parent_window, kanji_controller):
        super().__init__()
        self.parent_window = parent_window
        self.controller = kanji_controller

        layout = QVBoxLayout()

        title_label = QLabel("Поиск")
        title_label.setProperty("class", "title")  # Добавлено свойство для стиля
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        search_input_layout = QHBoxLayout()

        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Введите кандзи или слово...")
        # Убраны inline-стили
        search_input_layout.addWidget(self.search_line_edit)

        self.search_button = QPushButton("Найти")
        # Убраны inline-стили
        self.search_button.clicked.connect(self.perform_search)
        search_input_layout.addWidget(self.search_button)

        layout.addLayout(search_input_layout)

        self.results_list_widget = QListWidget()
        # Убраны inline-стили
        self.results_list_widget.itemClicked.connect(self.on_result_clicked)
        layout.addWidget(self.results_list_widget)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.parent_window.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

        self.last_query = ""
        self.search_line_edit.returnPressed.connect(self.perform_search)

    def perform_search(self):
        query = self.search_line_edit.text().strip()
        if query:
            print(f"Выполняется поиск для: '{query}'")
            self.last_query = query

            kanji_results = self.controller.search_kanji(query)
            word_results = self.controller.search_vocabulary(query)

            all_results = kanji_results + word_results
            self.update_results_list(all_results)
        else:
            self.results_list_widget.clear()
            self.last_query = ""

    def update_results_list(self, results):
        self.results_list_widget.clear()
        for result in results:
            if isinstance(result, Kanji):
                display_text = f"[Kanji] {result.character} - {result.meaning}"
            elif isinstance(result, Word):
                display_text = f"[Word] {result.japanese} - {result.translation}"
            else:
                display_text = f"Неизвестный тип результата: {type(result)}"
                print(f"Предупреждение: Неизвестный тип результата: {result}")

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, result)
            self.results_list_widget.addItem(item)

    def refresh_results(self):
        if self.last_query:
            print(f"Обновление результатов для: '{self.last_query}'")
            self.search_line_edit.setText(self.last_query)
            self.perform_search()
        else:
            self.results_list_widget.clear()
            print("Обновление: предыдущий запрос отсутствует, список очищен.")

    def on_result_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data is not None:
            print(f"SearchPage.on_result_clicked: Кликнут элемент с типом {type(data)}")
            if isinstance(data, Word):
                print(f"SearchPage.on_result_clicked: kanji_vocabulary ДО get_word_info: {getattr(data, 'kanji_vocabulary', 'N/A')}")
                word_id = data.id
                print(f"SearchPage.on_result_clicked: Запрашиваем полные данные для слова ID {word_id}")
                full_word_data = self.controller.get_word_info(word_id)
                print(f"SearchPage.on_result_clicked: full_word_ {full_word_data}")
                if full_word_data is not None:
                    print(f"SearchPage.on_result_clicked: kanji_vocabulary ПОСЛЕ get_word_info: {getattr(full_word_data, 'kanji_vocabulary', 'N/A')}")
                    print(f"SearchPage.on_result_clicked: Длина kanji_vocabulary ПОСЛЕ get_word_info: {len(getattr(full_word_data, 'kanji_vocabulary', []))}")
                    card_page = CardPage(self.parent_window, full_word_data, self.controller)
                else:
                    print(f"SearchPage.on_result_clicked: Не удалось получить полные данные для слова ID {word_id}")
                    return
            elif isinstance(data, Kanji):
                print(f"SearchPage.on_result_clicked: radicals/vars ДО get_kanji_info:_rad={len(getattr(data, 'radicals', []))}, _var={len(getattr(data, 'variations', []))}")
                kanji_id = data.id
                print(f"SearchPage.on_result_clicked: Запрашиваем полные данные для кандзи ID {kanji_id}")
                full_kanji_data = self.controller.get_kanji_info(kanji_id)
                print(f"SearchPage.on_result_clicked: full_kanji_ {full_kanji_data}")
                if full_kanji_data is not None:
                    print(f"SearchPage.on_result_clicked: radicals/vars ПОСЛЕ get_kanji_info: _rad={len(getattr(full_kanji_data, 'radicals', []))}, _var={len(getattr(full_kanji_data, 'variations', []))}")
                    card_page = CardPage(self.parent_window, full_kanji_data, self.controller)
                else:
                    print(f"SearchPage.on_result_clicked: Не удалось получить полные данные для кандзи ID {kanji_id}")
                    return
            else:
                print(f"SearchPage.on_result_clicked: Неизвестный тип данных: {type(data)}")
                return

            self.parent_window.add_page_to_stack(card_page)
            self.parent_window.show_current_page()
        else:
            print("Предупреждение: Элемент списка не содержит данных.")


class CardPage(QWidget):
    def __init__(self, parent_window, data, kanji_controller):
        super().__init__()
        self.parent_window = parent_window
        self.data = data
        self.kanji_controller = kanji_controller

        layout = QVBoxLayout()

        if isinstance(self.data, Kanji):
            main_char_label = QLabel(self.data.character)
            main_char_label.setProperty("class", "main_character")  # Добавлено свойство для стиля
            main_char_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(main_char_label)

            meaning_label = QLabel(f"<b>Значение:</b> {self.data.meaning}")
            meaning_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
            layout.addWidget(meaning_label)

            if self.data.on_readings:
                on_label = QLabel(f"<b>Онъёми:</b> {self.data.on_readings}")
                on_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
                layout.addWidget(on_label)
            if self.data.kun_readings:
                kun_label = QLabel(f"<b>Кунъёми:</b> {self.data.kun_readings}")
                kun_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
                layout.addWidget(kun_label)

            if self.data.jlpt_level is not None:
                jlpt_label = QLabel(f"<b>Уровень JLPT:</b> N{self.data.jlpt_level}")
                jlpt_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
                layout.addWidget(jlpt_label)

            complex_label = QLabel(f"<b>Составной:</b> {'Да' if self.data.is_complex else 'Нет'}")
            complex_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
            layout.addWidget(complex_label)

            if self.data.radicals:
                radicals_title = QLabel("<b>Составляющие радикалы:</b>")
                radicals_title.setProperty("class", "card_section_title")  # Добавлено свойство для стиля
                layout.addWidget(radicals_title)
                radicals_layout = QHBoxLayout()
                for radical_component in self.data.radicals:
                    radical = radical_component.kanji
                    variant_form = radical_component.variant_form

                    if variant_form:
                        display_text = f"{variant_form} ({radical.character})"
                    else:
                        display_text = f"{radical.character} ({radical.meaning})"

                    radical_label = QLabel(f"<a href='#'>{display_text}</a>")
                    radical_label.setTextFormat(Qt.RichText)
                    radical_label.setOpenExternalLinks(False)
                    radical_label.setProperty("class", "clickable")  # Добавлено свойство для стиля
                    radical_label.linkActivated.connect(lambda _, r_id=radical.id: self.go_to_kanji_card(r_id))
                    radicals_layout.addWidget(radical_label)
                radicals_layout.addStretch()
                layout.addLayout(radicals_layout)

            if self.data.variations:
                variations_title = QLabel("<b>Используется как радикал (варианты):</b>")
                variations_title.setProperty("class", "card_section_title")  # Добавлено свойство для стиля
                layout.addWidget(variations_title)
                variations_text = ", ".join(self.data.variations)
                variations_label = QLabel(variations_text)
                variations_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
                layout.addWidget(variations_label)

        elif isinstance(self.data, Word):
            main_jp_label = QLabel(self.data.japanese)
            main_jp_label.setProperty("class", "main_character")  # Добавлено свойство для стиля
            main_jp_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(main_jp_label)

            if self.data.reading:
                reading_label = QLabel(f"<b>Чтение:</b> {self.data.reading}")
                reading_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
                layout.addWidget(reading_label)

            translation_label = QLabel(f"<b>Перевод:</b> {self.data.translation}")
            translation_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
            layout.addWidget(translation_label)

            if self.data.kanji_vocabulary:
                kanji_in_word_title = QLabel("<b>Составные части (кандзи):</b>")
                kanji_in_word_title.setProperty("class", "card_section_title")  # Добавлено свойство для стиля
                layout.addWidget(kanji_in_word_title)
                kanji_layout = QHBoxLayout()
                for kanji_obj in self.data.kanji_vocabulary:
                    kanji_label = QLabel(f"<a href='#'>{kanji_obj.character} ({kanji_obj.meaning})</a>")
                    kanji_label.setTextFormat(Qt.RichText)
                    kanji_label.setOpenExternalLinks(False)
                    kanji_label.setProperty("class", "clickable")  # Добавлено свойство для стиля
                    kanji_label.linkActivated.connect(lambda _, k_id=kanji_obj.id: self.go_to_kanji_card(k_id))
                    kanji_layout.addWidget(kanji_label)
                kanji_layout.addStretch()
                layout.addLayout(kanji_layout)
            else:
                no_kanji_label = QLabel("<b>Составные части (кандзи):</b> Слово не содержит кандзи (например, хирагана/катакана)")
                no_kanji_label.setProperty("class", "card_text")  # Добавлено свойство для стиля
                layout.addWidget(no_kanji_label)

        else:
            error_label = QLabel(f"Ошибка: Неизвестный тип данных для карточки: {type(self.data)}")
            layout.addWidget(error_label)
            self.setLayout(layout)
            return

        notes_title = QLabel("<b>Заметки:</b>")
        notes_title.setProperty("class", "card_section_title")  # Добавлено свойство для стиля
        layout.addWidget(notes_title)

        self.notes_text_edit = QTextEdit()
        self.notes_text_edit.setPlainText(self.data.notes or "")
        layout.addWidget(self.notes_text_edit)

        save_notes_button = QPushButton("Сохранить заметки")
        save_notes_button.clicked.connect(self.save_notes)
        layout.addWidget(save_notes_button)

        edit_button = QPushButton("Редактировать")
        edit_button.clicked.connect(self.edit_item)
        layout.addWidget(edit_button)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.parent_window.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def save_notes(self):
        new_notes = self.notes_text_edit.toPlainText()
        success = self.kanji_controller.update_notes(self.data.id, new_notes, isinstance(self.data, Kanji))
        if success:
            self.data.notes = new_notes
            print("CardPage: Заметки успешно обновлены в БД и локально.")
        else:
            print("CardPage: Ошибка при сохранении заметок в БД.")

    def edit_item(self):
        edit_page = EditItemPage(self.parent_window, self.kanji_controller, self.data)
        self.parent_window.add_page_to_stack(edit_page)
        self.parent_window.show_current_page()

    def go_to_kanji_card(self, kanji_id):
        kanji_data = self.kanji_controller.get_kanji_info(kanji_id)
        if kanji_data is not None:
            new_card_page = CardPage(self.parent_window, kanji_data, self.kanji_controller)
            self.parent_window.add_page_to_stack(new_card_page)
            self.parent_window.show_current_page()
        else:
            print(f"Ошибка: Не удалось загрузить данные для кандзи ID {kanji_id}")


class EditItemPage(QWidget):
    def __init__(self, parent_window, kanji_controller, item_data):
        super().__init__()
        self.parent_window = parent_window
        self.controller = kanji_controller
        self.item_data = item_data

        layout = QVBoxLayout()

        title_text = f"Редактировать {'кандзи' if isinstance(self.item_data, Kanji) else 'слово'}"
        title_label = QLabel(title_text)
        title_label.setProperty("class", "title")  # Добавлено свойство для стиля
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Кандзи", "Слово"])
        initial_type = "Кандзи" if isinstance(self.item_data, Kanji) else "Слово"
        self.type_combo.setCurrentText(initial_type)
        self.type_combo.setEnabled(False)

        layout.addWidget(QLabel("Тип (неизменяемый):"))
        layout.addWidget(self.type_combo)

        self.kanji_char_label = QLabel("Кандзи:")
        self.kanji_char_edit = QLineEdit()
        self.kanji_meaning_label = QLabel("Значение:")
        self.kanji_meaning_edit = QLineEdit()
        self.kanji_on_label = QLabel("Он-чтение:")
        self.kanji_on_edit = QLineEdit()
        self.kanji_kun_label = QLabel("Кун-чтение:")
        self.kanji_kun_edit = QLineEdit()
        self.kanji_jlpt_label = QLabel("Уровень JLPT:")
        self.kanji_jlpt_edit = QLineEdit()
        self.kanji_complex_label = QLabel("Составной (Да/Нет):")
        self.kanji_complex_combo = QComboBox()
        self.kanji_complex_combo.addItems(["Нет", "Да"])
        self.kanji_notes_label = QLabel("Заметки:")
        self.kanji_notes_edit = QTextEdit()

        self.word_jp_label = QLabel("Японское:")
        self.word_jp_edit = QLineEdit()
        self.word_reading_label = QLabel("Чтение:")
        self.word_reading_edit = QLineEdit()
        self.word_trans_label = QLabel("Перевод:")
        self.word_trans_edit = QLineEdit()
        self.word_notes_label = QLabel("Заметки:")
        self.word_notes_edit_word = QTextEdit()

        self.kanji_components_label = QLabel("Компоненты (кандзи, через запятую):")
        self.kanji_components_edit = QLineEdit()
        self.kanji_variants_label = QLabel("Варианты написания (через запятую):")
        self.kanji_variants_edit = QLineEdit()
        self.word_kanji_label = QLabel("Кандзи в слове (через запятую):")
        self.word_kanji_edit = QLineEdit()

        if isinstance(self.item_data, Kanji):
            self.kanji_char_edit.setText(self.item_data.character)
            self.kanji_meaning_edit.setText(self.item_data.meaning)
            self.kanji_on_edit.setText(self.item_data.on_readings or "")
            self.kanji_kun_edit.setText(self.item_data.kun_readings or "")
            self.kanji_jlpt_edit.setText(str(self.item_data.jlpt_level) if self.item_data.jlpt_level is not None else "")
            self.kanji_complex_combo.setCurrentText("Да" if self.item_data.is_complex else "Нет")
            self.kanji_notes_edit.setPlainText(self.item_data.notes or "")

            component_chars = [comp.kanji.character for comp in self.item_data.radicals]
            self.kanji_components_edit.setText(", ".join(component_chars))
            self.kanji_variants_edit.setText(", ".join(self.item_data.variations))

        elif isinstance(self.item_data, Word):
            self.word_jp_edit.setText(self.item_data.japanese)
            self.word_reading_edit.setText(self.item_data.reading)
            self.word_trans_edit.setText(self.item_data.translation)
            self.word_notes_edit_word.setPlainText(self.item_data.notes or "")

            kanji_chars_in_word = [k.character for k in self.item_data.kanji_vocabulary]
            self.word_kanji_edit.setText(", ".join(kanji_chars_in_word))

        layout.addWidget(self.kanji_char_label)
        layout.addWidget(self.kanji_char_edit)
        layout.addWidget(self.kanji_meaning_label)
        layout.addWidget(self.kanji_meaning_edit)
        layout.addWidget(self.kanji_on_label)
        layout.addWidget(self.kanji_on_edit)
        layout.addWidget(self.kanji_kun_label)
        layout.addWidget(self.kanji_kun_edit)
        layout.addWidget(self.kanji_jlpt_label)
        layout.addWidget(self.kanji_jlpt_edit)
        layout.addWidget(self.kanji_complex_label)
        layout.addWidget(self.kanji_complex_combo)
        layout.addWidget(self.kanji_notes_label)
        layout.addWidget(self.kanji_notes_edit)

        layout.addWidget(self.word_jp_label)
        layout.addWidget(self.word_jp_edit)
        layout.addWidget(self.word_reading_label)
        layout.addWidget(self.word_reading_edit)
        layout.addWidget(self.word_trans_label)
        layout.addWidget(self.word_trans_edit)
        layout.addWidget(self.word_notes_label)
        layout.addWidget(self.word_notes_edit_word)

        layout.addWidget(self.kanji_components_label)
        layout.addWidget(self.kanji_components_edit)
        layout.addWidget(self.kanji_variants_label)
        layout.addWidget(self.kanji_variants_edit)
        layout.addWidget(self.word_kanji_label)
        layout.addWidget(self.word_kanji_edit)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.hide()
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_item)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.setObjectName("delete_button")
        self.delete_button.clicked.connect(self.delete_item)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.parent_window.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)
        self.update_fields_visibility()

    def update_fields_visibility(self):
        is_kanji = self.type_combo.currentText() == "Кандзи"
        self.kanji_char_label.setVisible(is_kanji)
        self.kanji_char_edit.setVisible(is_kanji)
        self.kanji_meaning_label.setVisible(is_kanji)
        self.kanji_meaning_edit.setVisible(is_kanji)
        self.kanji_on_label.setVisible(is_kanji)
        self.kanji_on_edit.setVisible(is_kanji)
        self.kanji_kun_label.setVisible(is_kanji)
        self.kanji_kun_edit.setVisible(is_kanji)
        self.kanji_jlpt_label.setVisible(is_kanji)
        self.kanji_jlpt_edit.setVisible(is_kanji)
        self.kanji_complex_label.setVisible(is_kanji)
        self.kanji_complex_combo.setVisible(is_kanji)
        self.kanji_notes_label.setVisible(is_kanji)
        self.kanji_notes_edit.setVisible(is_kanji)
        self.kanji_components_label.setVisible(is_kanji)
        self.kanji_components_edit.setVisible(is_kanji)
        self.kanji_variants_label.setVisible(is_kanji)
        self.kanji_variants_edit.setVisible(is_kanji)

        self.word_jp_label.setVisible(not is_kanji)
        self.word_jp_edit.setVisible(not is_kanji)
        self.word_reading_label.setVisible(not is_kanji)
        self.word_reading_edit.setVisible(not is_kanji)
        self.word_trans_label.setVisible(not is_kanji)
        self.word_trans_edit.setVisible(not is_kanji)
        self.word_notes_label.setVisible(not is_kanji)
        self.word_notes_edit_word.setVisible(not is_kanji)
        self.word_kanji_label.setVisible(not is_kanji)
        self.word_kanji_edit.setVisible(not is_kanji)

    def show_status_message(self, message, is_success=True, duration=3000):
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
            if is_success:
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.show()
            QTimer.singleShot(duration, lambda: self.hide_status_message())
        else:
            print("Предупреждение: status_label не найден.")

    def hide_status_message(self):
        if hasattr(self, 'status_label'):
            self.status_label.hide()
            self.status_label.setText("")
        else:
            print("Предупреждение: status_label не найден.")

    def save_item(self):
        item_type = self.type_combo.currentText()
        self.save_button.setEnabled(False)
        self.save_button.setText("Сохранение...")

        try:
            success = False
            if item_type == "Кандзи":
                self.item_data.character = self.kanji_char_edit.text().strip()
                self.item_data.meaning = self.kanji_meaning_edit.text().strip()
                self.item_data.on_readings = self.kanji_on_edit.text().strip()
                self.item_data.kun_readings = self.kanji_kun_edit.text().strip()
                jlpt_level_str = self.kanji_jlpt_edit.text().strip()
                self.item_data.jlpt_level = int(jlpt_level_str) if jlpt_level_str.isdigit() else None
                self.item_data.is_complex = self.kanji_complex_combo.currentText() == "Да"
                self.item_data.notes = self.kanji_notes_edit.toPlainText().strip()

                success = self.controller.update_kanji(self.item_data)

                if success:
                    components_str = self.kanji_components_edit.text().strip()
                    component_chars = [c.strip() for c in components_str.split(",")] if components_str else []
                    self.controller.update_kanji_components(self.item_data.id, component_chars)

                    variants_str = self.kanji_variants_edit.text().strip()
                    variant_forms = [v.strip() for v in variants_str.split(",")] if variants_str else []
                    self.controller.update_kanji_variants(self.item_data.id, variant_forms)

                    self.show_status_message(f"Кандзи '{self.item_data.character}' успешно обновлено!")

            elif item_type == "Слово":
                self.item_data.japanese = self.word_jp_edit.text().strip()
                self.item_data.reading = self.word_reading_edit.text().strip()
                self.item_data.translation = self.word_trans_edit.text().strip()
                self.item_data.notes = self.word_notes_edit_word.toPlainText().strip()

                success = self.controller.update_vocabulary(self.item_data)

                if success:
                    kanji_str = self.word_kanji_edit.text().strip()
                    kanji_chars = [k.strip() for k in kanji_str.split(",")] if kanji_str else []
                    self.controller.update_word_kanji(self.item_data.id, kanji_chars)

                    self.show_status_message(f"Слово '{self.item_data.japanese}' успешно обновлено!")

            if not success:
                self.show_status_message("Ошибка при сохранении.", is_success=False)
            else:
                current_index = self.parent_window.stacked_widget.currentIndex()
                self.parent_window.stacked_widget.removeWidget(self.parent_window.stacked_widget.currentWidget())
                self.parent_window.page_stack.pop()
                self.parent_window.show_current_page()

        except ValueError as e:
            self.show_status_message(f"Ошибка ввода: {e}", is_success=False)
        except Exception as e:
            self.show_status_message(f"Ошибка: {e}", is_success=False)
        finally:
            self.save_button.setEnabled(True)
            self.save_button.setText("Сохранить")

    def delete_item(self):
        item_type = self.type_combo.currentText()
        item_name = self.item_data.character if isinstance(self.item_data, Kanji) else self.item_data.japanese

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить {item_type.lower()} '{item_name}'? Это действие необратимо.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = False
            if item_type == "Кандзи":
                success = self.controller.delete_kanji(self.item_data.id)
            elif item_type == "Слово":
                success = self.controller.delete_vocabulary(self.item_data.id)

            if success:
                self.show_status_message(f"{item_type} '{item_name}' успешно удалено!", is_success=True)
                self.parent_window.go_back_to_search_page()
            else:
                self.show_status_message("Ошибка при удалении.", is_success=False)


class AddItemPage(QWidget):
    def __init__(self, parent_window, kanji_controller):
        super().__init__()
        self.parent_window = parent_window
        self.controller = kanji_controller

        layout = QVBoxLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Кандзи", "Слово"])
        layout.addWidget(QLabel("Тип:"))
        layout.addWidget(self.type_combo)

        self.kanji_char_label = QLabel("Кандзи:")
        self.kanji_char_edit = QLineEdit()
        self.kanji_meaning_label = QLabel("Значение:")
        self.kanji_meaning_edit = QLineEdit()
        self.kanji_on_label = QLabel("Он-чтение:")
        self.kanji_on_edit = QLineEdit()
        self.kanji_kun_label = QLabel("Кун-чтение:")
        self.kanji_kun_edit = QLineEdit()
        self.kanji_jlpt_label = QLabel("Уровень JLPT:")
        self.kanji_jlpt_edit = QLineEdit()
        self.kanji_complex_label = QLabel("Сложный (Да/Нет):")
        self.kanji_complex_combo = QComboBox()
        self.kanji_complex_combo.addItems(["Нет", "Да"])
        self.kanji_notes_label = QLabel("Заметки:")
        self.kanji_notes_edit = QTextEdit()

        self.word_jp_label = QLabel("Японское:")
        self.word_jp_edit = QLineEdit()
        self.word_reading_label = QLabel("Чтение:")
        self.word_reading_edit = QLineEdit()
        self.word_trans_label = QLabel("Перевод:")
        self.word_trans_edit = QLineEdit()
        self.word_notes_label = QLabel("Заметки:")
        self.word_notes_edit = QTextEdit()

        self.kanji_components_label = QLabel("Компоненты (кандзи, через запятую):")
        self.kanji_components_edit = QLineEdit()
        self.kanji_variants_label = QLabel("Варианты написания (через запятую):")
        self.kanji_variants_edit = QLineEdit()
        self.word_kanji_label = QLabel("Кандзи в слове (через запятую):")
        self.word_kanji_edit = QLineEdit()

        layout.addWidget(self.kanji_char_label)
        layout.addWidget(self.kanji_char_edit)
        layout.addWidget(self.kanji_meaning_label)
        layout.addWidget(self.kanji_meaning_edit)
        layout.addWidget(self.kanji_on_label)
        layout.addWidget(self.kanji_on_edit)
        layout.addWidget(self.kanji_kun_label)
        layout.addWidget(self.kanji_kun_edit)
        layout.addWidget(self.kanji_jlpt_label)
        layout.addWidget(self.kanji_jlpt_edit)
        layout.addWidget(self.kanji_complex_label)
        layout.addWidget(self.kanji_complex_combo)
        layout.addWidget(self.kanji_notes_label)
        layout.addWidget(self.kanji_notes_edit)
        layout.addWidget(self.kanji_components_label)
        layout.addWidget(self.kanji_components_edit)
        layout.addWidget(self.kanji_variants_label)
        layout.addWidget(self.kanji_variants_edit)

        layout.addWidget(self.word_jp_label)
        layout.addWidget(self.word_jp_edit)
        layout.addWidget(self.word_reading_label)
        layout.addWidget(self.word_reading_edit)
        layout.addWidget(self.word_trans_label)
        layout.addWidget(self.word_trans_edit)
        layout.addWidget(self.word_notes_label)
        layout.addWidget(self.word_notes_edit)
        layout.addWidget(self.word_kanji_label)
        layout.addWidget(self.word_kanji_edit)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.hide()
        layout.addWidget(self.status_label)

        self.create_button = QPushButton("Создать")
        self.create_button.clicked.connect(self.create_item)
        layout.addWidget(self.create_button)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.parent_window.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)
        self.update_fields_visibility()
        self.type_combo.currentTextChanged.connect(self.update_fields_visibility)

    def update_fields_visibility(self):
        is_kanji = self.type_combo.currentText() == "Кандзи"
        self.kanji_char_label.setVisible(is_kanji)
        self.kanji_char_edit.setVisible(is_kanji)
        self.kanji_meaning_label.setVisible(is_kanji)
        self.kanji_meaning_edit.setVisible(is_kanji)
        self.kanji_on_label.setVisible(is_kanji)
        self.kanji_on_edit.setVisible(is_kanji)
        self.kanji_kun_label.setVisible(is_kanji)
        self.kanji_kun_edit.setVisible(is_kanji)
        self.kanji_jlpt_label.setVisible(is_kanji)
        self.kanji_jlpt_edit.setVisible(is_kanji)
        self.kanji_complex_label.setVisible(is_kanji)
        self.kanji_complex_combo.setVisible(is_kanji)
        self.kanji_notes_label.setVisible(is_kanji)
        self.kanji_notes_edit.setVisible(is_kanji)
        self.kanji_components_label.setVisible(is_kanji)
        self.kanji_components_edit.setVisible(is_kanji)
        self.kanji_variants_label.setVisible(is_kanji)
        self.kanji_variants_edit.setVisible(is_kanji)

        self.word_jp_label.setVisible(not is_kanji)
        self.word_jp_edit.setVisible(not is_kanji)
        self.word_reading_label.setVisible(not is_kanji)
        self.word_reading_edit.setVisible(not is_kanji)
        self.word_trans_label.setVisible(not is_kanji)
        self.word_trans_edit.setVisible(not is_kanji)
        self.word_notes_label.setVisible(not is_kanji)
        self.word_notes_edit.setVisible(not is_kanji)
        self.word_kanji_label.setVisible(not is_kanji)
        self.word_kanji_edit.setVisible(not is_kanji)

    def show_status_message(self, message, is_success=True, duration=3000):
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
            if is_success:
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.show()
            QTimer.singleShot(duration, lambda: self.hide_status_message())
        else:
            print("Предупреждение: status_label не найден.")

    def hide_status_message(self):
        if hasattr(self, 'status_label'):
            self.status_label.hide()
            self.status_label.setText("")
        else:
            print("Предупреждение: status_label не найден.")

    def create_item(self):
        item_type = self.type_combo.currentText()
        self.create_button.setEnabled(False)
        self.create_button.setText("Создание...")

        try:
            success = False
            created_id = None
            created_name = ""

            if item_type == "Кандзи":
                char = self.kanji_char_edit.text().strip()
                if not char:
                    self.show_status_message("Кандзи не может быть пустым.", is_success=False)
                    return
                meaning = self.kanji_meaning_edit.text().strip()
                on_readings = self.kanji_on_edit.text().strip()
                kun_readings = self.kanji_kun_edit.text().strip()
                jlpt_level_str = self.kanji_jlpt_edit.text().strip()
                jlpt_level = int(jlpt_level_str) if jlpt_level_str.isdigit() else None
                is_complex = self.kanji_complex_combo.currentText() == "Да"
                notes = self.kanji_notes_edit.toPlainText().strip()

                new_kanji = Kanji(
                    character=char, meaning=meaning, on_readings=on_readings,
                    kun_readings=kun_readings, jlpt_level=jlpt_level,
                    is_complex=is_complex, notes=notes
                )

                kanji_id = self.controller.add_kanji_with_details(new_kanji)

                if kanji_id:
                    print(f"Кандзи '{char}' успешно добавлен с ID {kanji_id}.")
                    created_id = kanji_id
                    created_name = char
                    success = True

                    components_str = self.kanji_components_edit.text().strip()
                    if components_str:
                        component_chars = [c.strip() for c in components_str.split(",")]
                        self.controller.link_kanji_components(kanji_id, component_chars)

                    variants_str = self.kanji_variants_edit.text().strip()
                    if variants_str:
                        variant_forms = [v.strip() for v in variants_str.split(",")]
                        self.controller.link_kanji_variants(kanji_id, variant_forms)

            elif item_type == "Слово":
                japanese = self.word_jp_edit.text().strip()
                if not japanese:
                    self.show_status_message("Японское слово не может быть пустым.", is_success=False)
                    return
                reading = self.word_reading_edit.text().strip()
                translation = self.word_trans_edit.text().strip()
                notes = self.word_notes_edit.toPlainText().strip()

                new_word = Word(
                    japanese=japanese, reading=reading, translation=translation, notes=notes
                )

                word_id = self.controller.add_vocabulary_with_details(new_word)

                if word_id:
                    print(f"Слово '{japanese}' успешно добавлено с ID {word_id}.")
                    created_id = word_id
                    created_name = japanese
                    success = True

                    kanji_str = self.word_kanji_edit.text().strip()
                    if kanji_str:
                        kanji_chars = [k.strip() for k in kanji_str.split(",")]
                        self.controller.link_word_kanji(word_id, kanji_chars)

            if success:
                self.show_status_message(f"{item_type} '{created_name}' (ID: {created_id}) создано!")

        except ValueError as e:
            self.show_status_message(f"Ошибка ввода: {e}", is_success=False)
        except Exception as e:
            self.show_status_message(f"Ошибка: {e}", is_success=False)
        finally:
            self.create_button.setEnabled(True)
            self.create_button.setText("Создать")


class MainWindow(QMainWindow):
    def __init__(self, db_name="kanji.db"):
        super().__init__()
        self.setWindowTitle("Изучение Кандзи")
        self.setGeometry(100, 100, 800, 600)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.page_stack = []

        self.kanji_controller = KanjiController(db_name)

        self.load_stylesheet("styles.qss")

        self.add_page_to_stack(StartPage(self))
        self.show_current_page()

    def load_stylesheet(self, relative_path):
        path = resource_path(relative_path)
        style_file = QFile(path)
        if style_file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(style_file)
            stylesheet = stream.readAll()
            style_file.close()
            self.setStyleSheet(stylesheet)
            print(f"Таблица стилей загружена из {path}")
        else:
            print(f"Не удалось загрузить таблицу стилей из {path}")

    def add_page_to_stack(self, page):
        index = self.stacked_widget.addWidget(page)
        self.page_stack.append(index)

    def show_current_page(self):
        if self.page_stack:
            current_index = self.page_stack[-1]
            self.stacked_widget.setCurrentIndex(current_index)

    def go_back(self):
        if len(self.page_stack) > 1:
            self.stacked_widget.removeWidget(self.stacked_widget.currentWidget())
            self.page_stack.pop()
            self.show_current_page()

    def go_back_to_search_page(self):
        current_widget = self.stacked_widget.currentWidget()

        if isinstance(current_widget, SearchPage):
            current_widget.refresh_results()
            return

        while len(self.page_stack) > 1:
            self.stacked_widget.removeWidget(current_widget)
            self.page_stack.pop()

            current_widget = self.stacked_widget.currentWidget()

            if isinstance(current_widget, SearchPage):
                current_widget.refresh_results()
                self.show_current_page()
                return

        self.show_current_page()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(db_name="kanji.db")
    window.show()
    sys.exit(app.exec())