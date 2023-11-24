# used to retrieve and refresh the access token for the api calls
import time
import requests
import schedule
import logging

class Authenticate:

    def __init__(self):
        self.authorize()
        self.request_access_token()
    
    def authorize(self):  
        url = "https://www.deviantart.com/oauth2/authorize?response_type=code&client_id=29751&redirect_uri=http://localhost:3000/callback&scope=browse"
        print(f"Please go to {url}\n")

    # TODO check token
    def request_access_token(self):
        code = input("Please input the code: ")
        url = "https://www.deviantart.com/oauth2/token"
        data = {
            "redirect_uri": "http://localhost:3000/callback",
            "code": code,
            "grant_type": "authorization_code",
            "client_id": "29751",
            "client_secret": "748d42f4d4b16e2c321f417ee242e2bc",
            "redirect_uri": "http://localhost:3000/callback"
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            response_json = response.json()
            self._access_token = response_json["access_token"]
            self._refresh_token = response_json["refresh_token"]
            logging.info(f"Access token successfully requested.")

        except requests.exceptions.RequestException as e:
            logging.error(f"Error when requesting an access token: {e}.")

    def auto_refresh(self):
        schedule.every(55).minutes.do(self.refresh_access_token)
        while True:
            schedule.run_pending()
            time.sleep(10)

    def refresh_access_token(self):
        url = "https://www.deviantart.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": "29751",
            "client_secret": "748d42f4d4b16e2c321f417ee242e2bc",
            "refresh_token": self._refresh_token
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            response_json = response.json()
            self._access_token = response_json["access_token"]
            self._refresh_token = response_json["refresh_token"]
            logging.info("Successfully refreshed access token.")

        except requests.exceptions.RequestException as e:
            logging.error(f"Error when refreshing access token: {e}.")

    @property
    def access_token(self):
        return self._access_token
    
    @property
    def refresh_token(self):
        return self._refresh_token