# scrapes information from the deviantart api 
# and stores it in the database with SQLManager
import sys
import time
import requests
import logging
from .sqlManager import SQLManager


class APIScraper:
    def __init__(self, access_token):
        self._access_token = access_token
        self._manager = SQLManager("localhost", "root" ,"", "airesearch")
    
    def get_users(self, usernames):
        for username in usernames:
            url = f"https://www.deviantart.com/api/v1/oauth2/user/profile/{username}"
            data = {
                "access_token": self._access_token,
                "username": username,
                "ext_collections": "false",
                "ext_galleries": "yes"
            }
            params = {
                "expand": "user.details,user.geo,user.stats"
            }

            retry_count = 0
            max_retries = 3

            user_file = None
            while retry_count < max_retries:
                request = requests.post(url, data=data, params=params)

                if request.status_code == 429:
                    wait_time = 2**retry_count
                    logging.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds.")
                    time.sleep(wait_time)
                    retry_count += 1
                else:
                    user_file = request.json()
                    break
            
            assert(user_file != None)        

            request_error = user_file.get("error", {})
            if not request_error:
                logging.info(f"Fetched information for user {username} from the API.")
                self._manager.insert_user(user_file)
            else:
                logging.error(f"Error when fetching resources for user {username}: {user_file.get('error_description')}")
     
    # TODO catch the exception in case request doesnt connect
    def get_deviations(self, username):
        lower_date_bound = 1625068800 # july 2021
        upper_date_bound  = 1688140800 # july 2023

        offset = 0
        limit = 24
        has_more = True
        finished = False

        while (has_more and not finished):

            url = "https://www.deviantart.com/api/v1/oauth2/gallery/all"
            params = {
                    "access_token": self._access_token,
                    "username": username,
                    "limit" : limit,
                    "offset" : offset,
                    "mature_content" : "true",
            }

            retry_count = 0
            max_retries = 3

            req_json = None
            while retry_count < max_retries:
                request = requests.post(url, params=params)
                
                if request.status_code == 429:
                    wait_time = 2**retry_count
                    logging.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds.")
                    time.sleep(wait_time)
                    retry_count += 1
                else:
                    req_json = request.json()
                    break
            
            assert(req_json != None)

            deviations = req_json["results"]
            offset += len(deviations)
            has_more = req_json["has_more"]
            
            for dev in deviations:
                published_time = dev["published_time"]

                if published_time < lower_date_bound:
                    finished = True
                    break

                if published_time <= upper_date_bound:
                    self._manager.insert_deviation(dev)

    @property
    def access_token(self):
        return self._access_token
    
    @access_token.setter
    def access_token(self, value):
        self._access_token = value