from xml.etree import ElementTree

import requests


class CurrencyManager:
    def __init__(self):
        self.cbr_url = "https://www.cbr.ru/scripts/XML_daily.asp"
        self.currencies = {}
        self._fetch_rates()

    def _fetch_rates(self):
        response = requests.get(self.cbr_url)
        tree = ElementTree.fromstring(response.content)

        for currency in tree.findall('Valute'):
            char_code = currency.find('CharCode').text
            value = currency.find('Value').text.replace(',', '.')
            nominal = currency.find('Nominal').text

            self.currencies[char_code] = {
                'value': float(value),
                'nominal': int(nominal)
            }

        self.currencies['RUB'] = {'value': 1.0, 'nominal': 1}

    def get_rate(self, currency_code):
        if currency_code in self.currencies:
            return self.currencies[currency_code]['value'] / self.currencies[currency_code]['nominal']
        else:
            raise ValueError(f"Валюта {currency_code} не найдена")

    def convert(self, amount, from_currency, to_currency):
        if from_currency == 'RUB':
            result = amount / self.get_rate(to_currency)
        elif to_currency == 'RUB':
            result = amount * self.get_rate(from_currency)
        else:
            result = amount * self.get_rate(from_currency) / self.get_rate(to_currency)
        return result
