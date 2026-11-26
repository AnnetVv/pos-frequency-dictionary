# Електронний частотний словник частин мови.
# Програма читає два тексти, ділить їх на підвибірки по 1000 слововживань,
# рахує частоти словоформ, лем і частин мови (pymorphy3) та зберігає їх у SQLite.
# Тексти покладіть у data/sample/text1.txt і data/sample/text2.txt (по 20 000+ слів).
import re
import sqlite3
from collections import Counter, defaultdict
from pymorphy3 import MorphAnalyzer

morph = MorphAnalyzer(lang='uk')

# Створюємо словник частин мови з англійської абревіатури на українську мову
pos_translation = {
    "NOUN": "іменник",
    "VERB": "дієслово",
    "ADJF": "прикметник",
    "GRND": "прислівник", #дієприслівник
    "PRTF": "прикметник", #дієприкметник
    "NUMR": "числівник",
    "ADVB": "прислівник",
    "NPRO": "займенник",
    "PREP": "прийменник",
    "CONJ": "сполучник",
    "PRCL": "частка",
}

# Це словники винятків, якщо бібліотека неправильно визначає лему або частину мови. Додайте винятки якщо вони потрібні.
custom_pos = {}
lemma_exceptions = {}

# Функція для зчитування та попередньої обробки тексту
def tokenize(file_path):
    with open(file_path, encoding='utf-8') as file:
        text = file.read().lower()
    text = re.sub(r"[^а-яєіїґ'\s-]", '', text)
    tokens = text.split()
    return tokens[:20000]  # Відбираємо 20000 слововживань

# Функція для поділу на підвибірки
def divide_into_subsamples(tokens, size=1000):
    return [tokens[i:i + size] for i in range(0, len(tokens), size)]

# Обчислення словоформ - створюємо словник, де кожному слову відповідає список із частот його вживання в кожній із підвибірок
def calculate_frequencies(subsamples):
    freq_dict = defaultdict(lambda: [0] * len(subsamples))
    for i, subsample in enumerate(subsamples):
        counter = Counter(subsample)
        for word, freq in counter.items():
            freq_dict[word][i] = freq
    return freq_dict

# Функція для лематизації частот (визначення початкової форми, частини мови, переклад на українську)
def lemmatize_frequencies(freq_dict):
    lemma_dict = defaultdict(lambda: {"freqs": [], "pos": None})
    for word, freqs in freq_dict.items():
        if word in lemma_exceptions:
            lemma = lemma_exceptions[word]
            lemma_parse = morph.parse(lemma)[0]
            pos = pos_translation.get(lemma_parse.tag.POS, "невизначено")
        elif word in custom_pos:
            lemma = word  # Лема залишається тією ж самою
            pos = custom_pos[word]
        else:
            lemma_parse = morph.parse(word)[0]
            lemma = lemma_parse.normal_form
            pos = pos_translation.get(lemma_parse.tag.POS, lemma_parse.tag.POS)
        if pos == "невизначено":
            continue
        if lemma in lemma_dict:
            lemma_dict[lemma]["freqs"] = [x + y for x, y in zip(lemma_dict[lemma]["freqs"], freqs)]
        else:
            lemma_dict[lemma]["freqs"] = freqs
            lemma_dict[lemma]["pos"] = pos  # Зберігаємо частину мови

    return lemma_dict

# Функція для визначення частин мови
def pos_frequencies(subsamples):
    pos_dict = defaultdict(lambda: [0] * len(subsamples))
    for i, subsample in enumerate(subsamples):
        for word in subsample:
            pos = morph.parse(word)[0].tag.POS
            pos_ukr = pos_translation.get(pos, "невизначено")
            if pos_ukr == "невизначено":
                continue
            pos_dict[pos_ukr][i] += 1

    return pos_dict


# Функція для створення БД та імпорту даних
def create_database(freq_dict, lemma_dict, pos_dict, db_name="frequency_dict.db", sample_name="sample"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Таблиця частот словоформ
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS ЧС_словоформ_{sample_name} (
                      словоформа TEXT PRIMARY KEY,
                      загальна_частота INTEGER,
                      підвибірка_1 INTEGER, підвибірка_2 INTEGER, підвибірка_3 INTEGER, підвибірка_4 INTEGER,
                      підвибірка_5 INTEGER, підвибірка_6 INTEGER, підвибірка_7 INTEGER, підвибірка_8 INTEGER,
                      підвибірка_9 INTEGER, підвибірка_10 INTEGER, підвибірка_11 INTEGER, підвибірка_12 INTEGER,
                      підвибірка_13 INTEGER, підвибірка_14 INTEGER, підвибірка_15 INTEGER, підвибірка_16 INTEGER,
                      підвибірка_17 INTEGER, підвибірка_18 INTEGER, підвибірка_19 INTEGER, підвибірка_20 INTEGER)''')

    for word, freqs in freq_dict.items():
        cursor.execute(f"INSERT OR IGNORE INTO ЧС_словоформ_{sample_name} VALUES (?, ?, " + ", ".join("?" * 20) + ")", # Першим передаємо слово, другим — суму частот, далі — частоти для кожного підмасиву
                       [word, sum(freqs)] + freqs) #Виконується запит для вставки нового рядка до таблиці

    # Таблиця лем
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS ЧС_лем_{sample_name} (
                      лема TEXT PRIMARY KEY,
                      загальна_частота INTEGER,
                      частина_мови TEXT,
                      підвибірка_1 INTEGER, підвибірка_2 INTEGER, підвибірка_3 INTEGER, підвибірка_4 INTEGER,
                      підвибірка_5 INTEGER, підвибірка_6 INTEGER, підвибірка_7 INTEGER, підвибірка_8 INTEGER,
                      підвибірка_9 INTEGER, підвибірка_10 INTEGER, підвибірка_11 INTEGER, підвибірка_12 INTEGER,
                      підвибірка_13 INTEGER, підвибірка_14 INTEGER, підвибірка_15 INTEGER, підвибірка_16 INTEGER,
                      підвибірка_17 INTEGER, підвибірка_18 INTEGER, підвибірка_19 INTEGER, підвибірка_20 INTEGER)''')

    for lemma, data in lemma_dict.items():
        cursor.execute(f"INSERT OR IGNORE INTO ЧС_лем_{sample_name} VALUES (?, ?, ?, " + ", ".join("?" * 20) + ")",
                       [lemma, sum(data["freqs"]), data["pos"]] + data["freqs"]) #перше поле — частина мови,друге поле — загальна частота, наступні поля — частоти для кожного підвибірки

    # Таблиця частин мови
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS ЧС_частин_мови_{sample_name} (
                      частина_мови TEXT PRIMARY KEY,
                      загальна_частота INTEGER,
                      підвибірка_1 INTEGER, підвибірка_2 INTEGER, підвибірка_3 INTEGER, підвибірка_4 INTEGER,
                      підвибірка_5 INTEGER, підвибірка_6 INTEGER, підвибірка_7 INTEGER, підвибірка_8 INTEGER,
                      підвибірка_9 INTEGER, підвибірка_10 INTEGER, підвибірка_11 INTEGER, підвибірка_12 INTEGER,
                      підвибірка_13 INTEGER, підвибірка_14 INTEGER, підвибірка_15 INTEGER, підвибірка_16 INTEGER,
                      підвибірка_17 INTEGER, підвибірка_18 INTEGER, підвибірка_19 INTEGER, підвибірка_20 INTEGER)''')

    for pos, freqs in pos_dict.items():
        pos_ukrainian = pos_translation.get(pos, pos)
        cursor.execute(
            f"INSERT OR IGNORE INTO ЧС_частин_мови_{sample_name} VALUES (?, ?, " + ", ".join("?" * 20) + ")",
            [pos_ukrainian, sum(freqs)] + freqs[:20])

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS Проміжна_{sample_name} (
                              словоформа TEXT,
                              лема TEXT,
                              частина_мови TEXT,
                              загальна_частота INTEGER,
                              підвибірка_1 INTEGER, підвибірка_2 INTEGER, підвибірка_3 INTEGER, підвибірка_4 INTEGER,
                              підвибірка_5 INTEGER, підвибірка_6 INTEGER, підвибірка_7 INTEGER, підвибірка_8 INTEGER,
                              підвибірка_9 INTEGER, підвибірка_10 INTEGER, підвибірка_11 INTEGER, підвибірка_12 INTEGER,
                              підвибірка_13 INTEGER, підвибірка_14 INTEGER, підвибірка_15 INTEGER, підвибірка_16 INTEGER,
                              підвибірка_17 INTEGER, підвибірка_18 INTEGER, підвибірка_19 INTEGER, підвибірка_20 INTEGER)''')

    for word, freqs in freq_dict.items():
        lemma = lemma_exceptions.get(word, morph.parse(word)[0].normal_form)
        pos = custom_pos.get(word, pos_translation.get(morph.parse(word)[0].tag.POS, "невизначено"))
        cursor.execute(f"INSERT OR IGNORE INTO Проміжна_{sample_name} VALUES (?, ?, ?, ?, " + ", ".join("?" * 20) + ")",
                       [word, lemma, pos, sum(freqs)] + freqs[:20])
    conn.commit() #Зберігання
    conn.close()

# Основний код для обробки обох вибірок
tokens1 = tokenize("data/sample/text1.txt")
tokens2 = tokenize("data/sample/text2.txt")

# Обробка вибірки 1
subsamples1 = divide_into_subsamples(tokens1) #розбиваємо вхідний текстовий масив на менші підвибірки, щоб далі можна було обчислити частоти для кожної з цих підвибірок.
freq_dict1 = calculate_frequencies(subsamples1) #обчислюємо частоти кожного слова в кожній підвибірці і зберігаємо їх у вигляді словника, де кожне слово пов'язане зі списком частот.
lemma_dict1 = lemmatize_frequencies(freq_dict1) #виконуємо лематизацію і обчислюємо частоти вже для цих лем.
pos_dict1 = pos_frequencies(subsamples1) #визначаємо частини мови для кожного слова та обчислюємо їх частотність у кожній підвибірці, зберігаючи результати у словнику
create_database(freq_dict1, lemma_dict1, pos_dict1, db_name="frequency_dict.db", sample_name="vybirka1")

# Обробка вибірки 2
subsamples2 = divide_into_subsamples(tokens2)
freq_dict2 = calculate_frequencies(subsamples2)
lemma_dict2 = lemmatize_frequencies(freq_dict2)
pos_dict2 = pos_frequencies(subsamples2)
create_database(freq_dict2, lemma_dict2, pos_dict2, db_name="frequency_dict.db", sample_name="vybirka2")
