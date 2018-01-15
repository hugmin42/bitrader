========
BITRADER
========

Bitcoin Arbitrage utilities. Telegram bot included for free!

Features being worked on at the moment:

- Kraken and Luno buying and selling.
- Support for Altcointrader.co.za
- Experiemental local arbitrage routes

Version 0.12.0: Bot now sends graphs if you ask for /status :-)

Version  0.9.1: Now also supports Ethereum and Litecoin!

Quickstart
==========

1. Download code and install dependencies
-----------------------------------------

.. code-block:: bash

    git clone https://github.com/jr-minnaar/bitrader.git
    cd bitrader
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    cp .env-example .env


2. Configure secrets
--------------------

- Get your Telegram Bot token: https://core.telegram.org/bots#3-how-do-i-create-a-bot
- Sign up with `Kraken <https://www.kraken.com>`_ and get your API key under Settings > API.
- Do the same for `Luno <https://www.luno.com>`_.

Edit the .env file and add all the relevant keys and tokens as indicated by the example .env file.

3. Run the bot
--------------

.. code-block:: bash

    arbot

No parameters needed! Then type /start in chat with your brand new Bitcoin Arbitrage bot.

4. Profit!!!
------------


Jupyter Notebook use
------------

.. code-block:: python

    from dotenv import load_dotenv
    load_dotenv('.env')  # Load environment

    from bitrader.arbitrage_tools import (arbitrage,
        optimal, reverse_arb, get_books, luno_order_book, ice3x_order_book, altcointrader_order_book,
        prepare_order_book, coin_exchange, kraken_order_book, get_forex_buy_quote, COIN_MAP, truncate
    )

    from bitrader.kraken_tools import get_balance, withdraw, buy_coins, get_coins, get_deposit_status, get_deposit_limit


