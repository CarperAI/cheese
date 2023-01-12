from cheese.api import CHEESEAPI

api = CHEESEAPI(
    timeout = 10,
    host = 'localhost',
    port = 5672
)

api.launch()
