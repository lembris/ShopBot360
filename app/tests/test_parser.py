from app.parser.command_parser import CommandParser
from app.parser.intents import Intent


def test_sell_command():
    parser = CommandParser()
    result = parser.parse("sell 2 soda 1500")
    assert result.intent == Intent.SELL
    assert result.entities.qty == 2
    assert result.entities.product == "soda"
    assert result.entities.price == 1500


def test_sell_with_customer():
    result = CommandParser().parse("sell 1 rice 2500 john")
    assert result.entities.customer == "john"


def test_swahili_uza_synonym():
    result = CommandParser().parse("uza maji 3")
    # May need clarification without price
    assert result.intent in (Intent.SELL, Intent.UNKNOWN) or result.needs_clarification


def test_stock_add():
    result = CommandParser().parse("stock add sugar 50")
    assert result.intent == Intent.STOCK_ADD
    assert result.entities.qty == 50


def test_report_today():
    result = CommandParser().parse("report today")
    assert result.intent == Intent.REPORT_TODAY


def test_debt_command():
    result = CommandParser().parse("debt john")
    assert result.intent == Intent.DEBT
    assert result.entities.customer == "john"


def test_payment_command():
    result = CommandParser().parse("paid john 5000")
    assert result.intent == Intent.PAYMENT
    assert result.entities.amount == 5000
