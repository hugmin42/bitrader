import krakenex
from bitrader.arbitrage_tools import retry, prepare_order_book, kraken_order_book, coin_exchange
import os
from decimal import Decimal
from http.client import HTTPException
from socket import timeout

KRAKEN_API_KEY = os.environ.get('KRAKEN_API_KEY')
KRAKEN_PRIVATE_KEY = os.environ.get('KRAKEN_PRIVATE_KEY')


@retry(exception=(HTTPException, timeout, ValueError), report=print)
def get_balance(asset: str = None):
    kraken_api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_PRIVATE_KEY)
    balance = kraken_api.query_private('Balance')

    if asset is not None:
        amount = balance['result']['X' + asset]
        print('{asset} balance: {amount}'.format(asset=asset, amount=amount))
        return amount
    else:
        return balance


@retry(exception=(HTTPException, timeout, ValueError), report=print)
def withdraw(asset: str = 'XBT', wallet_key: str = 'Luno', amount=None):
    kraken_api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_PRIVATE_KEY)

    if amount is None:
        amount = get_balance(asset=asset)
        amount = round(float(amount), 8)
    if round(float(amount), 2) > 0:
        result = kraken_api.query_private('Withdraw', {'asset': asset, 'key': wallet_key, 'amount': amount})
        print('Success!!', result)
        return result
    else:
        print('All funds have been withdrawn from f{wallet_key}')


@retry(exception=(HTTPException, timeout, ValueError), report=print)
def get_coins(amount=None):
    if not amount:
        # Use full balance
        kraken_api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_PRIVATE_KEY)
        amount = kraken_api.query_private('Balance')['result']['ZEUR']
        print(amount)

    eur_asks = prepare_order_book(
        kraken_order_book('asks', coin_code='XBT'), 'asks')

    coins = coin_exchange(eur_asks, Decimal(amount), 'buy')
    coins = str(round(coins, 6))
    return coins


@retry(exception=(HTTPException, timeout, ValueError), report=print)
def buy_coins(euro=None, coins=None):
    if coins is None:
        coins = get_coins(amount=euro)

    kraken_api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_PRIVATE_KEY)
    result = kraken_api.query_private(
        'AddOrder', {'pair': 'XXBTZEUR', 'type': 'buy', 'ordertype': 'market', 'volume': coins})

    return result


@retry(exception=(HTTPException, timeout, ValueError), report=print)
def get_deposit_status(asset: str = 'EUR'):
    kraken_api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_PRIVATE_KEY)
    status = kraken_api.query_private('DepositStatus', {'asset': asset})

    return status


@retry(exception=(HTTPException, timeout, ValueError), report=print)
def get_deposit_limit(asset: str = 'EUR'):
    kraken_api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_PRIVATE_KEY)
    limit = kraken_api.query_private('DepositMethods', {'asset': asset})

    return limit
