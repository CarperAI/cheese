from cheese.api import CHEESEAPI

# With multiple clients, test if a client can close window, login again
# and get their data back without affecting any other clients

if __name__ == "__main__":
    cheese = CHEESEAPI(debug = True)

    cheese.create_client(1)
    cheese.create_client(2)