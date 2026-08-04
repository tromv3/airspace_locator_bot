from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsDigit(BaseFilter):
    """Mirrors old telebot `is_digit=True/False` filter: `message.text.isdigit()`."""

    def __init__(self, is_digit: bool = True) -> None:
        self.is_digit = is_digit

    async def __call__(self, message: Message) -> bool:
        text = message.text or ""
        return text.isdigit() == self.is_digit
