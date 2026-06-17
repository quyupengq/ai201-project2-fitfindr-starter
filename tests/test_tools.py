from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(results[0], dict)


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=50)

    assert isinstance(results, list)
    assert all(item["price"] <= 50 for item in results)


def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = suggest_outfit(results[0], get_empty_wardrobe())

    assert isinstance(outfit, str)
    assert len(outfit.strip()) > 0


def test_suggest_outfit_missing_item():
    outfit = suggest_outfit({}, get_empty_wardrobe())

    assert isinstance(outfit, str)
    assert "no thrifted item" in outfit.lower()


def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    fit_card = create_fit_card("", results[0])

    assert isinstance(fit_card, str)
    assert "no outfit suggestion" in fit_card.lower()


def test_create_fit_card_normal_input():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = "Pair it with baggy jeans and chunky sneakers for a casual Y2K thrifted look."
    fit_card = create_fit_card(outfit, results[0])

    assert isinstance(fit_card, str)
    assert len(fit_card.strip()) > 0