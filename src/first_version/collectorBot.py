from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from sqlManager import SQLManager
import logging

def main():
    sqlManager = SQLManager("localhost", "root" ,"", "airesearch")
    cB = CollectorBot(sqlManager)

    # TODO add loging config to __init__ later 
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="basic.log",
        force=True
    )

    users = []
    with open("data/testData/users.txt", "r") as file:
            users = [line.strip() for line in file.readlines()]
    
    for user in users:
        cB.get_user_information(user)

class CollectorBot:

    def __init__(self, sqlManager):
        assert(isinstance(sqlManager, SQLManager))
        self._sqlManager = sqlManager

        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self._driver.set_page_load_timeout(5000)

    def get_user_information(self, username):
        assert(isinstance(username, str))

        logging.info(f"Processing user information for {username}.")

        try: 
            self._driver.get(f"https://www.deviantart.com/{username}/about")

        except TimeoutException as e:
            logging.error(f"Page load timeout for user {username}: {e}")

        try:
            if self._verify_user_status(username):
                badges_giv, badges_rec = self._get_badges_info(username)
                groups_joined = self._get_groups_info(username)
                bio = self._get_user_bio(username)

                self._sqlManager.update_with_user_scrape(username, badges_rec, badges_giv, groups_joined, bio)

        except Exception as e:
            logging.error(f"Error processing user information for user {username}: {str(e)}")

    def _verify_user_status(self, username):
        if "Deactivated Account" in self._driver.title:
            logging.warning(f"User {username} has a deactivated account. Removing from the database.")
            self._sqlManager.remove_user(username)
            return False
        return True

    def _get_badges_info(self, username):
        xpath = "//div[@class='_6Syj_']//strong"
        num_badges_elem = self._driver.find_elements(By.XPATH, xpath)

        if len(num_badges_elem) != 2:
            logging.info(f"No information available to User {username}'s number of badges.")
            return None, None

        badges_giv = self._convert_K_str_to_int(num_badges_elem[0].get_attribute("title"))
        badges_rec = self._convert_K_str_to_int(num_badges_elem[1].get_attribute("title"))

        logging.info(f"Users {username}'s badges: Given - {badges_giv}, Received - {badges_rec}")
        return badges_giv, badges_rec

    def _get_groups_info(self, username):
        try:
            xpath = "//section[@id='group_list_members']//div[@class='HhEXv' and contains(text(), 'Group')]"
            num_groups_elem = self._driver.find_element(By.XPATH, xpath).text.split(" ")
            return self._convert_K_str_to_int(num_groups_elem[0])

        except NoSuchElementException:
            logging.info(f"No information available for User {username}'s  joined groups.")
            return None

    def _get_user_bio(self, username):
        try:
            xpath = "//p[@class='mm8Nw _1j-51 _35HYg _1oBmu _1FoOD _3M0Fe public-DraftStyleDefault-block-depth0 public-DraftStyleDefault-text-ltr']"
            bio_elem = self._driver.find_elements(By.XPATH, xpath)

            bio = "".join(x.text for x in bio_elem)
            logging.info(f"User {username}'s bio: {bio}")
            return bio

        except NoSuchElementException:
            logging.info(f"User {username} doesn't have a bio.")
            return None

    def _convert_K_str_to_int(self, s):
        assert(isinstance(s, str))

        multiplier = 1

        if 'K' in s:
            multiplier = 1000
            s = s.replace('K', '')

        return int(float(s) * multiplier)

if __name__ == '__main__':
    main()  
