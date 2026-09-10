"""DOM locator strategy.

Preferred hierarchy (see architecture doc section 13):
    1. data-testid
    2. accessible role + name
    3. label
    4. placeholder
    5. stable ID
    6. stable CSS selector
    7. visual detection fallback

Site-specific selectors come from configuration. Here we only provide small
helpers for resolving them and for optional role/label fallbacks.
"""

from __future__ import annotations

from playwright.async_api import Locator, Page


def image_region(page: Page, selector: str) -> Locator:
    return page.locator(selector).first


def input_field(page: Page, selector: str) -> Locator:
    return page.locator(selector).first


def continue_button(page: Page, selector: str) -> Locator:
    return page.locator(selector).first


def success_marker(page: Page, selector: str) -> Locator:
    return page.locator(selector).first


def rejection_marker(page: Page, selector: str) -> Locator:
    return page.locator(selector).first