from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from utils.constants import BOOKING_AVAILABLE, BOOKING_CLOSED, BOOKING_UNKNOWN


@pytest.mark.asyncio
async def test_srivari_page_status_available():
    from pages.srivari_page import SrivariPage
    mock_page = AsyncMock()
    mock_page.inner_text = AsyncMock(return_value="Book Now - slots available")
    sp = SrivariPage(mock_page, "http://example.com")
    status = await sp.get_booking_status()
    assert status == BOOKING_AVAILABLE


@pytest.mark.asyncio
async def test_srivari_page_status_closed():
    from pages.srivari_page import SrivariPage
    mock_page = AsyncMock()
    mock_page.inner_text = AsyncMock(return_value="Booking is closed for this month")
    sp = SrivariPage(mock_page, "http://example.com")
    status = await sp.get_booking_status()
    assert status == BOOKING_CLOSED


@pytest.mark.asyncio
async def test_srivari_page_status_unknown():
    from pages.srivari_page import SrivariPage
    mock_page = AsyncMock()
    mock_page.inner_text = AsyncMock(return_value="Welcome to TTD seva portal")
    sp = SrivariPage(mock_page, "http://example.com")
    status = await sp.get_booking_status()
    assert status == BOOKING_UNKNOWN
