# scrapes information from the deviantart api 
# and stores it in the database with SQLManager
import requests
import logging
from .sqlManager import SQLManager


class APIScraper:
    def __init__(self, access_token):
        self._access_token = access_token
        self._manager = SQLManager("localhost", "root" ,"", "airesearch")

    # TODO if the error 429 is returned, the request rate has to be slowed.
    def get_users(self, usernames):

        for username in usernames:
            url = f"https://www.deviantart.com/api/v1/oauth2/user/profile/{username}"
            data = {
                "access_token" : self._access_token,
                "username" : username,
                "ext_collections" : "false",
                "ext_galleries" : "yes"
            }
            params = {
                "expand" : "user.details,user.geo,user.stats"
            }

            user_file = requests.post(url, data=data, params=params).json()
            
            request_error = user_file.get("error", {})
            if  not request_error:
                logging.info(f"Fetched information for user {username} from the API.")
                self._manager.insert_user(user_file)
            else:
                logging.error(f"Error when fetching resources for user {username}: {user_file.get('error_description')}")
    
    @property
    def access_token(self):
        return self._access_token
    
    @access_token.setter
    def access_token(self, value):
        self._access_token = value