import requests
import base64
import re
import json
from bs4 import BeautifulSoup
import websocket
from time import time

# My libraries
from mw_requests.Request import Request
from mw_requests.Errors import *

with open("mw_requests/requests.json", "r") as f:
    all_requests = json.load(f)["userRequests"]

class User:
    def login_required(func):
        """
        Decorator function that checks for authentication

        :param func: inner function
        :returns: func return
        """
        def wrapper(self, *args, **kwargs):
            if self.authenticated:
                result = func(self, *args, **kwargs)
                return result
            else:
                raise FieldNotFoundError("User must be authenticated.")
        return wrapper
    
    def default_game_required(func):
        """
        Decorator function that checks for default game

        :param func: inner function
        :returns: func return
        """
        def wrapper(self, *args, **kwargs):
            if self.default_game:
                result = func(self, *args, **kwargs)
                return result
            else:
                raise GameNotFoundError(f"Function {func.__name__} requires default game.")
        return wrapper

    def __init__(self, username, password, default_game=None):
        """
        Client for trading on Marketwatch games

        :param username: user username
        :param password: user password
        :param default_game: opt name of default game
        """
        self.session = requests.Session()
        self.authenticated = self.authenticate(username, password)
        self.games = self.get_all_games()
        self.set_default_game(default_game)

    def authenticate(self, username, password):
        """
        Authenticate client session

        :param username: user username
        :param password: user password
        :returns: bool True if authentication successful
        """
        # Create and send login page request
        csrf = Request(all_requests["csrf"])
        login_page_text = csrf.send_request(self.session).text

        # Get login payload
        b64data = re.search("Base64.decode\('(.+?)'\)\)\)\);", login_page_text).group(1)
        data = json.loads(base64.b64decode(b64data))
        client_id = data["clientID"]
        data = data["internalOptions"]
        data["client_id"] = client_id
        data["_csrf"] = self.session.cookies.get_dict()["_csrf"]

        # Create and send login request
        login = Request(all_requests["login"], 
            add_headers={
                "x-remote-user": username
            },
            add_payload={
                **data,
                **{
                    "username": username,
                    "password": password,
                    "headers": {"X-REMOTE-USER": username}
                }
            }
        ).send_request(self.session)

        # Get handler payload
        page = BeautifulSoup(login.text, "html.parser")
        try:
            handler_payload = {
                "token": page.find("input", {"name": "token"}).get("value"),
                "params": page.find("input", {"name": "params"}).get("value")
            }
        except AttributeError:
            raise UserNotFoundError("User not found with given username/password.")

        # Create and send handler request
        handler = Request(all_requests["handler"],
            add_payload=handler_payload)
        handler.send_request(self.session)

        return "djcs_session" in self.session.cookies.get_dict()

    def get_quote(self, ticker):
        """
        Get quote of stock

        :param ticker: ticker to retrieve fuid
        :returns: fuid as string
        """
        # Search for ticker information
        search_request = Request(all_requests["search"], 
            add_headers={"referer": f"https://www.marketwatch.com/game/{self.default_game}"},
            add_query={"q": ticker}
        ).send_request(self.session)
        search_results = json.loads(search_request.text)["symbols"]
        top_result = [r for r in search_results if r["ticker"] == ticker.upper()]

        # Raise error if no matching results
        if len(top_result) == 0:
            error_string = f"Ticker {ticker} not found."
            if len(search_results) != 0:
                error_string += f" Did you mean '{search_results[0]['ticker']}'?"

            raise TickerNotFoundError(error_string)    
        
        # Get fuid and payload
        quote_request = Request(all_requests["quoteByDialect"],
            add_headers = {"referer": f"https://www.marketwatch.com/game/{self.default_game}"},
            add_query = {"id": top_result[0]["chartingSymbol"]}
        ).send_request(self.session).text
        return json.loads(quote_request)

    @default_game_required
    @login_required
    def get_realtime_stock_price(self, ticker, verbose=False):
        """
        Generator function, returns realtime stock price

        :param ticker: ticker of stock
        :yields: price as updated from MW
        """
        # Get websocket Connection Token
        negotiate = Request(all_requests["negotiate"]).send_request(self.session).text
        connection_token = json.loads(negotiate)["ConnectionToken"]

        # Get all websocket channels from bg-quote elements
        quote = self.get_quote(ticker)
        charting_symbol = quote["InstrumentResponses"][0]["RequestId"]
        miniquote = Request(
            all_requests["miniquote"],
            add_url_fields = { "game_name": self.games[self.default_game] },
            add_query = { "chartingSymbol": charting_symbol }
        ).send_request(self.session).text
        miniquote_parse = BeautifulSoup(miniquote, "html.parser")
        bg_quotes = [bg.get("channel") for bg in miniquote_parse.find_all("bg-quote")]
        nonuq_channels = ",".join(bg_quotes).split(",") # Join comma-separated channels
        channels = list(set(nonuq_channels)) # Clear duplicates

        # Set up websocket
        price_stream_url = all_requests["priceStream"]["url"].format(connection_token=connection_token)
        if verbose:
            print(f"Setting up WebSocket at url {price_stream_url}...")
        ws = websocket.create_connection(price_stream_url)
        if verbose:
            print("WebSocket created successfully")
        
        # Queue of messages to send
        send_queue = [{"H": "mainhub", "M": "ping", "A": [], "I": 0}] + [
            {
                "H": "mainhub",
                "M": "subscribe",
                "A": [channel,"","0"]
            }
            for channel in channels
        ]

        # Complete introduction
        ws.recv()
        ws.send(json.dumps(send_queue.pop(0)))
        initial_time = time()

        # Once "I" messages are received, we can start
        i = 0
        i_received = False
        while True:
            # Receive a message
            try:
                receive = json.loads(ws.recv())
            except KeyboardInterrupt:
                ws.close()
                raise KeyboardInterrupt()
            if verbose:
                print(f"Received message: {receive}")

            if receive.get("I"):
                i = int(receive["I"])
                i_received = True
            else:
                # YIELD RETURN DATA
                yield receive

            # If applicable, send return message
            if i_received and len(send_queue) > 0:
                i_received = False
                message = send_queue.pop(0)
                message["I"] = i + 1
                if verbose:
                    print(f"Sending {message}...")

                ws.send(json.dumps(message))

            # If applicable queue up a reping message
            current_time = time()
            if current_time - initial_time > 30:
                send_queue.append({
                    "H":"mainhub",
                    "M":"ping",
                    "A":[],
                })
                initial_time = current_time

    @default_game_required
    @login_required
    def transact(self, ticker, quantity):
        """
        Make transaction to default game

        :param ticker: ticker to transact
        :param quantity: quantity to transact
        :returns: response from transaction request
        """
        quote = self.get_quote(ticker)
        fuid_link = quote["InstrumentResponses"][0]["Matches"][0]["Instrument"]["Debug"][3]
        fuid = fuid_link.split("fuid/")[1]

        # Make transaction
        tx_request = Request(all_requests["transaction"],
            add_headers = {"referer": f"https://www.marketwatch.com/games/{self.games[self.default_game]}"},
            add_payload = {
                "Fuid": fuid,
                "Shares": str(quantity),
                "Type": "Buy",
                "Term": "Cancelled"
            }
        ).send_request(self.session) # TODO Add term and type options
        tx_result = json.loads(tx_request.text)

        # Raise error if transaction not successful
        if not tx_result["succeeded"]:
            raise TransactionError(f"Transaction failed with message '{tx_result['message']}'")

        return tx_request

    @login_required
    def get_all_games(self):
        """
        Get all joined Marketwatch games

        :returns: list of names of all marketwatch games 
        """
        gamepage = Request(all_requests["games"]).send_request(self.session).text
        gamepage_parse = BeautifulSoup(gamepage, "html.parser")
        game_elems = list()

        for elem in gamepage_parse.find_all("a"):
            try:
                if elem["href"][27:34] == "/games/":
                    game_elems.append(elem)
            except KeyError:
                pass
        
        # Only the last half of the tags are just the actual names
        game_elems = game_elems[int(len(game_elems) / 2):]
        game_names = [tag.text for tag in game_elems] # Get names rather than tags
        return game_names

    def set_default_game(self, game):
        """
        Set default game

        :param game: name of game
        """
        # Set default game to user input, if none, set to the first game
        try:
            if len(self.games) > 0:
                self.default_game = self.games.index(game)
            else:
                print("WARNING: No games found, setting default game to None")
                self.default_game = None
        except ValueError:
            print(f"WARNING: Game {game} not found, setting to default {self.games[0]}")
            self.default_game = self.games[0]
            