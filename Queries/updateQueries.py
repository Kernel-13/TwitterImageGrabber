import os
import shutil
import logging
import Queries.selectQueries as SQ

### NEW - FUSION OF update_user(USER,TWEET_ID,TWEET_DATE) AND update_user_status(USER,STATUS)
def update_user(user, tweet_id=None, tweet_date=None, status=None):
	
	if SQ.get_user(user):

		# UPDATES ONLY THE STATUS
		if status is not None:
			if status.lower().startswith('a'): 		status = 'Active'
			elif status.lower().startswith('n'):	status = 'Not Accessible'
			elif status.lower().startswith('p'):	status = 'Protected'
			elif status.lower().startswith('s'):	status = 'Suspended'
			elif status.lower().startswith('d'):	status = 'Deleted'
			else: 
				print("STATUS NOT RECOGNIZEd: {}".format(status))
				return

			__cursor.execute("UPDATE TWITTER_USERS SET STATUS = ? WHERE lower(TWEET_AUTHOR) = ?",(status, user.lower(),))

		# UPDATES BOTH LAST TWEET_ID AND LAST_LOOKUP
		elif tweet_id is not None and tweet_date is not None:

			__cursor.execute("UPDATE TWITTER_USERS SET TWEET_ID = ?, LAST_LOOKUP = ? WHERE lower(TWEET_AUTHOR) = ?",(tweet_id, tweet_date, user.lower(),))

		conn.commit()

	else:
		print("\t\t### ERROR ### -- We couldn't find [ {} ] in the user database!".format(user))

def remove_like(tweet_id, like_owner):
	cursor.execute("DELETE FROM LIKED_TWEETS WHERE TWEET_ID=? AND lower(LIKE_OWNER)=?", (tweet_id, like_owner) )
	conn.commit()

### OK
def delete_user(user):
	if SQ.get_user(user):
		cursor.execute("DELETE FROM TWITTER_USERS WHERE lower(TWEET_AUTHOR)=?", (user.lower(),))
		conn.commit()

		print("\nDatabase updated!")
		try:
			insert_deleted_history(user.lower()) # WARNING
			shutil.rmtree(os.path.join(os.getcwd(), user))
			print("\nFolder deleted!")
		except Exception as err:
			print("Error:", err)
			#print("\t\t### ERROR ### -- We couldn't find [ {} ] in the user database!")

### OK
def rename_user(old_user_name, new_user_name, command):

	# Checks if the old user exists in the database
	if SQ.get_user(old_user_name) is None:
		print("\t\t### ERROR ### -- We couldn't find any user with the name [{}] in the database!".format(old_user_name))
		raise Exceptions.Renaming_UnknownUser
	
	# Checks if the new user name is a valid one
	if new_user_name != sanitize_filename(new_user_name):
		print("\t\t### ERROR ### - User [{}] already exists in the database!".format(new_user_name))
		raise Exceptions.Renaming_InvalidName

	# Checks if the new user is already in the database
	if SQ.get_user(new_user_name):
		print("\t\t### ERROR ### - User [{}] already exists in the database!".format(new_user_name))
		raise Exceptions.Renaming_UserExists

	# Checks if there is a folder named after the new user
	if os.path.isdir(os.path.join(os.getcwd(), new_user_name)):
		print("Folder with name of new user already exists!")
		raise Exceptions.Renaming_FolderExists

	try:
		__cursor.execute("UPDATE TWITTER_USERS SET TWEET_AUTHOR=? WHERE lower(TWEET_AUTHOR)=?",(new_user_name, old_user_name.lower(),))
		conn.commit()
	except SQlite3.IntegrityError as e:
		print("\t\t### Error ### - Couldn't rename user [{}] to [{}]", format(old_user_name, new_user_name))
		print("\t\tERROR TYPE:", e)
		return

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
				except OSError as e: # FOR EXAMPLE, THE FILE ALREADY EXISTS
					print("\t\t### Error ### - Couldn't rename the following file:", file)
					print("\t\tERROR TYPE:", e)

			break

		try:
			insert_rename_history(old_user_name, new_user_name, command)
		except SQlite3.IntegrityError as e:
			pass

		try:
			os.rename(usr_folder, os.getcwd() + '\\' + new_user_name)
		except OSError as e: # FOR EXAMPLE, THE FOLDER ALREADY EXISTS
			pass

	except Exception as e:
		
		logging.error('Failed to rename folder or files')
		logging.exception("Rename Error")
		print("\t\t### Error ### - Couldn't rename the folder:", usr_folder)
		print("\t\tERROR TYPE:", e)

# NEW
def fuse_users(user_one, user_two):
	if SQ.get_user(user_one) and SQ.get_user(user_two):

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

	else:
		print("\t\t### ERROR ### - One or both names provided are not present in the database!")
