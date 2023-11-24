# creates the databank and provides functions to access the databank
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import pandas as pd

class SQLManager:

    def __init__ (self, host_name, user_name, user_password, db_name):
        self.create_db_connection(host_name, user_name, user_password, db_name)

        self.create_users_table()
        self.create_deviations_table()

    def create_db_connection(self, host_name, user_name, user_password, db_name):
        self.connection = None
        try:
            self.connection = mysql.connector.connect( 
                host=host_name,
                user=user_name,
                passwd=user_password,
                database=db_name
            )
            print("MySQL Database connection successful")
        except Error as err:
            print(f"Error: '{err}'")

    def execute_query(self, query, dict_data={}):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, dict_data)
            self.connection.commit()
            print("Query successful")
        except Error as err:
            print(f"Error: '{err}'")

    # primary key
    # username 20 characters
    # location: longest location name, united kingdom
    # bio: doesn't work yet
    # missing: badges & groups
    # TODO restart table, since i changed username to unique
    def create_users_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(40) PRIMARY KEY,
            userid VARCHAR(36) UNIQUE NOT NULL,
            type VARCHAR(20),
            tagline VARCHAR(32),
            age INT,
            location VARCHAR(60),
            joindate VARCHAR(24),
            website VARCHAR(200),
            sex CHAR(1),
            bio TEXT,
            pageviews INT,
            deviations INT,
            watchers INT,
            watching INT,
            favorites INT,
            comm_made INT,
            comm_rec INT,
            badges_giv INT,
            badges_rec INT,
            groups_joined INT
        );
        """
        self.execute_query(query)

    # printid: find out meaning
    # views: has to be scraped with bot
    def create_deviations_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS deviations (
            deviationid VARCHAR(36) PRIMARY KEY,
            printid VARCHAR(36),
            url VARCHAR(255),
            title VARCHAR(255),
            likes INT,
            comments INT,
            views INT,
            category VARCHAR(255),
            category_path VARCHAR(255),
            authorid VARCHAR(36) NOT NULL,
            is_downloadable VARCHAR(36),
            src TEXT,

            CONSTRAINT fk_deviations_users 
            FOREIGN KEY (authorid) REFERENCES users(username) ON DELETE CASCADE
        );
        """
        self.execute_query(query)
    
    # TODO what happens, if we want to insert element that already exists?
    # right now, we just overwrite the entry
    def insert_user(self, user_file):
        user_obj = user_file.get("user", {})

        data_to_insert = {
            'username' : self._convert_to_lowercase(user_obj.get("username", None)),
            'userid' : user_obj.get("userid", None),
            'type' : user_obj.get("type", None),
            'tagline' : user_file.get("tagline", None),
            'age' : user_obj.get("details", {}).get("age", None),
            'location' : user_obj.get("geo", {}).get("country", None),
            'joindate' : user_obj.get("details", {}).get("joindate", None),
            'website' : user_file.get("website", None),
            'sex' : user_obj.get("details", {}).get("sex", None),
            'bio' : self._extract_text_from_html(user_file.get("bio", None)), # doesn't work, error from server side
            'pageviews' : user_file.get("stats", {}).get("profile_pageviews", None),
            'deviations' : user_file.get("stats", {}).get("user_deviations", None),
            'watchers' : user_obj.get("stats", {}).get("watchers", None),
            'watching' : user_obj.get("stats", {}).get("friends", None),
            'favorites' : user_file.get("stats", {}).get("user_favourites", None),
            'comm_made' : user_file.get("stats", {}).get("user_comments", None),
            'comm_rec' : user_file.get("stats", {}).get("profile_comments", None)
        }

        query = """
        INSERT INTO users (
            username, userid, type, tagline, age, location, joindate,
            website, sex, bio, pageviews, deviations, watchers, watching, 
            favorites, comm_made, comm_rec
        )
        VALUES (
            %(username)s, %(userid)s, %(type)s, %(tagline)s, %(age)s, %(location)s, %(joindate)s,
            %(website)s, %(sex)s, %(bio)s, %(pageviews)s, %(deviations)s, %(watchers)s, %(watching)s,
            %(favorites)s, %(comm_made)s, %(comm_rec)s
        )
        ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            userid = VALUES(userid),
            type = VALUES(type),
            tagline = VALUES(tagline),
            age = VALUES(age),
            location = VALUES(location),
            joindate = VALUES(joindate),
            website = VALUES(website),
            sex = VALUES(sex),
            bio = VALUES(bio),
            pageviews = VALUES(pageviews),
            deviations = VALUES(deviations),
            watchers = VALUES(watchers),
            watching = VALUES(watching),
            favorites = VALUES(favorites),
            comm_made = VALUES(comm_made),
            comm_rec = VALUES(comm_rec);
        """
        self.execute_query(query, data_to_insert)

    def update_with_user_scrape(self, username, badges_rec, badges_giv, groups_joined):
        data_to_insert = {
            "username" : username,
            "badges_giv" : badges_giv,
            "badges_rec" : badges_rec,
            "groups_joined" : groups_joined
        }

        query = """
        UPDATE users SET
            badges_giv = %(badges_giv)s,
            badges_rec = %(badges_rec)s,
            groups_joined = %(groups_joined)s
        WHERE
            username = %(username)s
        ;
        """
        self.execute_query(query, data_to_insert)

    def remove_user(self, username):
        data_to_insert = {'username' : username}

        query = """
        DELETE FROM users
        WHERE 
            username = %(username)s;
        """
        self.execute_query(query, data_to_insert)

    def _convert_to_lowercase(self, input_string):
        if input_string is not None:
            return input_string.lower()
        else:
            return None

    def _extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        text = [paragraph.get_text() for paragraph in soup.find_all("div", class_="daeditor-paragraph")]
        return " ".join(text)
    
