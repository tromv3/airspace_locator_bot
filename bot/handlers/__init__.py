from aiogram import Router

from bot.handlers import (
    aircraft_info,
    cancel,
    draw,
    fallback,
    get_aircraft,
    help,
    history,
    set_location,
    start,
)


def setup_routers() -> Router:
    root = Router(name="root")
    modules = (
        start,
        help,
        cancel,
        history,
        set_location,
        get_aircraft,
        draw,
        aircraft_info,
        fallback,
    )
    for module in modules:
        root.include_router(module.router)
    return root
