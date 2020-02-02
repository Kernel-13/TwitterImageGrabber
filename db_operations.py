#  -*- coding: utf-8 -*-
'''
Created on 2 Apr 2018

@author: Kernel-13
'''

import os
import time

conn = sqlite3.connect('TwitterMediaGrabber.db')
cursor = conn.cursor()

#--------------------------- FIXES

def create_tables(cursor):
	cursor.execute("""CREATE TABLE IF NOT EXISTS LIKED_TWEETS (TWEET_ID NUMERIC(21,0), 
		TWEET_OWNER VARCHAR(30), 
		LIKE_OWNER VARCHAR(30), 
		DATE_POSTED VARCHAR(20), 
		TWEET_TEXT NVARCHAR(300))""")

	cursor.execute("""CREATE TABLE IF NOT EXISTS DOWNLOADED_TWEETS (TWEET_AUTHOR VARCHAR(30), 
		TWEET_ID NUMERIC(30,0),
		DATE_POSTED VARCHAR(20), 
		DATE_DOWNLOADED VARCHAR(20),
		COMMAND VARCHAR(100), 
		TWEET_TEXT NVARCHAR(300), 
		PRIMARY KEY (TWEET_AUTHOR, TWEET_ID))""")
	
	cursor.execute("""CREATE TABLE IF NOT EXISTS ERRORS_HISTORY (TWEET_AUTHOR VARCHAR(30), 
		STATUS VARCHAR(30), 
		ERROR_CODE VARCHAR(30), 
		DATE_ERROR VARCHAR(20))""")

	cursor.execute("""CREATE TABLE IF NOT EXISTS RENAMED_USERS_HISTORY (TWEET_AUTHOR_OLD VARCHAR(30) PRIMARY KEY, 
		TWEET_AUTHOR_NEW VARCHAR(30), 
		DATE_RENAME VARCHAR(20), 
		COMMAND VARCHAR(100))""")

	cursor.execute("""CREATE TABLE IF NOT EXISTS FUSED_USERS_HISTORY (TWEET_AUTHOR_OLD VARCHAR(30), 
		TWEET_AUTHOR_NEW VARCHAR(30), 
		DATE_FUSION VARCHAR(20))""")

	cursor.execute("""CREATE TABLE IF NOT EXISTS DELETED_USERS_HISTORY (TWEET_AUTHOR VARCHAR(30), DATE_DELETION VARCHAR(20))""")


def change_constraint_in_table():
	cursor.execute("CREATE TABLE IF NOT EXISTS renamed_users_history2(tweet_author_old VARCHAR(30), tweet_author_new VARCHAR(30), date_rename VARCHAR(20), command VARCHAR(100))")
	cursor.execute("INSERT INTO renamed_users_history2 (tweet_author_old, tweet_author_new, date_rename, command) SELECT tweet_author_old, tweet_author_new, date_rename, command FROM renamed_users_history")
	cursor.execute("DROP TABLE renamed_users_history")
	cursor.execute("ALTER TABLE renamed_users_history2 RENAME TO renamed_users_history")
	conn.commit()

#--------------------------- EXPERIMENTAL


### TESTING 
def check_if_users_from_folder_are_in_db(folder):
	dirs = [x.lower() for x in os.listdir(folder)]

	cursor.execute("SELECT * FROM twitter_users")
	for row in cursor.fetchall():
		if row[0].lower() in dirs:
			print(row[0])

#check_if_users_from_folder_are_in_db("C:\\Users\\funes\\Desktop\\DESKTOP HDD\\Kingston TMP\\NEW_SEARCH\\NO HOPE")

### Needs Check
def rescan_user(user):
	
	if not get_user(user): print(f"		### ERROR ### -- We couldn't find any user with the name {user} in the database!")
	else:
		usr_folder = os.walk(os.getcwd() + '\\' + user.lower())
		last_id = 0
		filename = ''
		for _, _, files in usr_folder:
			for file in files:
				data = file.split()
				if len(data) > 1:
					try:
						if int(data[1]) > last_id:
							last_id = int(data[1])
							filename = file
					except ValueError:
						pass

		try:				
			mod_date = ''
			date1 = time.strftime('%Y-%m-%d %X', time.gmtime(os.path.getatime(os.getcwd() + '\\' + str(user.lower()) + '\\' + filename) + 7200))
			date2 = time.strftime('%Y-%m-%d %X', time.gmtime(os.path.getmtime(os.getcwd() + '\\' + str(user.lower()) + '\\' + filename) + 7200))

			if date1 < date2:   mod_date = date1
			else: mod_date = date2

			cursor.execute("UPDATE twitter_users SET tweet_id=?,last_lookup=? WHERE lower(tweet_author)=?",(last_id, mod_date, user.lower(),))
			print("\nDatabase updated!")
			conn.commit()
		except FileNotFoundError:
	   		print("		### ERROR ### -- We couldn't find any files in this user's folder! (" + str(user) + ")")

### OK
def rescan_all():
	cursor.execute("SELECT * FROM twitter_users order by lower(tweet_author)")
	rows = cursor.fetchall()
	for row in rows:
		rescan_user(str(row[0]))