# Python Marketwatch API

## Overview
An ongoing Python API for Marketwatch games/simulations. 

## Quickstart
This project requires Python3.

Get the project from git:

```git clone https://github.com/ProfJAT/marketwatch-api-py.git```

Install required libraries:

```pip install -r requirements.txt```

Utilize the API

```
from MWUser import MWUser

# Instatiate user
# User is authenticated by default
user = MWUser(username, password)

# Make transaction
# Transaction happens on defautl game
user.trasact("AAPL", 5)

# Get all Marketwatch games
print(user.get_all_games())
```
