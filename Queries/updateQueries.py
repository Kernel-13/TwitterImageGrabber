import os
import time
import shutil
import logging
import Exceptions
import Queries.DBConnection as DB
import Queries.selectQueries as SQ
from pathvalidate import sanitize_filename

### NEW - FUSION OF update_user(USER,TWEET_ID,TWEET_DATE) AND update_user_status(USER,STATUS)
def update_user(user, tweet_id=None, tweet_date=None, status=None):

	if SQ.get_user(user) is None:
		print("\t\t### ERROR ### -- We couldn't find [ {} ] in the user database!".format(user))
		return

	db = DB.database()

	if tweet_id is not None and tweet_date is not None:
		db.query(statement="UPDATE TWITTER_USERS SET TWEET_ID = ?, LAST_LOOKUP = ? WHERE lower(TWEET_AUTHOR) = ?", values=(tweet_id, tweet_date, user.lower()), commit=True)

	if status is not None:
		if status.lower().startswith('a'): 		status = 'Active'
		elif status.lower().startswith('n'):	status = 'Not Accessible'
		elif status.lower().startswith('p'):	status = 'Protected'
		elif status.lower().startswith('s'):	status = 'Suspended'
		elif status.lower().startswith('d'):	status = 'Deleted'
		else: 
			print("STATUS NOT RECOGNIZEd: {}".format(status))
			return

		db.query(statement="UPDATE TWITTER_USERS SET STATUS = ? WHERE lower(TWEET_AUTHOR) = ?", values=(status, user.lower()), commit=True)

	db.close()

def remove_like(tweet_id, like_owner): 
	db = DB.database()
	db.query(statement="DELETE FROM LIKED_TWEETS WHERE TWEET_ID = ? AND lower(LIKE_OWNER) = ?", values=(tweet_id, like_owner), commit=True)
	db.close()

### OK
def delete_user(user):
	if SQ.get_user(user) is None:
		print("\t\t### ERROR ### -- We couldn't find [ {} ] in the user database!".format(user))
		return

	db = DB.database()

	db.query(statement="DELETE FROM TWITTER_USERS WHERE lower(TWEET_AUTHOR) = ?", values=(user.lower(),), commit=True)
	print("\nDatabase updated!")

	try:
		values = [user.lower()]
		values.append(time.strftime('%Y-%m-%d %X', time.localtime()))
		db.query("INSERT INTO DELETED_USERS_HISTORY VALUES(?,?)", values=tuple(values), commit=True)

		shutil.rmtree(os.path.join(os.getcwd(), user))
		print("\nFolder deleted!")

	except Exception as err:
		print("Error:", err)
		#print("\t\t### ERROR ### -- We couldn't find [ {} ] in the user database!")
	
	db.close()

### OK
def rename_user(old_user_name, new_user_name, command):
	db = DB.database()

	if SQ.get_user(old_user_name) is None:	
		raise Exceptions.UnknownUser("We couldn't find any user with the name [ {} ] in the database!".format(old_user_name))
	
	if new_user_name != sanitize_filename(new_user_name): 
		raise Exceptions.InvalidName("User [ {} ] already exists in the database!".format(new_user_name))

	if SQ.get_user(new_user_name):
		raise Exceptions.UserExists("User [ {} ] already exists in the database!".format(new_user_name))
	
	if os.path.isdir(os.path.join(os.getcwd(), new_user_name)):
		raise Exceptions.FolderExists("A folder named [ {} ] already exists!".format(new_user_name))

	db.query("UPDATE TWITTER_USERS SET TWEET_AUTHOR = ? WHERE lower(TWEET_AUTHOR) = ?", values=(new_user_name, old_user_name.lower()))

	usr_folder = os.path.join(os.getcwd(), old_user_name)
	folder_iterable = os.walk(usr_folder)
	try:
		for _, _, files in folder_iterable:

			for file in files:

				try:
					if old_user_name.lower() in file.lower():
						file_to_rename = usr_folder + '\\' + file
						renamed_file = file.lower().replace(old_user_name.lower(), new_user_name)
						new_filename = usr_folder + '\\' + renamed_file
						os.rename(file_to_rename, new_filename)
				except OSError as e:
					print("\t\t### Error ### - Couldn't rename the following file:", file)
					print("\t\tERROR TYPE:", e)

			break

		values = [old_user_name.lower()]
		values.append(new_user_name.lower())
		values.append(time.strftime('%Y-%m-%d %X', time.localtime()))
		values.append(command)
		db.query(statement="INSERT INTO RENAMED_USERS_HISTORY VALUES(?,?,?,?)", values=tuple(values), commit=True)
		os.rename(usr_folder, os.path.join(os.getcwd(), new_user_name))

	except Exception as e:
		
		logging.error('Failed to rename folder or files')
		logging.exception("Rename Error")
		print("\t\t### Error ### - Couldn't rename the folder:", usr_folder)
		print("\t\tERROR TYPE:", e)

	db.close()

# NEW
def fuse_users(user_one, user_two):

	if SQ.get_user(user_one) is None or SQ.get_user(user_two) is None:
		print("\t\t### ERROR ### - One or both names provided are not present in the database!")
		return

	user_one_folder = os.path.join(os.getcwd(), user_one)
	user_two_folder = os.path.join(os.getcwd(), user_two)

	for _, _, files in os.walk(user_one_folder):
		for file in files:
			if user_one.lower() in file.lower():
				try:
					old_file = os.path.join(user_one_folder, file)
					new_file = os.path.join(user_two_folder, file.lower().replace(user_one.lower(), user_two))
					os.rename(old_file, new_file)
				except FileExistsError:
					print("File already exists:", new_file)

	try:
		shutil.rmtree(user_one_folder)
		cursor.execute("DELETE FROM TWITTER_USERS WHERE lower(TWEET_AUTHOR)=?", (user_one.lower(),))
		conn.commit()
	except Exception as err:
		print("Error:", err)

