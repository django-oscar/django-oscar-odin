from pathlib import Path

import nox
from nox.sessions import Session

HERE = Path(__file__).parent


@nox.session(python=("3.8", "3.9", "3.10", "3.11"))
def tests(session: Session):
    # fmt: off
    session.run(
        "poetry", "export",
        # "--with=dev",
        "--output=requirements.txt",
        external=True,
    )
    # fmt: on
    session.install("-Ur", "requirements.txt")
    session.run(HERE / "manage.py")
