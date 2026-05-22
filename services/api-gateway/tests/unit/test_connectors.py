"""
Unit tests for connector parser functions.

Tests _extract_trax_id() for Ozon and Yandex Market connectors,
and the UTM-appending logic from the campaigns service.
"""
import pytest

from services.ingestion.connectors.ozon.connector import _extract_trax_id as ozon_extract_trax_id
from services.ingestion.connectors.yandex_market.connector import _extract_trax_id as ym_extract_trax_id
from app.services.campaigns import _append_utm


# ── Ozon: _extract_trax_id ────────────────────────────────────────────────────

class TestOzonExtractTraxId:
    def test_found_in_utm_term(self):
        data = {"utm_term": "trax_id=ab12cd34"}
        assert ozon_extract_trax_id(data) == "ab12cd34"

    def test_found_in_utm_content(self):
        data = {"utm_content": "trax_id=xy98zw56"}
        assert ozon_extract_trax_id(data) == "xy98zw56"

    def test_found_in_utm_campaign(self):
        data = {"utm_campaign": "summer&trax_id=mn34op78&foo=bar"}
        assert ozon_extract_trax_id(data) == "mn34op78"

    def test_found_in_custom_params(self):
        data = {"custom_params": "trax_id=qr12st34"}
        assert ozon_extract_trax_id(data) == "qr12st34"

    def test_found_in_visit_parameters(self):
        data = {"visit_parameters": "trax_id=ab00cd11"}
        assert ozon_extract_trax_id(data) == "ab00cd11"

    def test_not_found_returns_empty_string(self):
        data = {"utm_term": "no-tracking-here", "utm_content": ""}
        assert ozon_extract_trax_id(data) == ""

    def test_empty_dict_returns_empty_string(self):
        assert ozon_extract_trax_id({}) == ""

    def test_wrong_length_not_matched(self):
        # trax_id must be exactly 8 chars
        data = {"utm_term": "trax_id=short"}
        assert ozon_extract_trax_id(data) == ""

    def test_uppercase_not_matched(self):
        # trax_id is lowercase alphanumeric only
        data = {"utm_term": "trax_id=AB12CD34"}
        assert ozon_extract_trax_id(data) == ""

    def test_non_string_field_ignored(self):
        data = {"utm_term": {"nested": "trax_id=ab12cd34"}}
        assert ozon_extract_trax_id(data) == ""

    def test_full_query_string_in_utm_term(self):
        data = {"utm_term": "?utm_source=vk&trax_id=ab12cd34&foo=bar"}
        assert ozon_extract_trax_id(data) == "ab12cd34"


# ── Yandex Market: _extract_trax_id ──────────────────────────────────────────

class TestYMExtractTraxId:
    def test_found_in_context_utm_term(self):
        order = {"context": {"utmTerm": "trax_id=ab12cd34"}}
        assert ym_extract_trax_id(order) == "ab12cd34"

    def test_found_in_context_utm_content(self):
        order = {"context": {"utmContent": "trax_id=ef56gh78"}}
        assert ym_extract_trax_id(order) == "ef56gh78"

    def test_found_in_buyer_utm_term(self):
        order = {"buyer": {"utmTerm": "trax_id=ij90kl12"}}
        assert ym_extract_trax_id(order) == "ij90kl12"

    def test_found_in_custom_fields(self):
        order = {"customFields": "trax_id=mn34op78"}
        assert ym_extract_trax_id(order) == "mn34op78"

    def test_not_found_returns_empty_string(self):
        order = {"context": {"utmTerm": "no-trax-here"}, "buyer": {}}
        assert ym_extract_trax_id(order) == ""

    def test_empty_order_returns_empty_string(self):
        assert ym_extract_trax_id({}) == ""

    def test_context_missing_returns_empty_string(self):
        order = {"status": "PROCESSING", "items": []}
        assert ym_extract_trax_id(order) == ""

    def test_non_string_custom_fields_ignored(self):
        order = {"customFields": {"key": "trax_id=ab12cd34"}}
        assert ym_extract_trax_id(order) == ""

    def test_trax_id_in_query_string_format(self):
        order = {"context": {"utmTerm": "?foo=bar&trax_id=ab12cd34&baz=1"}}
        assert ym_extract_trax_id(order) == "ab12cd34"


# ── _append_utm ───────────────────────────────────────────────────────────────

class TestAppendUtm:
    def test_adds_utm_params_to_clean_url(self):
        result = _append_utm(
            url="https://ozon.ru/product/123",
            source="vk_ads", medium="cpc",
            campaign_name="summer", content=None, term=None,
            trax_id="ab12cd34",
        )
        assert "utm_source=vk_ads" in result
        assert "utm_medium=cpc" in result
        assert "utm_campaign=summer" in result
        assert "trax_id=ab12cd34" in result

    def test_trax_id_always_overwritten(self):
        url = "https://ozon.ru/p/1?trax_id=oldvalue"
        result = _append_utm(
            url=url, source="vk", medium="cpc",
            campaign_name="test", content=None, term=None,
            trax_id="newvalue1",
        )
        assert "trax_id=newvalue1" in result
        assert "oldvalue" not in result

    def test_existing_utm_source_preserved(self):
        url = "https://ozon.ru/p/1?utm_source=existing"
        result = _append_utm(
            url=url, source="vk_ads", medium="cpc",
            campaign_name="test", content=None, term=None,
            trax_id="ab12cd34",
        )
        # setdefault — не перезаписываем существующий utm_source
        assert "utm_source=existing" in result
        assert "utm_source=vk_ads" not in result

    def test_utm_content_added_when_provided(self):
        result = _append_utm(
            url="https://ozon.ru/p/1",
            source="vk", medium="cpc",
            campaign_name="camp", content="banner_v2", term=None,
            trax_id="ab12cd34",
        )
        assert "utm_content=banner_v2" in result

    def test_utm_term_added_when_provided(self):
        result = _append_utm(
            url="https://ozon.ru/p/1",
            source="vk", medium="cpc",
            campaign_name="camp", content=None, term="кроссовки",
            trax_id="ab12cd34",
        )
        assert "utm_term=" in result

    def test_none_content_not_added(self):
        result = _append_utm(
            url="https://ozon.ru/p/1",
            source="vk", medium="cpc",
            campaign_name="camp", content=None, term=None,
            trax_id="ab12cd34",
        )
        assert "utm_content" not in result

    def test_preserves_existing_query_params(self):
        url = "https://ozon.ru/product/123?color=red&size=42"
        result = _append_utm(
            url=url, source="vk", medium="cpc",
            campaign_name="camp", content=None, term=None,
            trax_id="ab12cd34",
        )
        assert "color=red" in result
        assert "size=42" in result

    def test_output_is_valid_url(self):
        from urllib.parse import urlparse
        result = _append_utm(
            url="https://wildberries.ru/catalog/123/detail.aspx",
            source="yandex", medium="cpc",
            campaign_name="shoes", content="ad1", term=None,
            trax_id="mn78op90",
        )
        parsed = urlparse(result)
        assert parsed.scheme == "https"
        assert parsed.netloc == "wildberries.ru"
