import time
import logging
import Queries.selectQueries as SQ

def insert_new_user(cursor, user, last_id=0, last_lookup=''):
	if not SQ.get_user(user):
		if last_lookup != '' and last_id != 0: 	
			cursor.execute("INSERT INTO TWITTER_USERS VALUES(?,?,?,?)", (user.lower(), 'Active', last_id, last_lookup,) )
		else: 	
			cursor.execute("INSERT INTO TWITTER_USERS VALUES(?,?,?,?)", (user.lower(), 'Not Accessible', last_id, time.strftime('%Y-%m-%d %X', time.localtime()),) )

		print('\nAdded [ {} ] to the database'.format(user))
		conn.commit()

#	OK
def insert_download(cursor, tweet, command):
    cursor.execute("INSERT INTO DOWNLOADED_TWEETS VALUES(?,?,?,?,?,?)", (
    	tweet.author.screen_name,
    	int(tweet.id),
    	tweet.created_at.strftime('%Y-%m-%d %X'),
    	time.strftime('%Y-%m-%d %X', time.localtime()),
    	command,
    	tweet.full_text,))
    conn.commit()

#	OK
def insert_error_history(cursor, tweet_author, status, error_code):
	cursor.execute("UPDATE ERRORS_HISTORY SET STATUS='{}', ERROR_CODE='{}', DATE_ERROR='{}' WHERE lower(TWEET_AUTHOR)='{}'".format(
		status, 
		error_code, 
		time.strftime('%Y-%m-%d %X', time.localtime()), 
		tweet_author.lower()))
	conn.commit()

#	OK
def insert_deleted_history(cursor, tweet_author):
	cursor.execute("INSERT INTO DELETED_USERS_HISTORY VALUES(?,?)", (
		tweet_author.lower(),
		time.strftime('%Y-%m-%d %X', time.localtime()),))
	conn.commit()

#	OK
def insert_rename_history(cursor, author_old, author_new, command):
	cursor.execute("INSERT INTO RENAMED_USERS_HISTORY VALUES(?,?,?,?)", (
		author_old.lower(),
		author_new.lower(),
		time.strftime('%Y-%m-%d %X', time.localtime()),
		command,))
	conn.commit()

### OK
def insert_like(cursor, Tweet, like_owner):
	cursor.execute("INSERT INTO LIKED_TWEETS VALUES(?,?,?,?,?)", (Tweet.author.screen_name, Tweet.id, like_owner.screen_name.lower(), Tweet.created_at, Tweet.text) )
	conn.commit()