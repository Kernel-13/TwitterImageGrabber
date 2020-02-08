import os
import time
import shutil
import logging
import Queries.Exceptions
import Queries.DBConnection as DB
import Queries.selectQueries as SQ
from pathvalidate import sanitize_filename

def update_user(user, status=None):

	db_user = SQ.get_user(user)

	if db_user is None:
		raise Queries.Exceptions.UnknownUser("We couldn't find any user with the name [ {} ] in the database!".format(user))

	db = DB.database()

	if status:
		if status.lower().startswith('a'): 		status = 'Active'
		elif status.lower().startswith('n'):	status = 'Not Accessible'
		elif status.lower().startswith('p'):	status = 'Protected'
		elif status.lower().startswith('s'):	status = 'Suspended'
		elif status.lower().startswith('d'):	status = 'Deleted'
		else:
			raise Queries.Exceptions.UnknownStatus("Status not recognized: {}".format(status))

		if db_user[1] != status:
			db.query(statement="UPDATE TWITTER_USERS SET STATUS = ? WHERE lower(TWEET_AUTHOR) = ?", values=(status, user.lower()), commit=True)
			Queries.Exceptions.print_info("=====> Changed status of [ {} ] to '{}'\n".format(user, status))

	try:
		tweet_id, tweet_date = SQ.get_last_tweet_from_user(user)
		db.query(statement="UPDATE TWITTER_USERS SET TWEET_ID = ?, LAST_LOOKUP = ? WHERE lower(TWEET_AUTHOR) = ?", values=(tweet_id, tweet_date, user.lower()), commit=True)
	except TypeError as err:
		logging.warning("Could not find any tweets whose author is the user [ {} ] in the DOWNLOADED_TWEETS table")
	
	db.close()

def remove_like(tweet_id, like_owner): 
	db = DB.database()
	db.query(statement="DELETE FROM LIKED_TWEETS WHERE TWEET_ID = ? AND lower(LIKE_OWNER) = ?", values=(tweet_id, like_owner.lower()), commit=True)
	db.close()

def delete_user(user):
	if SQ.get_user(user) is None:
		raise Queries.Exceptions.UnknownUser("We couldn't find any user with the name [ {} ] in the database!".format(user))

	values = [user.lower()]
	values.append(time.strftime('%Y-%m-%d %X', time.localtime()))
	
	db = DB.database()
	db.query("DELETE FROM TWITTER_USERS WHERE lower(TWEET_AUTHOR) = ?", values=(user.lower(),), commit=True)
	db.query("INSERT INTO DELETED_USERS_HISTORY VALUES(?,?)", values=tuple(values), commit=True)
	db.close()
	
	shutil.rmtree(os.path.join(os.getcwd(), user), ignore_errors=True)

	Queries.Exceptions.print_info("Database updated! User [ {} ] has been deleted!".format(user))
	Queries.Exceptions.print_info("Folder deleted!")
	
def rename_user(old_user_name, new_user_name, command):
	db = DB.database()

	if SQ.get_user(old_user_name) is None:	
		raise Queries.Exceptions.UnknownUser("We couldn't find any user with the name [ {} ] in the database!".format(old_user_name))
	
	if new_user_name != sanitize_filename(new_user_name): 
		raise Queries.Exceptions.InvalidName("User [ {} ] already exists in the database!".format(new_user_name))

	if SQ.get_user(new_user_name):
		raise Queries.Exceptions.UserExists("User [ {} ] already exists in the database!".format(new_user_name))
	
	if os.path.isdir(os.path.join(os.getcwd(), new_user_name)):
		raise Queries.Exceptions.FolderExists("A folder named [ {} ] already exists!".format(new_user_name))

	db.query("UPDATE TWITTER_USERS SET TWEET_AUTHOR = ? WHERE lower(TWEET_AUTHOR) = ?", values=(new_user_name, old_user_name.lower()))


	folder_to_rename = os.path.join(os.getcwd(), old_user_name)

	for _, _, files in os.walk(folder_to_rename):

		for file in files:

			try:

				if old_user_name.lower() in file.lower():

					old_file = os.path.join(folder_to_rename, file)
					renamed_file = file.lower().replace(old_user_name.lower(), new_user_name)
					new_file = os.path.join(folder_to_rename, renamed_file)
					os.rename(old_file, new_file)

			except FileExistsError:

				renamed_file = "[Duplicate] " + file.lower().replace(old_user_name.lower(), new_user_name)
				new_file = os.path.join(folder_to_rename, renamed_file)
				os.rename(old_file, new_file)

		break
	
	os.rename(folder_to_rename, os.path.join(os.getcwd(), new_user_name))
	Queries.Exceptions.print_info("====> User [ {} ] changed its name to [ {} ]".format(old_user_name, new_user_name))

	values = [old_user_name.lower()]
	values.append(new_user_name.lower())
	values.append(time.strftime('%Y-%m-%d %X', time.localtime()))
	values.append(command)
	db.query(statement="INSERT INTO RENAMED_USERS_HISTORY VALUES(?,?,?,?)", values=tuple(values), commit=True)
	db.close()

def fuse_users(user_one, user_two):

	if SQ.get_user(user_one) is None or SQ.get_user(user_two) is None:
		raise Queries.Exceptions.UnknownUser("Both or one of the users provided are not present in the database!".format(user))

	user_one_folder = os.path.join(os.getcwd(), user_one)
	user_two_folder = os.path.join(os.getcwd(), user_two)

	for _, _, files in os.walk(user_one_folder):

		for file in files:

			if user_one.lower() in file.lower():

				old_file = os.path.join(user_one_folder, file)
				
				try:
					new_file = os.path.join(user_two_folder, file.lower().replace(user_one.lower(), user_two))
					os.rename(old_file, new_file)

				except FileExistsError:
					new_file = "[Duplicate] " + file.lower().replace(user_one.lower(), user_two)
					os.rename(old_file, new_file)

				Queries.Exceptions.print_info("Changed name of file {} to {}".format(old_file, new_file))

	shutil.rmtree(user_one_folder)
	Queries.Exceptions.print_info("Deleted folder [ {} ]".format(user_one_folder))

	db = DB.database()
	db.query("DELETE FROM TWITTER_USERS WHERE lower(TWEET_AUTHOR) = ?", values=(user_one.lower(),) , commit=True)
	db.close()
