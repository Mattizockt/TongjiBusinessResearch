# creates the databank and provides functions to access the databank
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import pandas as pd
import logging

class SQLManager:

    def __init__ (self, host_name, user_name, user_password, db_name):
        self._create_db_connection(host_name, user_name, user_password, db_name)

        self.create_users_table()
        self.create_deviations_table()

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
        logging.info("Initializing users table.")
        self._execute_query(query)

    # printid: find out meaning
    # views, ai_marked: has to be scraped with bot
    # restart table
    def create_deviations_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS deviations (
            deviationid VARCHAR(36) PRIMARY KEY,
            printid VARCHAR(36),
            url VARCHAR(255),
            title VARCHAR(255),
            favourites INT,
            comments INT,
            views INT,
            category VARCHAR(255),
            category_path VARCHAR(255),
            author_username VARCHAR(40) NOT NULL,
            is_downloadable VARCHAR(36),
            src TEXT,
            published_time VARCHAR(11),
            ai_marked BOOLEAN,

            CONSTRAINT fk_deviations_users
            FOREIGN KEY (author_username) REFERENCES users(username) ON DELETE CASCADE
        );
        """
        logging.info("Initializing deviations table.")
        self._execute_query(query)
    
    def insert_deviation(self, dev_file):
        assert(isinstance(dev_file, dict))

        deviationid =  dev_file.get("deviationid", None)
        data_to_insert = {
            "deviationid" : deviationid,
            "printid" : dev_file.get("printid", None),
            "url" : dev_file.get("url", None),
            "title" : dev_file.get("title", None),
            "favourites" : dev_file.get("stats", {}).get("favourites", None),
            "comments" : dev_file.get("stats", {}).get("comments", None),
            "author_username" : dev_file.get("author", {}).get("username", None),
            "category" : dev_file.get("category", None),
            "category_path" : dev_file.get("category_path", None),
            "is_downloadable" : dev_file.get("is_downloadable", None),
            "published_time" : dev_file.get("published_time", None),
            "src" : dev_file.get("content",{}).get("src", None)
        }

        query = """
            INSERT INTO deviations (
                deviationid, printid, url, title, favourites, comments, author_username,
                category, category_path, is_downloadable, published_time, src
            )
            VALUES (
                %(deviationid)s, %(printid)s, %(url)s, %(title)s, %(favourites)s, 
                %(comments)s, %(author_username)s, %(category)s, %(category_path)s, 
                %(is_downloadable)s, %(published_time)s, %(src)s
            )
            ON DUPLICATE KEY UPDATE
                deviationid = VALUES(deviationid),
                printid = VALUES(printid),
                url = VALUES(url),
                title = VALUES(title),
                favourites = VALUES(favourites),
                comments = VALUES(comments),
                author_username = VALUES(author_username),
                category = VALUES(category),
                category_path = VALUES(category_path),
                is_downloadable = VALUES(is_downloadable),
                src = VALUES(src),
                published_time = VALUES(published_time);
        """
        logging.info(f"Inserting information for deviation {deviationid} into deviations from the deviation API.")
        self._execute_query(query, data_to_insert)
        
    def insert_user(self, user_file):
        assert(isinstance(user_file, dict))

        user_obj = user_file.get("user", {})
        username = self._convert_to_lowercase(user_obj.get("username", None))

        data_to_insert = {
            'username' : username,
            'userid' : user_obj.get("userid", None),
            'type' : user_obj.get("type", None),
            'tagline' : user_file.get("tagline", None),
            'age' : user_obj.get("details", {}).get("age", None),
            'location' : user_obj.get("geo", {}).get("country", None),
            'joindate' : user_obj.get("details", {}).get("joindate", None),
            'website' : user_file.get("website", None),
            'sex' : user_obj.get("details", {}).get("sex", None),
            'bio' : self._extract_text_from_html(user_file.get("bio", None)), # TODO doesn't work, error from server side
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
        logging.info(f"Inserting information for user {username} into users from the deviation API.")
        self._execute_query(query, data_to_insert)

    def update_with_user_scrape(self, username, badges_rec, badges_giv, groups_joined, bio):
        data_to_insert = {
            "username" : username,
            "badges_giv" : badges_giv,
            "badges_rec" : badges_rec,
            "groups_joined" : groups_joined,
            "bio" : bio
        }

        query = """
        UPDATE users SET
            badges_giv = %(badges_giv)s,
            badges_rec = %(badges_rec)s,
            groups_joined = %(groups_joined)s,
            bio = %(bio)s
        WHERE
            username = %(username)s
        ;
        """
        logging.info(f"Updating user {username} in users with scraped information.")
        self._execute_query(query, data_to_insert)

    def remove_user(self, username):
        data_to_insert = {'username' : username}

        query = """
        DELETE FROM users
        WHERE 
            username = %(username)s;
        """
        logging.info(f"Removed user {username} from users.")
        self._execute_query(query, data_to_insert)
    
    def _create_db_connection(self, host_name, user_name, user_password, db_name):
        self.connection = None
        try:
            self.connection = mysql.connector.connect( 
                host=host_name,
                user=user_name,
                passwd=user_password,
                database=db_name
            )
            logging.info(f"MySQL Database connection with {db_name} successful.")

        except Error as err:
            logging.error(f"Error when connecting with databank {db_name}: {err}.")
   
    def _execute_query(self, query, dict_data={}):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, dict_data)
            self.connection.commit()
            
        except Error as err:
            logging.error(f"Error when excuting query {query} : {err}.")

    def _convert_to_lowercase(self, input_string):
        if input_string is not None:
            return input_string.lower()
        else:
            return None

    def _extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        text = [paragraph.get_text() for paragraph in soup.find_all("div", class_="daeditor-paragraph")]
        return " ".join(text)
    
