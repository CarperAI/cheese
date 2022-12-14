from cheese.api import CHEESEAPI
import time

if  __name__ == "__main__":
    api = CHEESEAPI(timeout = 10)
    print("Connected to server")
    print(api.launch())
    time.sleep(1)
    print("adding client")
    print(api.create_client(1))

    _ = input("Press enter to view stats")

    print(api.get_stats()["client_stats"])