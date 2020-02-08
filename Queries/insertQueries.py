import time
import logging
import Queries.Exceptions
import Queries.DBConnection as DB
import Queries.selectQueries as SQ

def user(user, last_id=None, last_lookup=None):

	if SQ.get_user(user):
		Queries.Exceptions.print_error("### ERROR ### -- User [ {} ] already exists!".format(user))
		return

	values = [user.lower()]
	values.append('Active' if last_lookup and last_id else 'Not Accessible')
	values.append(last_id if last_id else 0)
	values.append(last_lookup if last_lookup else time.strftime('%Y-%m-%d %X', time.localtime()))
	
	db = DB.database()
	db.query(statement="INSERT INTO TWITTER_USERS VALUES(?,?,?,?)", values=tuple(values), commit=True)
	db.close()
	
	Queries.Exceptions.print_info('Added user [ {} ] to the database'.format(user))

def download(tweet, command):
	values = [tweet.author.screen_name]
	values.append(int(tweet.id))
	values.append(tweet.created_at.strftime('%Y-%m-%d %X'))
	values.append(time.strftime('%Y-%m-%d %X', time.localtime()))
	values.append(command)
	values.append(tweet.full_text)

	db = DB.database()
	db.query(statement="INSERT INTO DOWNLOADED_TWEETS VALUES(?,?,?,?,?,?)", values=tuple(values), commit=True)
	db.close()

def error(tweet_author, status, error_code):

	db = DB.database()
	values = []

	if db.query("SELECT * FROM ERRORS_HISTORY WHERE lower(TWEET_AUTHOR) = ?", values=(tweet_author.lower(),) , fetchone=True) is None:

		values = [tweet_author.lower()]
		values.append(status)
		values.append(error_code)
		values.append(time.strftime('%Y-%m-%d %X', time.localtime()))
		db.query(statement="INSERT INTO ERRORS_HISTORY VALUES(?,?,?,?)", values=tuple(values), commit=True)

	else:

		values = [status]
		values.append(error_code)
		values.append(time.strftime('%Y-%m-%d %X', time.localtime()))
		values.append(tweet_author.lower())
		db.query(statement="UPDATE ERRORS_HISTORY SET STATUS = ?, ERROR_CODE = ?, DATE_ERROR = ? WHERE lower(TWEET_AUTHOR) = ?", values=tuple(values), commit=True)

	logging.critical("User [ {} ] is not accessible anymore: The account is now {}".format(tweet_author, status))

	db.close()

def like(Tweet, like_owner):
	values = [Tweet.author.screen_name]
	values.append(Tweet.id)
	values.append(like_owner.lower())
	values.append(Tweet.created_at)
	values.append(Tweet.text)

	db = DB.database()
	db.query(statement="INSERT INTO LIKED_TWEETS VALUES(?,?,?,?,?)", values=tuple(values), commit=True)
	db.close()
