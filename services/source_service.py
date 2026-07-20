import feedparser
from datetime import datetime
from services.db_services import save_source_update

REGULATORY_SOURCES = [
    {
        "source": "RBI",
        "jurisdiction": "India",
        "url": "https://www.rbi.org.in/Scripts/rss.aspx",
    },
    {
        "source": "SEC",
        "jurisdiction": "United States",
        "url": "https://www.sec.gov/news/pressreleases.rss",
    },
    {
        "source": "EU",
        "jurisdiction": "European Union",
        "url": "https://www.consilium.europa.eu/en/rss/press-releases/",
    },
]

FALLBACK_UPDATES = [
    {
        "source": "RBI",
        "jurisdiction": "India",
        "title": "RBI releases updated KYC monitoring guidance",
        "link": "https://www.rbi.org.in/",
        "published": "Fallback demo update",
        "is_fallback": True
    },
    {
        "source": "EU",
        "jurisdiction": "European Union",
        "title": "EU publishes update on financial compliance supervision",
        "link": "https://european-union.europa.eu/",
        "published": "Fallback demo update",
        "is_fallback": True
    },
]


def fetch_regulatory_sources(limit_per_source=2):
    results = []

    for source in REGULATORY_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            entries = feed.entries[:limit_per_source]

            for entry in entries:
                update = {
                    "source": source["source"],
                    "jurisdiction": source["jurisdiction"],
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "Unknown"),
                    "fetched_at": datetime.now().isoformat(),
                    "is_fallback": False
                }

                saved_update = save_source_update(update)
                results.append(saved_update)

        except Exception:
            pass

    existing_sources = {item["source"] for item in results}

    for fallback in FALLBACK_UPDATES:
        if fallback["source"] not in existing_sources:
            fallback["fetched_at"] = datetime.now().isoformat()
            saved_update = save_source_update(fallback)
            results.append(saved_update)

    return results