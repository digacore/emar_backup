import os
from typing import Generator

from sqlalchemy.orm import Session

from config import config

env = os.environ.get("FLASK_ENV", "development")
CFG = config[env]

if CFG.IS_API:
    from alchemical import Alchemical
else:
    from alchemical.flask import Alchemical

db = Alchemical()

if CFG.IS_API:
    db.initialize(url=CFG.SQLALCHEMY_DATABASE_URI)


def get_db() -> Generator[Session, None, None]:
    with db.Session() as session:
        yield session
