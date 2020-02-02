#  -*- coding: utf-8 -*-
'''
Created on 2 Apr 2018

@author: Kernel-13
'''

import requests
import sys
import os
import tweepy
import time
import json
import winsound
import sqlite3
import logging
import argparse

import Queries.insertQueries as IQ
import Queries.selectQueries as SQ
import Queries.updateQueries as UQ
import Queries.printQueries as PQ

auth = None
api = None
authenticated_user = None
Options = None

db_new_user = ''
db_new_last_id = '0'
db_new_lookup = ''
error_code = 0

dups_count = 0
file_count = 0
fetched_tweets = 0
start_time = time.time()        #Change to time.localtime()
error_at_checking_user = False

class finished_folder_update(Exception):
	pass

class uncommon_twitter_exception(Exception):
	pass

### FUNCTIONS THAT WORK WITH ID QUEUES ### [Merge All]

def id_queue(action):
	
	if action == "like": 		queue = Options.like
	elif action == "dislike": 	queue = Options.dislike
	elif action == "retweet": 	queue = Options.retweet
	elif action == "unretweet": queue = Options.unretweet

	logging.info("\tQueue: {}\n".format(' '.join(queue)))
	logging.info("\tQueue Size: {}\n".format(len(queue)))
	error_list = []

	for tweet_id in queue:
		try:

			if action == "retweet":		api.retweet(tweet_id)
			elif action == "unretweet":	api.unretweet(tweet_id)
			elif action == "like": 		
				api.create_favorite(tweet_id)
				tweet = api.get_status(tweet_id)
				IQ.like(tweet, authenticated_user)
			elif action == "dislike":	
				api.destroy_favorite(tweet_id)
				db_operations.remove_like(tweet_id, authenticated_user)

			print("\tID: {} - Operation: {} - Status: Success".format(tweet_id, action.upper()))

		except tweepy.error.TweepError as err:

			if err.response.status_code == 429:
				error_message = 'The request limit for this resource has been reached.'
			else:
				error_message = err.response.json()['errors'][0]['message']

			print ("\tError with ID: {} ---> {} (Operation: {})".format(tweet_id, error_message, action.upper()))
			error_list.append((tweet_id, error_message))

		except sqlite3.IntegrityError as err:
			logging.info("\tIntegrityError")
			print(err)

		time.sleep(Options.time[0]) 

	if error_list:
		print("\n\tErrors occurred while processing some ({}) tweets. Check the log file for more information".format(len(error_list)))
		logging.info("\t### Errors ###")
		for err in error_list:
			logging.info("\t\tError with ID: {} ---> {}".format(err[0], err[1]))
		logging.info("\tNº of failed {}s: {}\n".format(action, len(error_list)))

### FUNCTIONS THAT ITERATE OVER THE USERS IN THE DATABASE ###

def update_all():
	update_db = True
	global db_new_last_id
	global db_new_lookup

	user_list = SQ.get_user_list('Active')

	# To resume update after the program crashes unexpectedly 
	try: 
		start_idx = user_list.index(Options.start_at[0].lower()) if Options.start_at is not None else 0

	except ValueError as err: 
		user = SQ.get_user(Options.start_at[0])
		if user is None:
			print("\tERROR: User '{}' is not in the database!".format(Options.start_at[0]))
		else:
			print("\tERROR: User '{}' is marked as '{}'.".format(user[0][0], user[0][1]))
			print("\tTry using the '--check_again' option to check if its accessible again.")
			print("\tYou can also use '--update_status' to manually change its status.")
		os._exit(1)

	# Self-explanatory
	if Options.skip is not None:
		for user in Options.skip:
			if user.lower() in user_list:  user_list.remove(user)

	# 
	for user in user_list[start_idx::]:

		try:
			if user != '':
				update_db = True
				print(f'\t--- Updating User: {user}\n')
				fetch_tweets(user)

		except finished_folder_update:
			pass

		except (requests.exceptions.RequestException,TimeoutError,tweepy.error.TweepError,requests.exceptions.ConnectionError) as e:
			update_db = False
			logging.exception("TypeError")
			print(e)

		except uncommon_twitter_exception:
			update_db = False

		except:
			raise

		if update_db and db_new_last_id != '0' and db_new_lookup != '':
			db_operations.update_user(user, db_new_last_id, db_new_lookup)
			db_new_last_id = '0'
			db_new_lookup = ''
		print()
	return

def retry_non_active():
	global error_code

	if Options.check_again[0].lower().startswith('p'):     user_list = SQ.get_user_list('Protected')
	elif Options.check_again[0].lower().startswith('s'):   user_list = SQ.get_user_list('Suspended')
	elif Options.check_again[0].lower().startswith('d'):   user_list = SQ.get_user_list('Deleted')
	elif Options.check_again[0].lower().startswith('n'):   user_list = SQ.get_user_list('Not Accessible')
	else:   user_list = SQ.get_user_list('x')

	update_db = True

	for user in user_list:

		try:
			if user != '':
				print(f'    --- Checking {user}\n')
				logging.info(f"      Checking {user}")
				fetch_tweets(str(user))

		except finished_folder_update:
			pass

		except (requests.exceptions.RequestException,TimeoutError,tweepy.error.TweepError,requests.exceptions.ConnectionError) as e:
			update_db = False
			logging.exception("TypeError")

		except uncommon_twitter_exception:
			update_db = False

		except:
			logging.exception("I have no idea dude")
			raise

		try:
			if error_code == 34:

				error_code = 0
				IQ.error(str(user), 'Not Accessible', '34')
				print(f'\n       --- Checking for new name of {user}')
				logging.info(f"          Checking for new name of {user}")

				last_known_id = SQ.get_user(str(user))[0][2]
				last_known_tweet = lookup_tweet(last_known_id)
				db_operations.rename_user(str(user), last_known_tweet.author.screen_name, ' '.join(sys.argv)[:97]+'...', Options.forced)
				fetch_tweets(str(last_known_tweet.author.screen_name))

				print(f'         ====> User [ {user} ] changed its name to [ {last_known_tweet.author.screen_name} ]')
				user = last_known_tweet.author.screen_name
				update_db = True

		except tweepy.error.TweepError:
				error_code = 0
				print('         ERROR: User might have a private account, or it may have been deleted')
				logging.exception("              User is private or the account has been deleted")


		global db_new_last_id
		global db_new_lookup
		username = user.lower()

		if update_db:
			db_operations.update_user_status(user,'Active')
			print('     =====> Changed status to Active')
			if db_new_last_id != '0' and db_new_lookup != '':
				db_operations.update_user(user,db_new_last_id,db_new_lookup)
			db_new_last_id = '0'
			db_new_lookup = ''

		print()
		update_db = True
	return

### OK
def follow_users():
	fail_count = 0
	for user in Options.follow:
		try:
			api.create_friendship(user)
		except tweepy.error.TweepError as err:
			fail_count += 1
			print ("Error with User: {} ---> {}".format(user, err.response.json()['errors'][0]['message']))
			logging.info("  Error with User: {} ---> {}".format(user, err.response.json()['errors'][0]['message']))
		#time.sleep(random.choice(range(Options.time[0]-60,Options.time[0]+60))) 

### OK
def search_tweets():
	save_folder = 'Searched Tweets' + '\\' + ''.join([ch if ch not in '\\/:"*?<>|' else '_' for ch in Options.search[0].strip()])
	os.makedirs(save_folder, exist_ok=True) 
	try:
		for twt in tweepy.Cursor(api.search, q=' '.join(Options.search), count=100, include_entities=True, tweet_mode='extended').items(): 
			print(twt.id)
			process_tweet(twt, save_folder, [0])  
	except Exception as e:
		print(e)


def lookup_tweet(id_str=None):
	if id_str is not None:  
		return api.get_status(id_str)
	else:
		for _id_ in Options.lookup_id:
			try:
				print(api.get_status(_id_))
			except tweepy.error.TweepError as err:
				print ("\tError with ID: {} ---> {}".format(_id_, err.response.json()['errors'][0]['message']))
			time.sleep(Options.time[0])


def single_tweet():
	os.makedirs('_tmp', exist_ok=True)
	fail_count = 0
	for tweet in Options.single:
		try:
			twt = api.get_status(tweet, tweet_mode='extended')
			#print(json.dumps(twt._json, sort_keys=True, indent=4))
			process_tweet(twt, '_tmp',[0])

		except tweepy.error.TweepError as err:
			fail_count += 1
			print ("Error with ID: {} ---> {}".format(tweet, err.response.json()['errors'][0]['message']))
			logging.info("  Error with ID: {} ---> {}".format(tweet, err.response.json()['errors'][0]['message']))

	logging.info('\t\tDownloaded media from single tweet(s) -- exiting script')

def my_timeline(last_id=None):
	max_id = last_id
	if Options.start_at is not None and last_id is None and Options.start_at[0].isdigit(): max_id = Options.start_at[0]
	return f"{authenticated_user.screen_name}'s Timeline", api.home_timeline(count=200,exclude_replies=Options.no_replies,max_id=max_id)

def user_timeline(username='', last_id=None):
	global error_code
	max_id = last_id

	try:
		tweets = api.user_timeline(screen_name=username,
			count=200,
			exclude_replies=Options.no_replies,
			include_rts=Options.no_retweets,
			max_id=max_id)
		## print(username, '--->' ,api.get_user(username)._json['id'])

	except requests.exceptions.RequestException as e:
		print ('    ###    Connection Error    ###')
		print ('    There is no internet connection')
		logging.info(" ####### Connection Error ####### ")
		logging.exception("Connection_Error")
		return
	except tweepy.TweepError as e:
		print ('    ###    Error    ###')
		logging.info(" ####### Twitter Error ####### ")
		try:
			print ('    Error Code: ' + str(e.args[0][0]['code']))
			print ('    Error Message: ' + e.args[0][0]['message'])
			logging.info(f" ### Twitter Error Code -- {str(e.args[0][0]['code'])}")
			logging.info(f" ### User: {username}")
			logging.info(f" ### Twitter Error Message -- {e.args[0][0]['message']}")
			if Options.check_again is not None: 
				error_code = int(e.args[0][0]['code'])
				raise uncommon_twitter_exception
		except TypeError:
			print (f'    Error Message: {e.args[0]}')
			logging.info(f" ### User: {username}")
			logging.info(f" ### Error Message -- {e.args[0]}")
		print ('    For more info about this error, check https://developer.twitter.com/en/docs/basics/response-codes')

		if SQ.get_user(username) is not None: 
			db_operations.update_user_status(username,'Not Accessible')
			try:
				IQ.error(username, 'Not Accessible', str(e.args[0][0]['code']))
			except:
				IQ.error(username, 'Not Accessible', 'Unknown')
		if Options.update_all or Options.check_again is not None:   raise uncommon_twitter_exception

		os._exit(1)
	
	return username,tweets

def fetch_tweets(username=''):
	global api, dups_count, fetched_tweets
	tweets = []
	
	if Options.my_timeline: save_folder,tweets = my_timeline()
	else: 
		if Options.start_at is not None and Options.start_at[0].isdigit():  save_folder,tweets = user_timeline(username,Options.start_at[0])
		else: save_folder,tweets = user_timeline(username)

	try:
		oldest = tweets[-1].id - 1     
		os.makedirs(save_folder, exist_ok=True)
	except IndexError:
		logging.info(f"     ::::::: ERROR (IndexError) while Updating {username}:")
		#logging.info(f"         ERROR (IndexError) while Updating {username}")
		return
			
	logging.info(f"      Updating {username}")
	local_tweet_count = 0

	# Really awful way to do it but just bear with me
	local_dups_count = []
	local_dups_count.append(0)

	while len(tweets) > 0:
		for twt in tweets:
			fetched_tweets += 1
			local_tweet_count += 1
			process_tweet(twt, save_folder,local_dups_count)
			if Options.max_fetch is not None and local_tweet_count >= int(Options.max_fetch[0]):
				logging.info(f'              Reached {local_tweet_count} fetched tweets (max. set to {Options.max_fetch[0]})')
				print(f'              Reached {local_tweet_count} fetched tweets (max. set to {Options.max_fetch[0]})')
				if Options.update_all:   raise finished_folder_update
				else:   return

			if (Options.no_dups and local_dups_count[0] > 0) or (Options.max_dups is not None and local_dups_count[0] >= int(Options.max_dups[0])):
				logging.info(f'              Found {local_dups_count[0]} duplicate files')
				print(f'              Found {local_dups_count[0]} duplicate files')
				if Options.update_all: raise finished_folder_update
				else: return

		if Options.my_timeline: _,tweets = my_timeline(oldest)
		else: _,tweets = user_timeline(username,oldest)
		if len(tweets) > 0: oldest = tweets[-1].id - 1

def process_tweet(twt, save_folder,local_dups_count):
	global db_new_user,db_new_last_id,dups_count

	try:
		file_path = ''
		date = twt.created_at.strftime('%Y-%m-%d %X')
		if hasattr(twt, "retweeted_status"):
			twt = twt.retweeted_status
			date = twt.created_at.strftime('%Y-%m-%d %X')
		
		if hasattr(twt, "extended_entities"):
			if Options.check_table and db_operations.already_downloaded(twt.id):
				if Options.dup_info: print(f'          # Already in table: {twt.author.screen_name} {twt.id_str}')
				logging.info(f'          Already downloaded: {twt.author.screen_name} {twt.id_str}')
				local_dups_count[0] += 1
				dups_count += 1
				return

			if twt.extended_entities['media']:
				db_new_user = twt.author.screen_name
				if int(twt.id_str) > int(db_new_last_id):
					db_new_last_id = twt.id_str

				media_count = 1
				for media in twt.extended_entities['media']:
					if 'video_info' in media and not Options.no_video:
						bitrate = 0
						url = ''
						videos = media["video_info"]["variants"]
						for i in videos:
							if i["content_type"] == "video/mp4" and i["bitrate"] >= bitrate:
								bitrate = i["bitrate"]
								url = i["url"]
						file_extension = url.rsplit('.', 1)[1]
					elif 'video_info' not in media and not Options.no_image:
						url = media['media_url']
						file_extension = url.rsplit('.', 1)[1]
						url = url + ':orig'
					else:
						break


					try:
						content = requests.get(url, stream=True, timeout=1) 
					except:
						logging.info(" ### ERROR - 'Connection Aborted' due to timeout")
						logging.info(f" ### Tweet Author: {twt.author.screen_name}")
						logging.info(f" ### Tweet ID: {twt.id_str}")
						logging.info(f" ### File Format: {file_extension}")
						logging.info(f" ### Media URL: {url}")
						return


					if '?' in file_extension:	# Special case
						file_extension = file_extension.split('?')[0]

					file_name = f"{twt.author.screen_name} {twt.id_str} [{media_count}].{file_extension}"

					if Options.save_to_user_folder:
						if SQ.get_user(twt.author.screen_name) is not None:   file_path = os.getcwd() + '\\' + twt.author.screen_name + '\\' + file_name
						elif Options.only_db:   break
						else:   file_path = save_folder + '\\' + file_name
					else:
						file_path = save_folder + '\\' + file_name

					if Options.into is not None:
						if os.path.isdir(Options.into[0]):
							if Options.split:
								db_path = Options.into[0] + '\\' + 'IN_DB'
								not_db_path = Options.into[0] + '\\' + 'NOT_IN_DB'
								os.makedirs(db_path, exist_ok=True)
								os.makedirs(not_db_path, exist_ok=True)
								if SQ.get_user(twt.author.screen_name) is not None:   file_path = db_path + '\\'+ file_name
								else:   file_path = not_db_path + '\\' + file_name
							else:
								file_path = Options.into[0] + '\\' + file_name

					save_file(file_path, content, date, Options, local_dups_count)
					media_count += 1  

				if db_operations.already_downloaded(twt.id):
					if len(' '.join(sys.argv)) > 100:   
						IQ.download(twt, ' '.join(sys.argv)[:97]+'...')
					else: 
						IQ.download(twt, ' '.join(sys.argv))
					logging.info(f'          ---> Added to the table: {twt.id_str}')
		else:
			print(twt._json['id'], "has no extended_entities => Can't be downloaded")
	except AttributeError:
		print(f'ERROR ---- Twitter User: {twt.author.screen_name} ----- Tweet ID: {twt.id_str}')
	return

def save_file(file_path, data, date, Options, local_dups_count):

	global dups_count,file_count
	filename = file_path.rsplit('\\', 1)[1]

	if not os.path.exists(file_path) or os.path.getsize(file_path) != len(data.content):

		prefix = 'Updating:' if os.path.exists(file_path) else 'Saving:'

		print(f'        {prefix} {filename}')
		logging.info(f'          {prefix} {filename}')
		
		try:
			with open(file_path, 'wb') as f: f.write(data.content)
			stinfo = os.stat(file_path)
			os.utime(file_path,(stinfo.st_mtime, time.mktime(time.strptime(date, '%Y-%m-%d %X'))))
			file_count += 1

		except requests.exceptions.ConnectionError as e:
			logging.exception("UNUSUAL:FAILED AT SAVE_FILE()")
			logging.info(f'          Failed to retrieve content from {filename}')
			with open(file_path + " [Corrupted]", 'wb') as f: f.write('1'.encode())

		if Options.store_in_tmp:
			db_path = 'D:' + '\\' + 'TEMP' + '\\' + 'IN_DB'
			not_db_path = 'D:' + '\\' + 'TEMP' + '\\' + 'NOT_IN_DB'
			if SQ.get_user(filename.split(' ')[0]) is not None:   file_path = db_path + '\\'+ filename
			else:   file_path = not_db_path + '\\' + filename

			try:
				with open(file_path, 'wb') as f: f.write(data.content)
			except requests.exceptions.ConnectionError as e:
				with open(file_path + " [Corrupted]", 'wb') as f: f.write(''.encode())
	
	else:
		logging.info(f'          Already saved: {filename}')
		if Options.dup_info: print(f'        Already saved: {filename}')
		dups_count += 1
		local_dups_count[0] += 1
	stinfo = os.stat(file_path)
	os.utime(file_path,(stinfo.st_mtime, time.mktime(time.strptime(date, '%Y-%m-%d %X'))))

	global db_new_lookup
	if db_new_lookup == '': db_new_lookup = date

# on mtl, utl and search, change status of user to active if its accessible
# DONE      -   if user in db, do not check ids lower than the 'last id' stored on the db when -nd is true

def main():
	global api, auth, authenticated_user
	credentials = {}
	print()
	script_start = time.strftime("%X", time.localtime())

	if not Options.nolog:
		logging.basicConfig(handlers=[logging.FileHandler('activity_log ' + str(time.strftime("%y-%m-%d %H.%M.%S", time.localtime())) + '.txt', 'w', 'utf-8')],level=logging.INFO,
		 format="%(asctime)s %(levelname)-4s %(message)s",
		 datefmt="%Y-%m-%d %H:%M:%S")
		logging.info("  Starting UTG")
		logging.info(f"  Started at: {script_start}\n")
	
	try:
		if Options.keys is not None:
			credentials = json.load(open(Options.keys[0]))
			auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
			auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
			api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
			authenticated_user = api.verify_credentials()
		
		if Options.lookup_id is not None:		lookup_tweet()
		if Options.search is not None:			search_tweets()
		if Options.retweet is not None:			id_queue('retweet')
		if Options.unretweet is not None:		id_queue('unretweet')
		if Options.like is not None:			id_queue('like')
		if Options.dislike is not None:			id_queue('dislike')
		if Options.single is not None:			single_tweet()
		if Options.follow is not None:			follow_users()
		if Options.update_all:					update_all()
		if Options.check_again is not None:		retry_non_active()
		if Options.my_timeline:					fetch_tweets()
		if Options.user_timeline is not None:
			fetch_tweets(Options.user_timeline[0])
			if SQ.get_user(Options.user_timeline[0]) is not None and db_new_last_id != '0' and db_new_lookup != '':
				user = SQ.get_user(Options.user_timeline[0])
				db_operations.update_user(Options.user_timeline[0],db_new_last_id,db_new_lookup)
				if user[0][1] != 'Active': db_operations.update_user_status(Options.user_timeline[0],'Active')
			elif SQ.get_user(Options.user_timeline[0]) is None:
				IQ.user(Options.user_timeline[0],db_new_last_id,db_new_lookup)
			print('\nDatabase updated!')

	except KeyboardInterrupt:	logging.info('\t\tSIGINT detected -- Stopping script')
	except TimeoutError:		print('\nClosing due to TimeoutError\n')
	except:						logging.exception("Unknown Error at the end of MAIN")

	if Options.print_already_downloaded_text:	db_operations.print_downloaded_with_text() 
	if Options.print_already_downloaded:		PQ.downloaded_tweets(include_command=True) 
	if Options.print_renamed:					PQ.renamed_users(include_command=True)
	if Options.print_deleted:					PQ.deleted_users()
	if Options.print_errors:					PQ.errors()
	if Options.print_users is not None:			PQ.users(Options.print_users[0]) 
	if Options.print_likes is not None:			PQ.likes(Options.print_likes[0])

	if Options.add_user is not None:			IQ.user(user=Options.add_user[0])
	if Options.remove_user is not None:			db_operations.delete_user(Options.remove_user[0])
	if Options.rename_user is not None:			db_operations.rename_user(Options.rename_user[0], Options.rename_user[1], ' '.join(sys.argv)[:97]+'...', Options.forced)
	if Options.fuse_users is not None:			db_operations.fuse_users(Options.fuse_users[0], Options.fuse_users[1])
	if Options.update_status is not None:		db_operations.update_user_status(Options.update_status[0], Options.update_status[1])
	if Options.rescan_user is not None:			db_operations.rescan_user(Options.rescan_user[0])
	if Options.rescan_all:						db_operations.rescan_all()    

	db_operations.conn.close()  
	print('\nClosing...\n')
	
	print(f'\tFetched {fetched_tweets} tweets')
	print(f'\tSaved {file_count} images / gifs / videos')
	print(f'\tFound {dups_count} duplicate files')
	print(f'\tStarted at:  {script_start}')
	print(f'\tEnded at:    {time.strftime("%X", time.localtime())}')
	print(f'\tRun time:    {time.strftime("%X", time.gmtime(time.time() - start_time))}')
	#winsound.PlaySound('doves.wav', winsound.SND_FILENAME)

	end_time = time.strftime("%X", time.localtime())
	run_time = time.strftime("%X", time.gmtime(time.time() - start_time))

	logging.info(f'\tFetched {fetched_tweets} tweets')
	logging.info(f'\tSaved {file_count} files')
	logging.info(f'\tFound {dups_count} duplicate files')
	logging.info(f'\tStarted at: {script_start}')
	logging.info(f'\tEnded at: {end_time}')
	logging.info(f'\tRun time: {run_time}')
	if(Options.sleep):   os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

if __name__== "__main__":
	
	with open('TIG_commands_history.txt', 'a', encoding='utf-8') as history:
		history.write(time.strftime("%d/%m/%y %X", time.localtime()) + ' ---- ' + ' '.join(sys.argv) + '\n')

	parser = argparse.ArgumentParser()

	# Basic Options
	parser.add_argument('-k', '--keys', help='Specifies the JSON file containing your API keys',type=str,metavar=('JSON_FILE'), nargs=1)
	parser.add_argument('-mtl', '--my_timeline', help='Downloads media from YOUR Timeline (the account associated with the Access Token / Keys you provided) (800 tweets max.)', action='store_true')
	parser.add_argument('-utl', '--user_timeline', help='Downloads media from the specified user (Up to 3200 tweets)', nargs=1, metavar=('USER_NAME'))
	parser.add_argument('-lk', '--like', help='Likes the specified tweet(s)', nargs='+', metavar=('TWEET_ID'))
	parser.add_argument('-rt', '--retweet', help='Retweets the specified tweet(s)', nargs='+', metavar=('TWEET_ID'))
	parser.add_argument('-dlk', '--dislike', help='Removes the specified tweet(s) from your Likes', nargs='+', metavar=('TWEET_ID'))
	parser.add_argument('-urt', '--unretweet', help='Removes the specified retweet(s) from your timeline', nargs='+', metavar=('TWEET_ID'))
	parser.add_argument('--single', help='Downloads media from a single (or multiple) tweet(s).', nargs='+', metavar=('TWEET_ID'))
	parser.add_argument('--follow', help='Follows the given accounts', nargs='+', metavar=('TWITTER_HANDLE'))
	parser.add_argument('--search', help='Downloads media from tweets that include the specified #hashtag / word.', nargs='+', metavar=('QUERY'))
	parser.add_argument('--update_all', help="It will try to update all ACTIVE users from the database", action='store_true')

	# Advanced Options
	parser.add_argument('-nrt', '--no_retweets', help='Prevents retweets from being downloaded', action='store_false')
	parser.add_argument('-nrp', '--no_replies', help='Prevents replies from being downloaded', action='store_true')
	parser.add_argument('-nimg', '--no_image', help='Prevents images from being downloaded (Only gif/videos will be downloaded)', action='store_true')
	parser.add_argument('-nvid', '--no_video', help='Prevents videos/gif from being downloaded', action='store_true')
	parser.add_argument('-mxd', '--max_dups', help='Stops the download after it finds more than N duplicate files.',type=int, nargs=1,metavar=('N'))
	parser.add_argument('-mxf', '--max_fetch', help='Stops the download after it fetches N duplicate tweets.',type=int, nargs=1,metavar=('N'))
	parser.add_argument('-nd', '--no_dups', help='Exits the script after finding the first duplicate image', action='store_true')
	parser.add_argument('--skip', help='Used with --update-all. It will try to update all users from the database except for those specified in this list', nargs='+', metavar=('USER_NAME'))
	parser.add_argument('--start_at', help='When used with -utl, the script will only download tweets with an ID number lower than the one provided. When used with --update-all, ----------- ---------- ---------', nargs=1, metavar=('TWEET_ID / USER_NAME'))
	parser.add_argument('--save_to_user_folder', help="If a tweet's author is in the database, it will download the tweet into their user folder, instead of the default folder.", action='store_true')
	parser.add_argument('--only_db', help='Only saves media from tweets whose author is in the database', action='store_true')
	parser.add_argument('--sleep', help='Puts the computer to sleep once the script finishes.', action='store_true')
	parser.add_argument('--dup_info', help="It will print a message (both in console and logging file) whenever it tries to download a tweet that's already stored in it's respective folder", action='store_true')
	parser.add_argument('--delete_tweets', help='Deletes the specified tweet(s), as long as they belong to the user authenticated', nargs='+', metavar=('TWEET_ID'))
	parser.add_argument('--lookup_id', help='Checks a single tweet and prints its information', nargs="+", metavar=('TWEET_ID'))
	parser.add_argument('--check_last_id', help='If the user is in the DB, the script will stop downloading tweets whenever it find a tweet with an ID lower than the one stored in the DB', action='store_true')
	parser.add_argument('--nolog', help="If used, the script will not create a log file", action='store_true')
	parser.add_argument('--into', help="When providing a valid path, the script will proceed to download all media into the specified folder path", nargs=1, metavar=('FOLDER_PATH'))
	parser.add_argument('--split', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--check_table', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--print_already_downloaded', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--print_already_downloaded_text', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--store_in_tmp', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--time', nargs=1, type=int, metavar=('SECONDS'), help=argparse.SUPPRESS)

	# Database Options
	parser.add_argument('--print_users', help='Prints all users stored in your Database.',nargs='?', metavar=('ORDER'), const="x")
	parser.add_argument('--print_likes', help='Prints all likes stored in your Database.', nargs=1, metavar=('OWNER'))
	parser.add_argument('--print_renamed', help='Prints all the renames done', action='store_true')
	parser.add_argument('--print_errors', help='Prints all the renames done', action='store_true')
	parser.add_argument('--print_deleted', help='Prints all the renames done', action='store_true')
	parser.add_argument('--add_user', help='Adds the specified user to the database (With Last_id=0 & Date=None)',nargs=1, metavar=('USER_NAME'))
	parser.add_argument('--remove_user', help='Removes the specified user from the database (and deletes their folder)',nargs=1, metavar=('USER_NAME'))
	parser.add_argument('--rename_user', help='Renames the specified user from the database (and renames the files in their folder)',nargs=2, metavar=('OLD_NAME', 'NEW_NAME'))
	parser.add_argument('--fuse_users', help='Renames the specified user from the database (and renames the files in their folder)',nargs=2, metavar=('OLD_NAME', 'NEW_NAME'))
	parser.add_argument('--update_status', help='Changes the status of the specified user',nargs=2, metavar=('USER_NAME', 'NEW_STATUS'))
	parser.add_argument('--rescan_user', help='Scans the user folder in order to update its Last_id field in the database.',nargs=1, metavar=('USER_NAME'))
	parser.add_argument('--rescan_all', help="Scans all users' folders in order to update their Last_id field in the database.", action='store_true')
	parser.add_argument('--forced', help="", action='store_true')
	parser.add_argument('--check_again', help='Tries to download media from those users whose status match with the one provided',nargs=1, metavar=('STATUS'))

	Options = None
	Options = parser.parse_args()

	main()