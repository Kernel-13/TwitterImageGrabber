import Queries.DBConnection as DB

def get_user(user):
	db = DB.database()
	row = db.query("SELECT LOWER(TWEET_AUTHOR), STATUS, TWEET_ID, LAST_LOOKUP FROM TWITTER_USERS WHERE LOWER(TWEET_AUTHOR) = ?", values=(user.lower(),) , fetchone=True)
	db.close()

	return row


def get_ids_from_user(user):
	db = DB.database()
	rows = db.query("SELECT TWEET_ID FROM DOWNLOADED_TWEETS WHERE LOWER(TWEET_AUTHOR) = ? ORDER BY RANDOM()", values=(user.lower(),) , fetchall=True)
	db.close()

	return rows if len(rows) != 0 else None

def get_last_tweet_from_user(user):
	db = DB.database()
	row = db.query("SELECT TWEET_ID, DATE_DOWNLOADED FROM DOWNLOADED_TWEETS WHERE LOWER(TWEET_AUTHOR) = ? ORDER BY TWEET_ID DESC LIMIT 1", values=(user.lower(),) , fetchone=True)
	db.close()

	return row

def get_random_tweet(user):
	db = DB.database()
	row = db.query("SELECT * FROM DOWNLOADED_TWEETS WHERE LOWER(TWEET_AUTHOR) = ? ORDER BY RANDOM() LIMIT 1", values=(user.lower(),) , fetchone=True)
	db.close()

	return row

def get_user_list(status):

	if status.lower().startswith('a'): 		statement = "SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Active' ORDER BY lower(TWEET_AUTHOR)"
	elif status.lower().startswith('s'):   	statement = "SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Suspended' ORDER BY lower(TWEET_AUTHOR)"
	elif status.lower().startswith('p'):   	statement = "SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Active' ORDER BY lower(TWEET_AUTHOR)"
	elif status.lower().startswith('d'):   	statement = "SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Protected' ORDER BY lower(TWEET_AUTHOR)"
	elif status.lower().startswith('n'):   	statement = "SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Not Accessible' ORDER BY lower(TWEET_AUTHOR)"
	else: statement = "SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS != 'Active' ORDER BY lower(TWEET_AUTHOR)"

	db = DB.database()
	rows = db.query(statement, fetchall=True)
	db.close()

	return [row[0] for row in rows]

def already_downloaded(tweet_id):
	db = DB.database()
	row = db.query("SELECT * FROM DOWNLOADED_TWEETS WHERE TWEET_ID = ?", values=(tweet_id,), fetchone=True)
	db.close()

	return row != None