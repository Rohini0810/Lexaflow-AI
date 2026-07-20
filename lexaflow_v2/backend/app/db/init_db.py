from pathlib import Path

from backend.app.db.database import Base, engine
from backend.app.db import models  # noqa: F401


def init_db() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


