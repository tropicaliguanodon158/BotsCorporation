from __future__ import annotations

from aiogram import Dispatcher

from app.handlers.common.start import router as start_router
from app.middlewares.database import DatabaseMiddleware


def create_dispatcher() -> Dispatcher:
    """
    Создаёт главный Dispatcher приложения.

    Здесь собираются:

        - middleware;
        - пользовательские роутеры;
        - обработчики Telegram updates.

    Бизнес-логика здесь отсутствует.
    """

    dp = Dispatcher()

    # ========================================================================
    # MIDDLEWARE
    # ========================================================================

    dp.update.outer_middleware(
        DatabaseMiddleware(),
    )

    # ========================================================================
    # ROUTERS
    # ========================================================================

    # Пока подключаем только реально реализованные handlers.
    #
    # Остальные handler-файлы проекта пока пустые, поэтому импортировать
    # их заранее нельзя — это создаст ложное ощущение готовности системы.
    #
    # По мере реализации каждого модуля его router будет добавляться сюда.

    dp.include_router(
        start_router,
    )

    return dp