SHEET_LOCATION_STORE_NAMES = {
    "Гавришкевича": "Гавришкевича 5",
    "Гавришкевича 5": "Гавришкевича 5",
    "Галицька": "Галицька 1",
    "Галицька 1": "Галицька 1",
    "Appleroom Львів (Городоцька 3)": "Городоцька 3",
    "Городоцька": "Городоцька 3",
    "Городоцька 3": "Городоцька 3",
    "Ябко Львів (ГОРОДОЦЬКА)": "Городоцька 3",
    "Пр. Свободи 35": "Пр. Свободи 35",
    "Свободи 35": "Пр. Свободи 35",
    "Пр. Шевченка": "Пр. Шевченка 3",
    "Пр. Шевченка 3": "Пр. Шевченка 3",
    "Appleroom Львів (Пр. Шевченка 3)": "Пр. Шевченка 3",
    "Пр. Свободи 9": "Пр. Свободи 9",
    "Свободи 9": "Пр. Свободи 9",
    "Appleroom Львів (Пр.Свободи 9)": "Пр. Свободи 9",
    "Сервісний Центр": "Сервісний Центр",
    "Відділ сервісу": "Сервісний Центр",
    "Відділ сервісу ( клієнтські ремонти)": "Сервісний Центр",
    "King Cross": "ТРЦ King Cross",
    "ТРЦ King Cross": "ТРЦ King Cross",
    "Appleroom Львів (ТРЦ King Cross)": "ТРЦ King Cross",
    "Ябко Львів King Cross": "ТРЦ King Cross",
    "Victoria Gardens": "ТРЦ Victoria Gardens (Паркінг)",
    "Victoria Gardens 2": "ТРЦ Victoria Gardens (Паркінг)",
    "ТРЦ Victoria Gardens": "ТРЦ Victoria Gardens (Паркінг)",
    "ТРЦ Victoria Gardens (Паркінг)": "ТРЦ Victoria Gardens (Паркінг)",
    "Appleroom Львів (ТРЦ Victoria Gardens [Паркінг])": "ТРЦ Victoria Gardens (Паркінг)",
    "Appleroom Львів (ТРЦ Victoria Gardens)": "ТРЦ Victoria Gardens (Паркінг)",
    "Ябко Львів (Victoria Gardens 2)": "ТРЦ Victoria Gardens (Паркінг)",
    "Ябко Львів (Victoria Gardens)": "ТРЦ Victoria Gardens (Паркінг)",
    "Appleroom Львів (ТЦ Форум)": "ТЦ Форум",
    "Ябко Львів (Привокзальна)": "Привокзальна",
    "Ябко Львів (Проспект)": "Проспект",
    "Ябко Львів (Спартак)": "Спартак",
    "Ябко Львів (ТРЦ NewPoint)": "ТРЦ NewPoint",
    "Ябко Львів (ТЦ Great)": "ТЦ Great",
    "Ябко Львів (Форум)": "Форум",
    "Ябко Львів (ШЕВСЬКА)": "ШЕВСЬКА",
    "Львівський ГО": "ЛГО",
}

UNRESOLVED_SHEET_LOCATIONS = {}

NON_STORE_COURIER_DEPARTMENTS = {
    "Відділ транспортної логістики",
}

SHEET_LOCATION_DISPLAY_NAMES = {
    "Відділ сервісу ( клієнтські ремонти)": "Сервіс Данилишина",
    "Львівський ГО": "ЛГО",
}

STORE_NAME_DISPLAY_NAMES = {
    SHEET_LOCATION_STORE_NAMES[location]: display_name
    for location, display_name in SHEET_LOCATION_DISPLAY_NAMES.items()
    if location in SHEET_LOCATION_STORE_NAMES
}