# entities.py

from typing import List
from collections import namedtuple

# Новый тип для представления радикала и его варианта в сложном кандзи
KanjiComponent = namedtuple('KanjiComponent', ['kanji', 'variant_form'])

class Kanji:
    def __init__(self, id=None, character="", meaning="", on_readings="",
                 kun_readings="", jlpt_level=None, is_complex=False, notes=""):
        self.id = id
        self.character = character
        self.meaning = meaning
        self.on_readings = on_readings
        self.kun_readings = kun_readings
        self.jlpt_level = jlpt_level
        self.is_complex = is_complex
        self.notes = notes
        self.radicals: List[KanjiComponent] = [] # Теперь список KanjiComponent
        self.variations: List[str] = [] # Варианты, как радикал

class Word:
    def __init__(self, id=None, japanese="", reading="", translation="", notes=""):
        self.id = id
        self.japanese = japanese
        self.reading = reading
        self.translation = translation
        self.notes = notes
        self.kanji_vocabulary: List[Kanji] = []