import requests

url = "https://goszakup.gov.kz/ru/registry/show_supplier/73801"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)

print("Статус:", r.status_code)
print("Длина ответа:", len(r.text))
print("Есть слово 'Руководитель':", "Руководитель" in r.text)

i = r.text.find("Руководитель")
print(r.text[max(0, i - 200): i + 600] if i != -1 else r.text[:1500])   