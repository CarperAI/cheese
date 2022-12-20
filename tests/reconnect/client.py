from cheese.api import CHEESEAPI

if __name__ == "__main__":
    print("Attempt connect")
    cheese = CHEESEAPI(debug = True)

    print(cheese.get_stats()["url"])
