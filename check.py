import sys
from parser import get_soup, section_table, key_values, parse_address

url = sys.argv[1]
soup = get_soup(url)
raw = str(soup)

print("Длина страницы:", len(raw))
print("Слово 'Руководитель' в HTML:", "Руководитель" in raw)

t = section_table(soup, "Руководитель")
print("Таблица руководителя найдена:", t is not None)
print("Данные:", key_values(t))
print("Адрес:", parse_address(section_table(soup, "Контактная информация")))

i = raw.find("Руководитель")
print("\n--- HTML вокруг заголовка ---")
print(raw[max(0, i - 300): i + 900] if i != -1 else "слова нет в ответе сайта")