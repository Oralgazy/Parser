"""Парсер реестра квалифицированных поставщиков goszakup.gov.kz -> Excel."""
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment

BASE = "https://goszakup.gov.kz"
LIST_URL = BASE + "/ru/registry/rqc?count_record=500&page=1"
OUTPUT = Path("output/suppliers.xlsx")
PAUSE = 1  # пауза между запросами, секунды

session = requests.Session()
session.headers["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def get_soup(url):
    """Загрузка страницы с тремя попытками."""
    for attempt in range(3):
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            return BeautifulSoup(r.text, "lxml")
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Не удалось загрузить {url}")


def parse_list():
    """Список организаций: название, БИН, ссылка на карточку."""
    soup = get_soup(LIST_URL)
    items = []
    for a in soup.select('a[href*="/registry/show_supplier/"]'):
        tds = a.find_parent("tr").find_all("td")
        href = a["href"]
        items.append({
            "name": a.get_text(strip=True),
            "bin": tds[2].get_text(strip=True),
            "url": href if href.startswith("http") else BASE + href,
        })
    return items


def unique(items):
    """В реестре одна организация встречается несколько раз: оставляем по одному БИН."""
    seen, result = set(), []
    for it in items:
        if it["bin"] not in seen:
            seen.add(it["bin"])
            result.append(it)
    return result


def section_table(soup, heading):
    """Таблица, которая идёт после заголовка; закомментированный HTML игнорируем."""
    node = soup.find(
        string=lambda s: s and not isinstance(s, Comment) and s.strip() == heading
    )
    return node.find_next("table") if node else None


def key_values(table):
    """Таблица вида «название: значение» -> словарь."""
    data = {}
    if table is None:
        return data
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) >= 2:
            data[cells[0].get_text(strip=True)] = cells[1].get_text(strip=True)
    return data


def parse_address(table):
    """Полный адрес (рус): предпочитаем юридический, иначе первый."""
    if table is None:
        return ""
    rows = table.find_all("tr")
    if not rows:
        return ""
    headers = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
    col = next((i for i, h in enumerate(headers) if "Полный адрес(рус)" in h), None)
    type_col = next((i for i, h in enumerate(headers) if "Тип адреса" in h), None)
    if col is None:
        return ""

    addresses = []
    for tr in rows[1:]:
        cells = [c.get_text(strip=True) for c in tr.find_all("td")]
        if len(cells) > col:
            addr_type = cells[type_col] if type_col is not None and len(cells) > type_col else ""
            addresses.append((addr_type, cells[col]))

    for addr_type, addr in addresses:
        if "Юридический" in addr_type and addr:
            return addr
    return next((addr for _, addr in addresses if addr), "")


def parse_supplier(item):
    """Карточка организации -> одна строка (с повтором, если страница пришла неполной)."""
    for attempt in range(4):
        soup = get_soup(item["url"])
        head = key_values(section_table(soup, "Руководитель"))
        address = parse_address(section_table(soup, "Контактная информация"))
        if head.get("ФИО") and address:
            break
        time.sleep(2 * (attempt + 1))
    return {
        "Наименование организации": item["name"],
        "БИН организации": item["bin"],
        "ФИО руководителя": head.get("ФИО", ""),
        "ИИН руководителя": head.get("ИИН", ""),
        "Полный адрес организации": address,
        "_url": item["url"],  # служебная колонка, в Excel не попадёт
    }


def main():
    items = unique(parse_list())
    print(f"Уникальных организаций: {len(items)}")

    rows = []
    for i, item in enumerate(items, 1):
        rows.append(parse_supplier(item))
        print(f"{i}/{len(items)} {item['name']}")
        time.sleep(PAUSE)

    df = pd.DataFrame(rows).drop_duplicates(subset="БИН организации")

    # диагностика: у кого остались пустые поля
    empty = df[(df["ФИО руководителя"] == "") | (df["Полный адрес организации"] == "")]
    print(f"\nС пустыми полями: {len(empty)} из {len(df)}")
    for _, r in empty.head(10).iterrows():
        print(" -", r["Наименование организации"], r["_url"])

    # в Excel только 5 нужных столбцов
    df = df.drop(columns="_url")
    OUTPUT.parent.mkdir(exist_ok=True)
    df.to_excel(OUTPUT, index=False)
    print(f"\nГотово: {OUTPUT}, записей: {len(df)}")


if __name__ == "__main__":
    main()