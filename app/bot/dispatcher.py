from aiogram import Dispatcher


def create_dispatcher() -> Dispatcher:
    """
    Создаёт и возвращает главный Dispatcher приложения.

    Dispatcher отвечает за обработку входящих обновлений
    от Telegram и передачу их соответствующим роутерам.
    """

    dp = Dispatcher()

    return dp