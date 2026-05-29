import asyncio
from typing import Annotated, Literal

import httpx
import trafilatura
from playwright.async_api import async_playwright
from pydantic import Field


async def web_search(
    q: Annotated[str, Field(description="search query")],
    time_range: Annotated[
        Literal["day", "week", "month", "year"] | None,
        Field(description="time range filter"),
    ] = None,
    safesearch: Annotated[
        Literal[0, 1, 2],
        Field(description="safe search filter (0: normal, 1: moderate, 2: strict)"),
    ] = 0,
    n: Annotated[int, Field(description="number of pages")] = 10,
):
    """Search the web for candidate pages"""

    results = {"status": "", "error": None, "results": []}
    excludes = [
        # image
        "pinterest.com",
        # video
        "youtube.com",
        # social media
        "facebook.com",
        "x.com",
        "instagram.com",
        # audio
        "spotify.com",
    ]

    suffix = " "
    suffix += " ".join(f"-site:{s}" for s in excludes)

    try:
        client = httpx.AsyncClient()
        response = await client.get(
            "http://localhost:5279/search",
            params={
                "q": q + suffix,
                "format": "json",
                "language": "en",
                "time_range": time_range or "",
                "safesearch": safesearch,
            },
        )

        results["status"] = str(response)
        data = response.json()

        if response.status_code == 200:
            for result in data["results"][:n]:
                results["results"].append(
                    {
                        "url": result.get("url"),
                        "title": result.get("title"),
                        "content": result.get("content"),
                        "engines": result.get("engines", []),
                    }
                )

    except Exception as e:
        results["error"] = str(e)

    return results


async def web_read(url: str):
    """Simple web access that reads the page content."""

    results = {"status": "ok", "error": None, "content": None}

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = await browser.contexts[0].new_page()

        try:
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")

            while await page.title() == "Just a moment...":
                print("Waiting for captcha challenge.")
                await asyncio.sleep(5)

            html = await page.content()
            results["content"] = trafilatura.extract(html)

        except Exception as e:
            results["error"] = f"Failed to load page: {e}"

    return results
