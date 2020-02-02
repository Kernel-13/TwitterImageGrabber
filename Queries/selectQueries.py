### OK
def get_user(cursor, user):
	cursor.execute("SELECT * FROM TWITTER_USERS WHERE lower(tweet_author) = ?", (user.lower(),))
	row = cursor.fetchall()
	return row if len(row) != 0 else None

### OK
def get_user_list(cursor, status):

	if status.lower().startswith('a'): 		cursor.execute("SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Active' ORDER BY lower(TWEET_AUTHOR)")
	elif status.lower().startswith('s'):   	cursor.execute("SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Suspended' ORDER BY lower(TWEET_AUTHOR)")
	elif status.lower().startswith('p'):   	cursor.execute("SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Active' ORDER BY lower(TWEET_AUTHOR)")
	elif status.lower().startswith('d'):   	cursor.execute("SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Protected' ORDER BY lower(TWEET_AUTHOR)")
	elif status.lower().startswith('n'):   	cursor.execute("SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS = 'Not Accessible' ORDER BY lower(TWEET_AUTHOR)")
	else: cursor.execute("SELECT LOWER(TWEET_AUTHOR) FROM TWITTER_USERS WHERE STATUS != 'Active' ORDER BY lower(TWEET_AUTHOR)")

	return [row[0].lower() for row in cursor.fetchall()]

# DONE
def like_exists(cursor, like_owner, tweet_id):
	cursor.execute("SELECT * FROM LIKED_TWEETS WHERE TWEET_ID = ? AND lower(LIKE_OWNER) = ?", (tweet_id, like_owner.lower(),) )
	return len(cursor.fetchall()) != 0

# DONE ?
def get_likes(cursor, like_owner):
	cursor.execute("SELECT TWEET_ID, TWEET_OWNER, LIKE_OWNER, DATE_POSTED FROM LIKED_TWEETS WHERE lower(LIKE_OWNER) = ? ORDER BY TWEET_ID DESC", (like_owner.screen_name.lower(),) )
	return [str(row[0]) for rows in cursor.fetchall()]

# DONE
def already_downloaded(cursor, tweet_id):
	cursor.execute("SELECT * FROM DOWNLOADED_TWEETS WHERE TWEET_ID = ?", (tweet_id,))
	row = cursor.fetchall()
	return row if len(row) != 0 else None
	# Change to return len(cursor.fetchall()) != 0