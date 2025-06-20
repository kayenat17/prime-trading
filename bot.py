import os
import time
import questionary
from binance import Client
from binance.exceptions import BinanceAPIException
from logger import setup_logger
from dotenv import load_dotenv

class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.logger = setup_logger('trading_bot')
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
        self.logger.info('Initialized BasicBot with testnet=%s', testnet)

    def place_market_order(self, symbol, side, quantity):
        try:
            self.logger.info(f"Placing MARKET order: {side} {quantity} {symbol}")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='MARKET',
                quantity=quantity
            )
            self.logger.info(f"Order response: {order}")
            print("Order placed successfully:", order)
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
            print(f"Error placing market order: {e}")
        except Exception as e:
            self.logger.error(f"Exception: {e}")
            print(f"Unexpected error: {e}")

    def place_limit_order(self, symbol, side, quantity, price):
        try:
            self.logger.info(f"Placing LIMIT order: {side} {quantity} {symbol} @ {price}")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            self.logger.info(f"Order response: {order}")
            print("Order placed successfully:", order)
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
            print(f"Error placing limit order: {e}")
        except Exception as e:
            self.logger.error(f"Exception: {e}")
            print(f"Unexpected error: {e}")

    def place_stop_limit_order(self, symbol, side, quantity, price, stop_price):
        try:
            self.logger.info(f"Placing STOP-LIMIT order: {side} {quantity} {symbol} @ {price} (stop: {stop_price})")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='STOP',
                timeInForce='GTC',
                quantity=quantity,
                price=price,
                stopPrice=stop_price
            )
            self.logger.info(f"Order response: {order}")
            print("Order placed successfully:", order)
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
            print(f"Error placing stop-limit order: {e}")
        except Exception as e:
            self.logger.error(f"Exception: {e}")
            print(f"Unexpected error: {e}")

    def place_twap_order(self, symbol, side, total_quantity, slices, interval_sec):
        try:
            self.logger.info(f"Placing TWAP order: {side} {total_quantity} {symbol} in {slices} slices every {interval_sec}s")
            qty_per_slice = total_quantity / slices
            for i in range(slices):
                self.logger.info(f"TWAP slice {i+1}/{slices}: {qty_per_slice} {symbol}")
                print(f"Placing TWAP slice {i+1}/{slices}: {qty_per_slice} {symbol}")
                self.place_market_order(symbol, side, qty_per_slice)
                if i < slices - 1:
                    time.sleep(interval_sec)
            print("TWAP order completed.")
            self.logger.info("TWAP order completed.")
        except Exception as e:
            self.logger.error(f"Exception in TWAP: {e}")
            print(f"Error in TWAP order: {e}")


def get_api_credentials():
    load_dotenv()
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    if not api_key:
        api_key = questionary.text("Enter your Binance Testnet API Key:").ask().strip()
    if not api_secret:
        api_secret = questionary.text("Enter your Binance Testnet API Secret:").ask().strip()
    return api_key, api_secret


def main():
    print("=== Binance Futures Testnet Trading Bot ===")
    api_key, api_secret = get_api_credentials()
    bot = BasicBot(api_key, api_secret)

    while True:
        order_type = questionary.select(
            "Select order type:",
            choices=["market", "limit", "stop-limit", "twap"]
        ).ask()
        symbol = questionary.text("Symbol (e.g., BTCUSDT):").ask().strip().upper()
        side = questionary.select(
            "Side:",
            choices=["buy", "sell"]
        ).ask()
        if order_type == "twap":
            try:
                total_quantity = float(questionary.text("Total quantity:").ask().strip())
                slices = int(questionary.text("Number of slices:").ask().strip())
                interval_sec = int(questionary.text("Interval between orders (seconds):").ask().strip())
            except ValueError:
                print("Invalid input for TWAP. Try again.")
                continue
            bot.place_twap_order(symbol, side, total_quantity, slices, interval_sec)
        else:
            try:
                quantity = float(questionary.text("Quantity:").ask().strip())
            except ValueError:
                print("Invalid quantity. Try again.")
                continue
            if order_type == "limit":
                try:
                    price = float(questionary.text("Limit price:").ask().strip())
                except ValueError:
                    print("Invalid price. Try again.")
                    continue
                bot.place_limit_order(symbol, side, quantity, price)
            elif order_type == "stop-limit":
                try:
                    price = float(questionary.text("Limit price:").ask().strip())
                    stop_price = float(questionary.text("Stop price:").ask().strip())
                except ValueError:
                    print("Invalid price or stop price. Try again.")
                    continue
                bot.place_stop_limit_order(symbol, side, quantity, price, stop_price)
            else:
                bot.place_market_order(symbol, side, quantity)
        again = questionary.confirm("Place another order?").ask()
        if not again:
            break

if __name__ == '__main__':
    main() 