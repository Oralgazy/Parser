# Парсер реестра квалифицированных поставщиков

Собирает данные с https://www.goszakup.gov.kz/ru/registry/rqc и сохраняет в Excel:
наименование организации, БИН, ФИО и ИИН руководителя, полный адрес.
Дубликаты организаций удаляются по БИН.

## Запуск локально
pip install -r requirements.txt
python parser.py

## Запуск в Docker
docker build -t goszakup-parser .
docker run --rm -v "%cd%/output:/app/output" goszakup-parser

Результат: output/suppliers.xlsx