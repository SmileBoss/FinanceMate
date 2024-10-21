import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bot_controller import BotController
from currency_manager import CurrencyManager
from database_manager import DatabaseManager
from finance_manager import FinanceManager
from goal_manager import GoalManager
from user_manager import UserManager


class TestBot(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user_manager = AsyncMock(spec=UserManager)
        self.finance_manager = AsyncMock(spec=FinanceManager)
        self.currency_manager = AsyncMock(spec=CurrencyManager)
        self.db_manager = AsyncMock(spec=DatabaseManager)
        self.goal_manager = AsyncMock(spec=GoalManager)

        self.bot = MagicMock()
        self.dp = MagicMock()

        self.bot_controller = BotController(
            self.bot, self.dp,
            self.finance_manager,
            self.currency_manager,
            self.db_manager,
            self.goal_manager,
            self.user_manager
        )

    async def test_send_welcome(self):
        message = AsyncMock()
        message.from_user.id = 123

        await self.bot_controller.send_welcome(message)

        message.answer.assert_called_once()
        self.user_manager.add_user.assert_called_once_with(123)

    async def test_get_exchange_rate_valid(self):
        message = AsyncMock()
        message.text = '/rate USD'

        self.currency_manager.get_rate.return_value = 70.5

        await self.bot_controller.get_exchange_rate(message)

        message.answer.assert_called_once_with("Текущий курс USD составляет 70.50 RUB.", parse_mode='Markdown')

    async def test_get_exchange_rate_invalid(self):
        message = AsyncMock()
        message.text = '/rate'

        await self.bot_controller.get_exchange_rate(message)

        message.answer.assert_called_once_with("Пожалуйста, используйте команду в формате /rate `<код_валюты>`.",
                                               parse_mode='Markdown')

    async def test_show_statistics(self):
        message = AsyncMock()
        self.finance_manager.get_statistics.return_value = "Статистика за месяц"
        self.finance_manager.create_statistics_chart.return_value = b'image_data'

        await self.bot_controller.show_statistics(message)

        message.answer.assert_called_once_with("Статистика за месяц", parse_mode='Markdown')
        message.answer_photo.assert_called_once_with(b'image_data', caption="Диаграмма доходов и расходов",
                                                     parse_mode='Markdown')

    async def test_set_goal_start(self):
        message = AsyncMock()
        message.text = '/set_goal Car 300000 2024-12-01'

        await self.bot_controller.set_goal_start(message)

        self.goal_manager.set_financial_goal.assert_called_once_with(
            message.from_user.id, 'Car', 300000.0, '2024-12-01'
        )
        message.reply.assert_called_once_with('Финансовая цель установлена!', parse_mode='Markdown')

    async def test_contribute_to_goal(self):
        message = AsyncMock()
        message.text = '/contribute 1 2000'
        self.goal_manager.contribute_to_goal.return_value = 5000.0

        await self.bot_controller.contribute_to_goal(message)

        self.goal_manager.contribute_to_goal.assert_called_once_with(
            message.from_user.id, 1, 2000.0
        )
        message.reply.assert_called_once_with(
            "Успешно добавлено 2000.00 к цели. Новая накопленная сумма: 5000.00", parse_mode='Markdown'
        )

    async def test_convert_currency(self):
        message = AsyncMock()
        message.text = '/convert 100 USD EUR'

        self.currency_manager.convert.return_value = 85.0

        await self.bot_controller.convert_currency(message)

        message.answer.assert_called_once_with("100.00 USD = 85.00 EUR", parse_mode='Markdown')

    async def test_convert_currency_invalid(self):
        message = AsyncMock()
        message.text = '/convert 100'

        await self.bot_controller.convert_currency(message)

        message.answer.assert_called_once_with(
            "Пожалуйста, используйте команду в формате /convert <сумма> <из_валюты> <в_валюту>.",
            parse_mode='Markdown'
        )

    @patch('aiosqlite.connect', new_callable=AsyncMock)
    async def test_set_goal(self, mock_connect):
        message = AsyncMock()
        message.text = '/set_goal Vacation 5000 2023-12-01'
        message.from_user.id = 123456

        await self.bot_controller.set_goal_start(message)

        self.goal_manager.set_financial_goal.assert_awaited_once_with(
            message.from_user.id, 'Vacation', 5000.0, '2023-12-01'
        )

        message.reply.assert_called_once_with('Финансовая цель установлена!', parse_mode='Markdown')

    @patch('aiosqlite.connect', new_callable=AsyncMock)
    async def test_show_goals_no_goals(self, mock_connect):
        message = AsyncMock()
        message.from_user.id = 123456

        self.goal_manager.get_financial_goals.return_value = []

        await self.bot_controller.show_goals(message)

        message.reply.assert_called_once_with("У вас нет активных финансовых целей.", parse_mode='Markdown')

    @patch('aiosqlite.connect', new_callable=AsyncMock)
    async def test_show_goals_with_entries(self, mock_connect):
        message = AsyncMock()
        message.from_user.id = 123456

        self.goal_manager.get_financial_goals.return_value = [{
            'id': 1,
            'goal_name': 'Vacation',
            'target_amount': 5000,
            'deadline': '2023-12-01',
            'current_amount': 3000
        }]

        await self.bot_controller.show_goals(message)

        expected_response = (
            "id: 1\n"
            "Цель: Vacation\n"
            "Целевая сумма: 5000\n"
            "Текущая сумма: 3000\n"
            "Срок: 2023-12-01"
        )
        message.reply.assert_called_once_with(expected_response, parse_mode='Markdown')

    @patch('aiosqlite.connect', new_callable=AsyncMock)
    async def test_add_reminder(self, mock_connect):
        message = AsyncMock()
        message.text = '/set_reminder Remember this 2023-11-30T14:00:00'
        message.from_user.id = 123456

        await self.bot_controller.goal_manager.add_reminder(message.from_user.id, "Remember this",
                                                            "2023-11-30T14:00:00")

        self.goal_manager.add_reminder.assert_awaited_once_with(
            message.from_user.id, "Remember this", "2023-11-30T14:00:00"
        )

    @patch('aiosqlite.connect', new_callable=AsyncMock)
    async def test_contribute_goal(self, mock_connect):
        message = AsyncMock()
        message.text = '/contribute 1 500'
        message.from_user.id = 123456

        self.goal_manager.contribute_to_goal.return_value = 3500

        await self.bot_controller.contribute_to_goal(message)

        self.goal_manager.contribute_to_goal.assert_awaited_once_with(
            message.from_user.id, 1, 500.0
        )

        message.reply.assert_called_once_with(
            "Успешно добавлено 500.00 к цели. Новая накопленная сумма: 3500.00", parse_mode='Markdown'
        )

    @patch('aiosqlite.connect', new_callable=AsyncMock)
    async def test_set_reminder_invalid_format(self, mock_connect):
        message = AsyncMock()
        message.text = '/set_reminder Remember this tomorrow'
        message.from_user.id = 123456

        await self.bot_controller.set_goal_start(message)

        message.answer.assert_called_once_with(
            "Ошибка в данных. Пожалуйста, убедитесь, что сумма задана правильно.", parse_mode='Markdown'
        )


class TestFinanceManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user_manager = AsyncMock(spec=UserManager)
        self.finance_manager = FinanceManager(db_name=':memory:')
        self.finance_manager.user_manager = self.user_manager

    @patch('aiosqlite.connect')
    async def test_add_income(self, mock_connect):
        mock_db = mock_connect.return_value.__aenter__.return_value
        self.user_manager.get_user_id.return_value = 1

        await self.finance_manager.add_income(telegram_id=12345, category='Зарплата', amount=1000, currency='USD')

        mock_db.execute.assert_called_with('''
                INSERT INTO income (user_id, category, amount, currency, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (1, 'Зарплата', 1000, 'USD', unittest.mock.ANY))

        mock_db.commit.assert_called_once()

    @patch('aiosqlite.connect')
    async def test_add_expense(self, mock_connect):
        mock_db = mock_connect.return_value.__aenter__.return_value
        self.user_manager.get_user_id.return_value = 1

        await self.finance_manager.add_expense(telegram_id=12345, category='Продукты', amount=250, currency='USD')

        mock_db.execute.assert_called_with('''
                INSERT INTO expenses (user_id, category, amount, currency, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (1, 'Продукты', 250, 'USD', unittest.mock.ANY))

        mock_db.commit.assert_called_once()


class TestCurrencyManager(unittest.TestCase):

    def setUp(self):
        self.mock_xml_response = '''<?xml version="1.0" encoding="windows-1251"?>
        <ValCurs Date="01.01.2023" name="Foreign Currency Market">
            <Valute ID="R01010">
                <CharCode>USD</CharCode>
                <Nominal>1</Nominal>
                <Value>76.32</Value>
            </Valute>
            <Valute ID="R01035">
                <CharCode>EUR</CharCode>
                <Nominal>1</Nominal>
                <Value>90.57</Value>
            </Valute>
        </ValCurs>'''
        self.patcher = patch('requests.get')
        self.mock_requests_get = self.patcher.start()
        self.mock_requests_get.return_value.content = self.mock_xml_response

        self.currency_manager = CurrencyManager()

    def tearDown(self):
        self.patcher.stop()

    def test_get_rate_existing_currency(self):
        self.assertAlmostEqual(self.currency_manager.get_rate('USD'), 76.32)
        self.assertAlmostEqual(self.currency_manager.get_rate('EUR'), 90.57)
        self.assertAlmostEqual(self.currency_manager.get_rate('RUB'), 1.0)

    def test_get_rate_nonexistent_currency(self):
        with self.assertRaises(ValueError) as context:
            self.currency_manager.get_rate('ABC')
        self.assertEqual(str(context.exception), "Валюта ABC не найдена")

    def test_convert_rub_to_usd(self):
        result = self.currency_manager.convert(7632, 'RUB', 'USD')
        self.assertAlmostEqual(result, 100.0)

    def test_convert_usd_to_rub(self):
        result = self.currency_manager.convert(1, 'USD', 'RUB')
        self.assertAlmostEqual(result, 76.32)


if __name__ == '__main__':
    unittest.main()
