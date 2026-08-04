from bot.filters.is_digit import IsDigit


class _FakeMessage:
    def __init__(self, text):
        self.text = text


async def test_matches_digit_only_text():
    assert await IsDigit(is_digit=True)(_FakeMessage("123")) is True


async def test_rejects_non_digit_text_when_expecting_digit():
    assert await IsDigit(is_digit=True)(_FakeMessage("12.3")) is False


async def test_negated_filter_matches_non_digit_text():
    assert await IsDigit(is_digit=False)(_FakeMessage("abc")) is True


async def test_negated_filter_rejects_digit_text():
    assert await IsDigit(is_digit=False)(_FakeMessage("123")) is False


async def test_empty_text_is_not_digit():
    assert await IsDigit(is_digit=True)(_FakeMessage(None)) is False
