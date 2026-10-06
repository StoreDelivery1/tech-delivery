SHEET_LOCATION_STORE_IDS = {
    "Appleroom Львів (Городоцька 3)": 34,
    "Appleroom Львів (Пр. Шевченка 3)": 36,
    "Appleroom Львів (Пр.Свободи 9)": 37,
    "Appleroom Львів (ТРЦ King Cross)": 39,
    "Appleroom Львів (ТРЦ Victoria Gardens [Паркінг])": 31,
    "Appleroom Львів (ТРЦ Victoria Gardens)": 40,
    "Appleroom Львів (ТЦ Форум)": 42,
    "Ябко Львів (Victoria Gardens 2)": 44,
    "Ябко Львів (Victoria Gardens)": 43,
    "Ябко Львів (ГОРОДОЦЬКА)": 45,
    "Ябко Львів (Привокзальна)": 48,
    "Ябко Львів (Проспект)": 49,
    "Ябко Львів (Спартак)": 51,
    "Ябко Львів (ТРЦ NewPoint)": 53,
    "Ябко Львів (ТЦ Great)": 54,
    "Ябко Львів (Форум)": 55,
    "Ябко Львів (ШЕВСЬКА)": 57,
    "Ябко Львів King Cross": 58,
    "Відділ сервісу ( клієнтські ремонти)": 50,
    "Львівський ГО": 59,
}

UNRESOLVED_SHEET_LOCATIONS = {
    "Відділ сервісу": (
        "Manual Store.id selection is required; Store IDs 38 and 50 are both "
        "named 'Сервісний Центр'."
    ),
}

NON_STORE_COURIER_DEPARTMENTS = {
    "Відділ транспортної логістики",
}

CREATE_REQUIRED_SHEET_LOCATIONS = {
    "Відділ аксесуарів",
    "Відділ сервісу ( полірування)",
    "Відділ сервісу (наші ремонти)",
    "Відділ сервісу (Переклейки)",
    "Техніка ГО ( нові телефони)",
    "Техніка ГО (вживана техніка)",
    "Техніка ГО (Інтернет Продажі)",
}

SHEET_LOCATION_DISPLAY_NAMES = {
    "Відділ сервісу ( клієнтські ремонти)": "Сервіс Данилишина",
    "Львівський ГО": "ЛГО",
}

STORE_ID_DISPLAY_NAMES = {
    SHEET_LOCATION_STORE_IDS[location]: display_name
    for location, display_name in SHEET_LOCATION_DISPLAY_NAMES.items()
    if location in SHEET_LOCATION_STORE_IDS
}