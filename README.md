# Python Marketwatch API

## Overview
An ongoing Python API for Marketwatch games/simulations. 

The current version is a work in progress.

## Quickstart
This project requires Python3.

Get the project from git:

```git clone https://github.com/ProfJAT/marketwatch-api-py.git```

Install required libraries:

```pip install -r requirements.txt```

Utilize the API

```
from src.User import User

username = "[YOUR USERNAME]"
password = "[YOUR PASSWORD]"

# Instatiate user
# User is authenticated by default
user = User(username, password)

# Get realtime stock price, use Ctrl+C to stop
for price in user.get_realtime_stock_price("AAPL"):
    print(price)

# Make transaction
# Transaction happens on default game
user.trasact("AAPL", 5)

# Get all Marketwatch games
print(user.get_all_games())
```
