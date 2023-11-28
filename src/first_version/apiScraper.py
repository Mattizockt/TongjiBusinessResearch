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
            params = {
                "access_token": self._access_token,
                "username": username,
                "ext_collections": "false",
                "ext_galleries": "false",
                "expand" : "user.details,user.geo,user.stats"
            }

            req_json = self._make_api_call(url, params)

            if req_json is None:
                logging.error("API call returned None.")

            request_error = req_json.get("error", {})
            if not request_error:
                logging.info(f"Fetched information for user {username} from the API.")
                self._manager.insert_user(req_json)
            else:
                logging.error(f"Error when fetching resources for user {username}: {req_json.get('error_description')}")
     
    # TODO make username into array
    def get_deviations(self, usernames):

        lower_date_bound = 1625068800 # july 2021
        upper_date_bound  = 1688140800 # july 2023
        limit = 24

        for username in usernames:
            offset = 0
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

                # TODO don't terminate project if there is a request error.
                req_json = self._make_api_call(url, params)

                if req_json == None:
                    continue

                request_error = req_json.get("error", {})
                if request_error:
                    logging.error(f"Error when fetching user {username} deviations, offset: {offset}, error: {req_json.get('error_description')}")
                    return
                
                logging.info(f"Successfully fetched information about user {username}'s deviations from API with offset: {offset}")

                deviations = req_json["results"]
                offset += len(deviations)
                has_more = req_json["has_more"]
                
                for dev in deviations:
                    published_time = int(dev["published_time"])

                    if published_time < lower_date_bound:
                        finished = True
                        break

                    if published_time <= upper_date_bound:
                        self._manager.insert_deviation(dev)

    def _make_api_call(self, url, params):
            retry_count = 0
            max_retries = 3

            req_json = None
            while retry_count < max_retries:

                try:
                    request = requests.post(url, params=params)

                    # TODO when the user is not available, this raises an error
                    # request.raise_for_status()  # Raise HTTPError for bad responses
                    # because the server return 404 as an error code. perhaps include for error searching??

                    if request.status_code == 429:
                        wait_time = 2**retry_count
                        logging.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds.")
                        time.sleep(wait_time)
                        retry_count += 1
                    else:
                        req_json = request.json()
                        break

                except requests.RequestException as e:
                    logging.error(f"Error during request: {e}")
                    return

            return req_json


    @property
    def manager(self):
        return self._manager