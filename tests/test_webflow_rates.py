import os

import pytest
import respx
from httpx import Response

from routers import leads as leads_router
from settings import settings


@pytest.mark.asyncio
@respx.mock
async def test_get_webflow_exchange_rate_returns_rate_for_city_and_pair(monkeypatch):
    # Arrange
    monkeypatch.setattr(settings, "webflow_cms_items_url", "https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items")
    monkeypatch.setattr(settings, "webflow_api_key", "test-key")

    payload = {
        "items": [
            {
                "fieldData": {
                    "name": "Санкт-Петербург",
                    "usdt-to-rub-5": "76.41",
                    "rub-to-usdt-2": "77.23",
                }
            }
        ]
    }

    respx.get("https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items").respond(
        200, json=payload
    )

    # Act
    rate = await leads_router._get_webflow_exchange_rate("Санкт-Петербург", "USDT/RUB")

    # Assert
    assert rate == "76.41"


@pytest.mark.asyncio
@respx.mock
async def test_get_webflow_exchange_rate_returns_none_when_field_missing(monkeypatch):
    monkeypatch.setattr(settings, "webflow_cms_items_url", "https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items")
    monkeypatch.setattr(settings, "webflow_api_key", "test-key")

    payload = {
        "items": [
            {
                "fieldData": {
                    "name": "Лас-Вегас",
                    # no usdt-to-usd-4 field
                }
            }
        ]
    }

    respx.get("https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items").respond(
        200, json=payload
    )

    rate = await leads_router._get_webflow_exchange_rate("Лас-Вегас", "USDT/USD")

    assert rate is None


@pytest.mark.asyncio
@respx.mock
async def test_get_webflow_exchange_rate_sends_bearer_auth_header(monkeypatch):
    monkeypatch.setattr(settings, "webflow_cms_items_url", "https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items")
    monkeypatch.setattr(settings, "webflow_api_key", "test-key")

    route = respx.get("https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items").mock(
        return_value=Response(200, json={"items": []})
    )

    await leads_router._get_webflow_exchange_rate("Москва", "USDT/RUB")

    assert route.called
    req = route.calls[0].request
    assert req.headers.get("Authorization") == "Bearer test-key"


@pytest.mark.asyncio
@respx.mock
async def test_get_webflow_exchange_rate_returns_none_on_non_2xx(monkeypatch):
    monkeypatch.setattr(settings, "webflow_cms_items_url", "https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items")
    monkeypatch.setattr(settings, "webflow_api_key", "test-key")

    respx.get("https://api.webflow.com/v2/collections/695ce1515f8c865b2da91da6/items").respond(
        401, json={"message": "unauthorized"}
    )

    rate = await leads_router._get_webflow_exchange_rate("Москва", "USDT/RUB")

    assert rate is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_webflow_rate_not_none():
    """Calls the real Webflow API. Only runs when env vars are configured."""
    if not settings.webflow_api_key or not settings.webflow_cms_items_url:
        pytest.skip("WEBFLOW_API_KEY / WEBFLOW_CMS_ITEMS_URL not set")

    # Pick a city+pair that you expect to have a rate in Webflow CMS
    rate = await leads_router._get_webflow_exchange_rate("Москва", "USDT/RUB")

    assert rate is not None and str(rate).strip() != ""
