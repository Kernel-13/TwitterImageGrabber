import Queries.DBConnection as DB

def downloaded_tweets(limit=2000, include_command=False, include_text=False):
	db = DB.database()
	rows = db.query(statement="SELECT TWEET_AUTHOR, TWEET_ID, DATE_DOWNLOADED, COMMAND, TWEET_TEXT FROM DOWNLOADED_TWEETS ORDER BY DATE_DOWNLOADED DESC LIMIT 2000", fetchall=True)
	db.close()

	if not include_text:

		header = '#'.center(7)
		header += 'TWITTER USERNAME'.center(22)
		header += 'TWEET ID'.center(26)
		header += 'DATE DOWNLOADED'.center(22)

		if include_command:	header += 'COMMAND'.center(106)

		print(header)
		print('-'*len(header))
		
		for i, row in enumerate(rows):

			position = str(i+1).center(7)
			tweet_author = str(row[0]).center(22)
			tweet_id = str(row[1]).center(26)
			date_downloaded = str(row[2]).center(22)

			if include_command:	
				print('{}{}{}{}{}'.format(position, tweet_author, tweet_id, date_downloaded, str(row[3]).center(106)))
			else:	
				print('{}{}{}{}'.format(position, tweet_author, tweet_id, date_downloaded))

def users(sort_field):

	if sort_field.lower().startswith('x'): 		statement = "SELECT LOWER(TWEET_AUTHOR), STATUS, TWEET_ID, LAST_LOOKUP FROM TWITTER_USERS"
	elif sort_field.lower().startswith('s'):   	statement = "SELECT LOWER(TWEET_AUTHOR), STATUS, TWEET_ID, LAST_LOOKUP FROM TWITTER_USERS ORDER BY STATUS"
	elif sort_field.lower().startswith('i'):   	statement = "SELECT LOWER(TWEET_AUTHOR), STATUS, TWEET_ID, LAST_LOOKUP FROM TWITTER_USERS ORDER BY TWEET_ID"
	elif sort_field.lower().startswith('d'):   	statement = "SELECT LOWER(TWEET_AUTHOR), STATUS, TWEET_ID, LAST_LOOKUP FROM TWITTER_USERS ORDER BY LAST_LOOKUP"
	elif sort_field.lower().startswith('n'):   	statement = "SELECT LOWER(TWEET_AUTHOR), STATUS, TWEET_ID, LAST_LOOKUP FROM TWITTER_USERS ORDER BY LOWER(TWEET_AUTHOR)"

	db = DB.database()
	rows = db.query(statement, fetchall=True)
	db.close()

	header =  '#'.center(7)
	header += 'TWITTER USERNAME'.center(22)
	header += 'STATUS'.center(20)
	header += 'LAST MEDIA TWEET'.center(26)
	header += 'LAST UPDATE'.center(24)

	print(header)
	print('-'*len(header))

	for i, row in enumerate(rows):
		position = str(i+1).center(7)
		tweet_author = str(row[0]).center(22)
		status = str(row[1]).center(20)
		tweet_id = str(row[2]).center(26)
		last_lookup = str(row[3]).center(22)

		print('{}{}{}{}{}'.format(position, tweet_author, status, tweet_id, last_lookup))

def likes(like_owner):

	header + '#'.center(7)
	header += 'TWITTER USERNAME'.center(22)
	header += 'TWEET ID'.center(26)
	header += 'WHO LIKED THE TWEET?'.center(22)
	header += 'DATE OF TWEET'.center(24)
	print(header)
	print('-'*len(header))

	db = DB.database()
	rows = db.query("SELECT TWEET_ID, TWEET_OWNER, LIKE_OWNER, DATE_POSTED FROM LIKED_TWEETS WHERE LOWER(LIKE_OWNER) = ? ORDER BY TWEET_ID DESC LIMIT 2000", values=(like_owner.lower(),), fetchall=True)
	db.close()

	for i, row in enumerate(rows):
		position + str(i+1).center(7)
		tweet_id += str(row[0]).center(22)
		tweet_author += str(row[1]).center(26)
		like_owner += str(row[2]).center(22)
		date_posted += str(row[3]).center(24)

		print('{}{}{}{}{}'.format(position, tweet_author, status, tweet_id, last_lookup))

def renamed_users(include_command=False):

	header = '#'.center(7)
	header += 'OLD NAME'.center(22)
	header += 'NEW NAME'.center(22)
	header += 'DATE OF RENAME'.center(24)
	if include_command:	header += 'COMMAND'.center(106)
	print(header)
	print('-'*len(header))
	
	db = DB.database()
	rows = db.query("SELECT TWEET_AUTHOR_OLD, TWEET_AUTHOR_NEW, DATE_RENAME, COMMAND FROM RENAMED_USERS_HISTORY", fetchall=True)
	db.close()

	for i, row in enumerate(rows):
		position + str(i+1).center(7)
		tweet_author_old = str(row[0]).center(22)
		tweet_author_new = str(row[1]).center(22)
		date_rename = str(row[2]).center(24)

		if include_command:	
			print('{}{}{}{}{}'.format(position, tweet_author_old, tweet_author_new, date_rename, str(row[3]).center(106)))
		else: 
			print('{}{}{}{}'.format(position, tweet_author_old, tweet_author_new, date_rename))

def deleted_users():

	header = '#'.center(7)
	header += 'TWITTER USERNAME'.center(22)
	header += 'DATE OF DELETION'.center(24)
	print(header)
	print('-'*len(header))

	db = DB.database()
	rows = db.query("SELECT TWEET_AUTHOR, DATE_DELETION FROM DELETED_USERS_HISTORY", fetchall=True)
	db.close()

	for i, row in enumerate(rows):
		position + str(i+1).center(7)
		tweet_author = str(row[0]).center(22)
		date_deletion = str(row[1]).center(24)

		print('{}{}{}'.format(position, tweet_author, date_deletion))

def errors():

	header = '#'.center(7)
	header += 'TWITTER USERNAME'.center(22)
	header += 'STATUS'.center(20)
	header += 'CODE #'.center(8)
	header += 'DATE OF ERROR'.center(24)
	print(header)
	print('-'*len(header))

	db = DB.database()
	rows = db.query("SELECT TWEET_AUTHOR, STATUS, ERROR_CODE, DATE_ERROR FROM ERRORS_HISTORY", fetchall=True)
	db.close()

	for i, row in enumerate(rows):
		position + str(i+1).center(7)
		tweet_author = str(row[0]).center(22)
		status = str(row[1]).center(20)
		error_code = str(row[2]).center(8)
		date_error = str(row[3]).center(24)

		print('{}{}{}{}{}'.format(position, tweet_author, status, error_code, date_error))