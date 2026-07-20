from datetime import datetime

import feedparser
from sqlalchemy.orm import Session

from backend.app import crud


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
        "is_fallback": True,
    },
    {
        "source": "EU",
        "jurisdiction": "European Union",
        "title": "EU publishes update on financial compliance supervision",
        "link": "https://european-union.europa.eu/",
        "published": "Fallback demo update",
        "is_fallback": True,
    },
]


def fetch_regulatory_sources(db: Session, limit_per_source: int = 2) -> list[dict]:
    results: list[dict] = []

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
                    "is_fallback": False,
                    "fetched_at": datetime.utcnow().isoformat(),
                }
                row = crud.save_source_update(db, update)
                results.append(
                    {
                        "update_id": row.update_id,
                        "source": row.source,
                        "jurisdiction": row.jurisdiction,
                        "title": row.title,
                        "link": row.link,
                        "published": row.published,
                        "is_new_update": bool(row.is_new_update),
                        "is_fallback": bool(row.is_fallback),
                        "fetched_at": row.fetched_at,
                    }
                )
        except Exception:
            continue

    existing_sources = {item["source"] for item in results}

    for fallback in FALLBACK_UPDATES:
        if fallback["source"] in existing_sources:
            continue
        row = crud.save_source_update(db, fallback)
        results.append(
            {
                "update_id": row.update_id,
                "source": row.source,
                "jurisdiction": row.jurisdiction,
                "title": row.title,
                "link": row.link,
                "published": row.published,
                "is_new_update": bool(row.is_new_update),
                "is_fallback": bool(row.is_fallback),
                "fetched_at": row.fetched_at,
            }
        )

    db.commit()
    return results


