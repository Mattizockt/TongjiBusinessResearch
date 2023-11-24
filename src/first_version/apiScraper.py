# scrapes information from the deviantart api 
# and stores it in the database with SQLManager
import requests

from .sqlManager import SQLManager


class APIScraper:
    def __init__(self, access_token):
        # TODO check token
        self._access_token = access_token
        self._manager = SQLManager("localhost", "root" ,"", "airesearch")

    # TODO if the error 429 is returned, the request rate has to be slowed.
    def get_users(self, usernames):

        # perhaps substitute through sql request later
        for user in usernames:
            url = f"https://www.deviantart.com/api/v1/oauth2/user/profile/{user}"
            data = {
                "access_token" : self._access_token,
                "username" : user,
                "ext_collections" : "false",
                "ext_galleries" : "yes"
            }
            params = {
                "expand" : "user.details,user.geo,user.stats"
            }

            user_file = requests.post(url, data=data, params=params).json()
            
            request_error = user_file.get("error", {})
            if  not request_error:
                self._manager.insert_user(user_file)
            elif user_file.get("error_description") == user_file.get("error_description"):
                print(f"Error when fetching resources for {user}")
                print(f" \" {user_file.get('error_description')} \" ")
            else:
                print(f"Error when requesting information for {user} from the API")
                print(user_file.get("error_description"))
    
    @property
    def access_token(self):
        return self._access_token
    
    @access_token.setter
    def access_token(self, value):
        self._access_token = value