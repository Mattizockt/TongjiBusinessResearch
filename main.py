import threading
import src.first_version as src
import logging

def main():
    # retrieve access token
    authObject = src.Authenticate()
    access_token = authObject.access_token

    auto_refresh_thread = threading.Thread(target=authObject.auto_refresh) 
    auto_refresh_thread.start()

    users = []
    with open("data/testData/users.txt", "r") as file:
        users = [line.strip() for line in file.readlines()]

    api_scraper = src.APIScraper(access_token)
    api_scraper.get_users(users)

    print("Finished collecting data. You can stop the programme now.")

    # wait till thread finishes
    auto_refresh_thread.join()

if __name__ == "__name__":
    main()