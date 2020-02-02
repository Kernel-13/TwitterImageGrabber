import Queries.DBConnection as DB

def get_user(user):
	db = DB.database()
	row = db.query("SELECT * FROM TWITTER_USERS WHERE TWEET_AUTHOR = ?", values=(user.lower(),) , fetchall=True)
	db.close()

	return row if len(row) != 0 else None

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