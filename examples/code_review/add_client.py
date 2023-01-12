from cheese.api import CHEESEAPI
import time

api = CHEESEAPI(
    timeout = 10,
    host = 'localhost',
    port = 5672
)

# Can now use API as we'd expect

# Trying to launch when already launched will cause an error
# So ensure that the server did not call launch beforehand
#api.launch()
stats = api.get_stats()

# If you need the URL after launching, you can access it from stats
url = stats["url"]

usr, passwd = api.create_client(1)

while True:
    time.sleep(10)
    stats = api.get_stats()
    if stats["finished"]:
        break
