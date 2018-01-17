"""
Dump of some new exploratory routes.
TODO: Needs to be cleaned up and standardized with a way to specify arbitrary routes with fees.
E.g.:
    FNB|ZAR > LUNO|BTC > LUNO|ETH > ALT|ZAR > ALT|BTC > LUNO|ZAR
    10000 > FNB|(0.55%^650)ZAR(110) > KRAKEN|EUR(15) > KRAKEN|(0.26%)BTC(0.001) > LUNO|(0.0002)BTC(1%)
"""

from decimal import Decimal
import os
import pandas as pd

from bitrader.arbitrage_tools import (
    altcointrader_order_book, coin_exchange, ice3x_order_book,
    kraken_order_book, luno_order_book, prepare_order_book, get_prepared_order_book
)

CFUID = os.getenv('CFUID')
CFCLEARANCE = os.getenv('CFCLEARANCE')
USERAGENT = os.getenv('USERAGENT')


def eth_luno_xrp_kraken_arb(amount=Decimal('10000')):
    zar = Decimal(amount)

    btc_asks = prepare_order_book(luno_order_book(book_type='asks', pair='XBTZAR'), book_type='asks')
    btc = coin_exchange(btc_asks, limit=zar, order_type='buy')

    eth_asks = prepare_order_book(luno_order_book(book_type='asks', pair='ETHXBT'), book_type='asks')
    eth = coin_exchange(eth_asks, limit=btc, order_type='buy')

    eur_bids = prepare_order_book(
        kraken_order_book(book_type='bids', currency_code='EUR', coin_code='ETH'), book_type='bids')
    eur = coin_exchange(eur_bids, limit=eth, order_type='sell')

    xrp_asks = prepare_order_book(
        kraken_order_book(book_type='asks', currency_code='EUR', coin_code='XRP'), book_type='asks')
    xrp = coin_exchange(xrp_asks, limit=eur, order_type='buy')

    xrp_bids = prepare_order_book(
        altcointrader_order_book(USERAGENT, CFUID, CFCLEARANCE, 'bids', 'xrp'), book_type='bids')

    zar_out = coin_exchange(xrp_bids, limit=Decimal(xrp), order_type='sell')
    zar_out = zar_out * (1 - Decimal('0.008'))

    roi = ((zar_out - zar) / zar) * 100

    print('BTC/ETH\t', btc / eth)
    print('ZAR/ETH\t', zar / eth)
    print('ETH\t', eth)
    print('EUR/ETH\t', eur / eth)
    print('EUR\t', eur)
    print('EUR/XRP\t', eur)
    print('XRP\t', xrp)

    print('ROI\t', roi)


def btc_luno_xrp_kraken_arb(amount=Decimal('10000')):
    zar = Decimal(amount)

    btc_asks = prepare_order_book(luno_order_book(book_type='asks', pair='XBTZAR'), book_type='asks')
    btc = coin_exchange(btc_asks, limit=zar, order_type='buy')

    xrp_asks = prepare_order_book(kraken_order_book(book_type='asks', pair='XXRPXXBT'), book_type='asks')
    xrp = coin_exchange(xrp_asks, limit=btc, order_type='buy')

    xrp_bids = prepare_order_book(
        altcointrader_order_book(USERAGENT, CFUID, CFCLEARANCE, book_type='bids', coin_code='xrp'), book_type='bids')

    zar_out = coin_exchange(xrp_bids, limit=Decimal(xrp), order_type='sell')
    zar_out = zar_out * (1 - Decimal('0.008'))

    roi = ((zar_out - zar) / zar) * 100

    print('ZAR/BTC\t', zar / btc)
    print('BTC\t', btc)
    print('BTC/XRP\t', btc / xrp)
    print('XRP\t', xrp)
    print('ZAR/XRP\t', zar / xrp)
    print('ZAR\t', zar)
    print('ZAR/XRP\t', zar_out / xrp)
    print('ZAR\t', zar_out)

    print('ROI\t', roi)

    return zar, btc, xrp


def eth_alt_arb(amount=Decimal('10000'), exchange='altcointrader', books=None):
    if not books:
        try:
            eth_asks, eth_bids, btc_asks, btc_bids = get_local_books(coin_code='ETH', start='luno', end=exchange)
        except KeyError:
            return 'Error processing order books. Check if the exchanges are working and that there are open orders.'
    else:
        eth_asks, eth_bids, btc_asks, btc_bids = books

    btc = coin_exchange(btc_asks, limit=amount, order_type='buy')

    eth_out = coin_exchange(eth_asks, limit=btc, order_type='buy')

    eth_fee = eth_out * Decimal('0.0025')
    _start_trade_fee = eth_fee * (amount / eth_out)

    eth_in = eth_out - eth_fee

    zar_in = coin_exchange(eth_bids, limit=Decimal(eth_in), order_type='sell')

    _end_trade_fee = zar_in * Decimal('0.008')

    return eth_out, eth_in, zar_in, _start_trade_fee, _end_trade_fee


def eth_alt_arb_to_luno(amount=Decimal('10000'), exchange='altcointrader', books=None):
    eth_asks = get_prepared_order_book(exchange=exchange, coin_code='ETH', book_type='asks')
    eth_out = coin_exchange(eth_asks, limit=amount, order_type='buy')

    if exchange == "altcointrader":
        eth_fee = eth_out * Decimal('0.008')
    elif exchange == "ice3x":
        eth_fee = eth_out * Decimal('0.01')  # TODO Ice3x variable trading fees

    _start_trade_fee = eth_fee * (amount / eth_out)

    eth_in = eth_out - eth_fee

    eth_fee_luno = eth_in * Decimal('0.0025')
    _end_trade_fee = eth_fee_luno * (amount / eth_in)

    eth_bids = get_prepared_order_book(exchange='luno', coin_code='ETH', book_type='bids')
    btc = coin_exchange(eth_bids, limit=(eth_in - eth_fee_luno), order_type='sell')

    btc_bids = get_prepared_order_book(exchange='luno', coin_code='XBT', book_type='bids')
    zar_in = coin_exchange(btc_bids, limit=btc, order_type='sell')

    return eth_out, eth_in, zar_in, _start_trade_fee, _end_trade_fee


def local_arbitrage(amount=Decimal('10000'), coin_code='ETH', verbose=False, start="ice3x", end="altcointrader",
                    books=None):
    """
    Works for BTC, ETH between Luno, Ice3x and Altcoin in both directions
    And LTC between Ice3x and Altcoin in both directions

    Altcointrader fees included when selling there
    """

    if not books:
        try:
            coin_asks, coin_bids, btc_asks, btc_bids = get_local_books(coin_code=coin_code, start=start, end=end)
        except KeyError:
            return 'Error processing order books. Check if the exchanges are working and that there are open orders.'
    else:
        coin_asks, coin_bids, btc_asks, btc_bids = books

    zar_out = Decimal(amount)
    _end_trade_fee = 0

    if start == "luno" and coin_code == "ETH":
        coin_out, coin_in, zar_in, _start_trade_fee, _end_trade_fee = eth_alt_arb(amount=zar_out, exchange=end,
                                                                                  books=books)

    elif end == "luno" and coin_code == "ETH":
        coin_out, coin_in, zar_in, _start_trade_fee, _end_trade_fee = eth_alt_arb_to_luno(amount=zar_out,
                                                                                          exchange=start)

    else:
        coin_out = coin_exchange(coin_asks, limit=amount, order_type='buy')

        _coin_fee = 0

        if start == "altcointrader":
            _coin_fee = coin_out * Decimal('0.008')
        elif start == "ice3x":
            _coin_fee = coin_out * Decimal('0.01')  # TODO Ice3x variable trading fees

        _start_trade_fee = _coin_fee * (zar_out / coin_out)

        coin_in = coin_out - _coin_fee

        zar_in = coin_exchange(coin_bids, limit=Decimal(coin_in), order_type='sell')

        if end == "altcointrader":
            _end_trade_fee = zar_in * Decimal('0.008')
        elif end == "ice3x":
            _end_trade_fee = zar_in * Decimal('0.01')  # TODO Ice3x variable trading fees

    zar_in_after_fee = zar_in - _end_trade_fee
    roi = (zar_in_after_fee - zar_out) / zar_out * 100
    _total_fees = _start_trade_fee + _end_trade_fee

    response = [
        f'Rands out: R{zar_out:.2f}',
        f'# {start} trade fee: R{_start_trade_fee:.2f}',
        f'{coin_code}: {coin_in:.8f}',
        f'# {end} trade fee: R{_end_trade_fee:.2f}',
        f'Rands in: R{zar_in:.2f}',
        '--------------------',
        f'Profit: R{zar_in_after_fee - zar_out:.2f}',
        f'ROI: {roi:.2f}%',
        '--------------------',
        f'ZAR/{coin_code} Buy: R{(zar_out / coin_out):.2f}',
        f'ZAR/{coin_code} Sell: R{(zar_in / coin_in):.2f}',
        '--------------------',
        f'Total fees: R{_total_fees:.2f}',
    ]

    if verbose:
        print('\n'.join(response))

    return {'roi': roi, 'summary': '\n'.join(response)}


def get_local_books(coin_code: str = 'XBT', start="ice3x", end="altcointrader"):
    """

    :param coin_code: BTC, LTC, or ETH
    :param start: luno, ice3x, altcointrader
    :param end: luno, ice3x, altcointrader
    :return:
    """

    btc_asks = pd.DataFrame()
    btc_bids = pd.DataFrame()

    coin_asks = get_prepared_order_book(exchange=start, coin_code=coin_code, book_type='asks')

    coin_bids = get_prepared_order_book(exchange=end, coin_code=coin_code, book_type='bids')

    if start == "luno" and coin_code == "ETH":
        btc_asks = get_prepared_order_book(exchange='luno', coin_code='XBT', book_type='asks')

    elif end == "luno" and coin_code == "ETH":
        btc_bids = get_prepared_order_book(exchange='luno', coin_code='XBT', book_type='bids')

    return coin_asks, coin_bids, btc_asks, btc_bids


def local_optimal(max_invest: int = 1000000, coin_code: str = 'XBT', start="ice3x", end="altcointrader",
                  return_format: str = 'text'):
    """

    Args:
        max_invest:
        coin_code: XBT, LTC, ETH
        start: luno, ice3x, altcointrader
        end: luno, ice3x, altcointrader
        return_format: text or picture
    """

    books = get_local_books(
        coin_code=coin_code,
        start=start,
        end=end,
    )

    results = []
    for amount in range(5000, max_invest, 5000):

        try:
            results.append(
                dict(
                    amount=amount, roi=local_arbitrage(
                        amount=amount,
                        coin_code=coin_code,
                        start=start,
                        end=end,
                        books=books
                        ,
                    )['roi']))
        except Exception as e:
            print(e)
            break

    df = pd.DataFrame(results)
    df.amount = df.amount.astype(float)
    df = df.set_index('amount')
    df.roi = df.roi.astype(float)

    max_roi = df.max()

    try:
        near_optimal = df.loc[df.roi > max_roi * (1 - 0.001)].reset_index()
        invest_amount = near_optimal.iloc[0].amount
        invest_roi = near_optimal.iloc[0].roi
    except:
        return df

    if return_format == 'text':
        return f'Ideal invest amount: {invest_amount} with ROI of {invest_roi:.2f}'
    elif return_format == 'values':
        return invest_amount, near_optimal
    elif return_format == 'raw':
        return df
    elif return_format == 'png':
        raise NotImplementedError('Not yet implemented')
    else:
        raise KeyError(f'Invalid return_format selection {return_format}')
