from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from sqlManager import SQLManager

def main():
    sqlManager = SQLManager("localhost", "root" ,"", "airesearch")
    cB = CollectorBot(sqlManager)

    users = []
    with open("data/testData/users.txt", "r") as file:
            users = [line.strip() for line in file.readlines()]
    
    for user in users:
        cB.user_information(user)

# TODO what to do next, make sure that if there's a timeout
# when using a vpn, the program does not crashes.
# also maybe insert -1 if the users does not display their values to differenitate from
# people that are just losers
# also check if losers have the same "symptome" (you can't see their badges) as "edgy" people
class CollectorBot:

    def __init__(self, sqlManager):
        assert(isinstance(sqlManager, SQLManager))
        self._sqlManager = sqlManager

        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    
    def user_information(self, username):
        assert isinstance(username, str)

        self._driver.get(f"https://www.deviantart.com/{username}/about")
        
        # verify that user is not blocked, otherwise, remove from database
        if "Deactivated Account" in self._driver.title:
            self._sqlManager.remove_user(username)

        # number of badges gave, received
        badges_giv = None
        badges_rec = None
        try: 
            xpath_num_badges = "//div[@class='_6Syj_']//strong"
            num_badges_elem = self._driver.find_elements(By.XPATH, xpath_num_badges)
            if num_badges_elem == []:
                raise NoSuchElementException()
            
            assert(len(num_badges_elem) == 2)

            badges_giv = self.convert_K_str_to_int(num_badges_elem[0].get_attribute("title"))
            badges_rec = self.convert_K_str_to_int(num_badges_elem[1].get_attribute("title"))
            print(badges_giv, badges_rec)

        except NoSuchElementException:
            print(f"user {username} does not display his received badges.")

        # number of groups that are joined.
        groups_joined = None
        try:
            xpath_num_groups = "//section[@id='group_list_members']//div[@class='HhEXv' and contains(text(), 'Groups')]"
            num_groups_elem = self._driver.find_element(By.XPATH, xpath_num_groups).text.split(" ")
            assert(len(num_groups_elem) == 2)

            groups_joined = self.convert_K_str_to_int(num_groups_elem[0])
            print(groups_joined)
            
        except NoSuchElementException:
            print(f"user {username} does not display the groups he has joined")

        # insert badge and group details
        self._sqlManager.update_with_user_scrape(username, badges_rec, badges_giv, groups_joined)


    def convert_K_str_to_int(self, s):
        assert(isinstance(s, str))

        multiplier = 1

        if 'K' in s:
            multiplier = 1000
            s = s.replace('K', '')

        return int(float(s) * multiplier)

if __name__ == '__main__':
    main()  
