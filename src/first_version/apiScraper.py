# scrapes information from the deviantart api 
# and stores it in the database with SQLManager
import time
import requests
import logging
from .sqlManager import SQLManager
import random


class APIScraper:

    def __init__(self, access_token):
        self._access_token = access_token
        self._manager = SQLManager("localhost", "root" ,"", "airesearch")
    
    @property
    def manager(self):
        return self._manager
    
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
     
    # maybe check if author still exist first
    def get_deviations(self, usernames):
        lower_date_bound = 1625068800 # july 2021
        upper_date_bound  = 1688140800 # july 2023
    
    def get_author_deviations(self, username):
        low_date = 1625068800 # july 2021
        high_date  = 1688140800 # july 2023
        low_index, high_index = self._search_correct_deviation_range(username, low_date, high_date)

        if low_index == high_index:
            logging.info(f"User {username} has no deviations in the specified time range {low_index} to {high_index}")
            return
        elif low_index is None or high_index is None:
            logging.error(f"Not collection user {username}'s deviation because low_index or high_index is None.")
            return
        else:
            logging.info(f"found time range of deviations for user {username}: from offset {low_index} to offset {high_index}.")

        index_lst = self._sample_integers(low_index, high_index)
        for inner_lst in index_lst:
            deviations, _ = self._req_dev(username, len(inner_lst), inner_lst[0])
            for deviation in deviations: 
                self._manager.insert_deviation(deviation)

    def _search_correct_deviation_range(self, username, low_target, high_target):
        # minimal and maximal offset
        low = 0
        high = 50000

        # perhaps store old values to save time?
        low_index = self._dev_binary_search(username, low_target, low, high, round_down=False)
        high_index = self._dev_binary_search(username, high_target, low, high)
        
        return low_index, high_index
        
    def _dev_binary_search(self, username, target, low, high):
        last_index = -1

        while low <= high:
            mid = (low + high) // 2
            result, _ = self._req_dev(username, 1, mid)

            if result is None:
                logging.error(f"Error when fetching the bound {target} of deviations for user {username}")
                return None
        
            if result == []:
                high = mid - 1
                continue

            dev = result[0] if result else None
            deviation_date = int(dev["published_time"])

            if deviation_date == target:
                last_index = mid
                break
            elif deviation_date > target:
                last_index = mid
                low = mid + 1
            else:
                last_index = mid
                high = mid - 1

        return last_index if last_index != -1 else secondary_index

    def _req_dev(self, username, limit, offset): 
        url = "https://www.deviantart.com/api/v1/oauth2/gallery/all"
        params = {
                "access_token": self._access_token,
                "username": username,
                "limit" : limit,
                "offset" : offset,
                "mature_content" : "true",
        }

        req_json = self._make_api_call(url, params)
        results = req_json.get("results", {})

        if results == []:
            logging.info(f"User {username} has no deviations with offset {offset}.")
            return (results, False)

        request_error = req_json.get("error", {})
        if request_error:
            logging.error(f"Error when fetching user {username} deviations, offset: {offset}, error: {req_json.get('error_description')}")
            return (None, None)
        
        logging.info(f"Successfully fetched information about user {username}'s deviations from API with offset: {offset}")
        
        # (deviations, has_more)
        return (req_json["results"], req_json["has_more"]) 
    
    def _sample_integers(self, low, high, sample_count=100):
        unique_integers = min(high - low + 1, sample_count)
        sampled_numbers = sorted(random.sample(range(low, high + 1), unique_integers))
        
        grouped_numbers = []
        current_group = []
        
        for num in sampled_numbers:
            if not current_group or num == current_group[-1] + 1:
                current_group.append(num)
            else:
                grouped_numbers.append(current_group)
                current_group = [num]

        if current_group:
            grouped_numbers.append(current_group)
        
        return grouped_numbers

    def _make_api_call(self, url, params):
            retry_count = 0
            max_retries = 3

            req_json = None
            while retry_count < max_retries:

                try:
                    request = requests.post(url, params=params)
                    
                    if request.status_code == 429:
                        wait_time = 2**retry_count
                        logging.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds.")
                        time.sleep(wait_time)
                        retry_count += 1
                    elif request.status_code == 404:
                        logging.warning(f"Server returned 404 with url {url} with params {params}")
                        req_json = request.json()
                    else:
                        req_json = request.json()
                        break

                except requests.RequestException as e:
                    logging.error(f"Error during request: {e}")

            return req_json

