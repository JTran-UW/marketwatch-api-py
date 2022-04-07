import requests
import base64
import re
import json
from bs4 import BeautifulSoup

# My libraries
from mw_requests.Request import Request
from mw_requests.Errors import *

with open("mw_requests/requests.json", "r") as f:
    all_requests = json.load(f)["userRequests"]

class MWUser:
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
        login_page_text = csrf.send_session_request(self.session).text

        # Get login payload
        b64data = re.search("Base64.decode\('(.+?)'\)\)\)\);", login_page_text).group(1)
        data = json.loads(base64.b64decode(b64data))
        client_id = data["clientID"]
        data = data["internalOptions"]
        data["client_id"] = client_id

        # Create and send login request
        wresult = Request(all_requests["login"], 
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
        ).send_session_request(self.session)

        # Get callback payload
        page = BeautifulSoup(wresult.text, "html.parser")
        inputs = page.find_all("input")
        callback_payload = dict()
        for i in inputs[:3]:
            name = i["name"]
            value = i["value"]
            callback_payload[name] = value

        # Create and send callback request
        callback_request = Request(all_requests["callback"],
            add_payload=callback_payload)
        callback_request.send_session_request(self.session)

        return "djcs_session" in self.session.cookies.get_dict()

    @default_game_required
    @login_required
    def transact(self, ticker, quantity):
        """
        Make transaction to default game

        :param ticker: ticker to transact
        :param quantity: quantity to transact
        :returns: response from transaction request
        """
        # Search for ticker information
        search_request = Request(all_requests["search"], 
            add_headers={"referer": f"https://www.marketwatch.com/game/{self.default_game}"},
            add_query={"q": ticker}
        ).send_session_request(self.session)
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
        ).send_session_request(self.session)
        fuid_link = json.loads(quote_request.text)["InstrumentResponses"][0]["Matches"][0]["Instrument"]["Debug"][3]
        fuid = fuid_link.split("fuid/")[1]

        # Make transaction
        tx_request = Request(all_requests["transaction"],
            add_headers = {"referer": f"https://www.marketwatch.com/game/{self.default_game}"},
            add_payload = {
                "Fuid": fuid,
                "Shares": str(quantity),
                "Type": "Buy",
                "Term": "Cancelled"
            }
        ).send_session_request(self.session) # TODO Add term and type options
        tx_result = json.loads(tx_request.text)

        # Raise error if transaction not successful
        if not tx_result["succeeded"]:
            raise TransactionError(f"Transaction failed with message {tx_result['message']}")

        return tx_request

    @login_required
    def get_all_games(self):
        """
        Get all joined Marketwatch games

        :returns: list of names of all marketwatch games 
        """
        gamepage = Request(all_requests["games"]).send_session_request(self.session).text
        soup = BeautifulSoup(gamepage, "html.parser")
        game_elems = list()

        for elem in soup.find_all("a"):
            try:
                if elem["href"][27:33] == "/game/":
                    game_elems.append(elem)
            except KeyError:
                pass
        
        # Only the last half of the tags are just the actual names
        game_elems = game_elems[int(len(game_elems) / 2):]
        game_names = [tag.text for tag in game_elems] # Get names rather than tags
        return game_names

    @default_game_required
    @login_required
    def get_realtime_stock_price(self):
        """
        Get stock price realtime via generator

        :param stock: ticker of stock
        :yields: price as updated from MW
        """
        ps_request = Request(all_requests["priceStream"]).send_session_request(self.session)
        print(ps_request.content) # TODO figure this out

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

with open("login.json", "r") as f:
    user = json.load(f)
    username = user["username"]
    password = user["password"]

my_user = MWUser(username, password, default_game="mw-api-test")
my_user.get_realtime_stock_price()
