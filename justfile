fcmp:
    uv run -m fcmp.main

monero:
    uv run -m monero.main

demo: fcmp monero

test:
    uv run pytest
