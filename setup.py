from pathlib import Path

from poetry.core.factory import Factory
from poetry.core.masonry.builders.sdist import SdistBuilder

# let poetry construct setupt.py
cwd_path = Path(".").resolve()
poetry = Factory().create_poetry()
sdist_builder = SdistBuilder(poetry)
setup_py = sdist_builder.build_setup()

# run setup in the current context
exec(setup_py, globals(), locals())
