#  -*- coding: utf-8 -*-
'''
Created on 2 Apr 2018

@author: Kernel-13
'''

import sys
import os
import time
import json
import tweepy
import sqlite3
import logging
import requests
import argparse
import winsound
from math import ceil

import Queries.insertQueries as IQ
import Queries.selectQueries as SQ
import Queries.updateQueries as UQ
import Queries.printQueries as PQ
import Queries.Exceptions as MsgPrinter

API = None
AUTHENTICATED_USER = None
OPTIONS = None

DUPES_COUNT = 0
FILE_COUNT = 0
FETCHED_TWEETS_COUNT = 0

COMMAND_ARGUMENTS = ' '.join(sys.argv)

#print(json.dumps(tweet._json, sort_keys=True, indent=4))

def id_queue(action):
	
	if action == "like": 		queue = OPTIONS.like
	elif action == "dislike": 	queue = OPTIONS.dislike
	elif action == "retweet": 	queue = OPTIONS.retweet
	elif action == "unretweet": queue = OPTIONS.unretweet

	logging.info("Queue Size: {}\n".format(len(queue)))

	for tweet_id in queue:
		try:

			if action == "retweet":		API.retweet(tweet_id)
			elif action == "unretweet":	API.unretweet(tweet_id)
			elif action == "like": 		
				API.create_favorite(tweet_id)
				tweet = API.get_status(tweet_id)
			elif action == "dislike":	
				API.destroy_favorite(tweet_id)

			MsgPrinter.print_info("ID: {} - Operation: {} - Status: Success".format(tweet_id, action.upper()))

		except tweepy.error.TweepError as err:

			if err.response.status_code == 429:
				error_message = 'The request limit for this resource has been reached.'
			else:
				error_message = err.response.json()['errors'][0]['message']

			MsgPrinter.print_error("ID: {} ---> {} (Operation: {})".format(tweet_id, error_message, action.upper()))

		else:
			try:
				if action == "like":
					IQ.like(tweet, AUTHENTICATED_USER.screen_name)
				elif action == "dislike":
					UQ.remove_like(tweet_id, AUTHENTICATED_USER.screen_name)

			except sqlite3.IntegrityError as err:
				logging.error("IntegrityError: ID {} already in LIKED_TWEETS")

		time.sleep(OPTIONS.time[0]) 

def update_all():

	user_list = SQ.get_user_list('Active')

	try:
		start_idx = user_list.index(OPTIONS.start_at_user[0].lower()) if OPTIONS.start_at_user else 0

	except ValueError: 
		user = SQ.get_user(OPTIONS.start_at_user[0])

		if user:
			MsgPrinter.print_error("User [ {} ] is marked as '{}'!".format(user[0], user[1]))
			print("\t\t\tTry using the '--check_again' option to check if its accessible again.")
			print("\t\t\tYou can also use '--update_status' to manually change its status.")

		else:
			MsgPrinter.print_error("User [ {} ] is not in the database!".format(OPTIONS.start_at_user[0]))
		
		return

	if OPTIONS.skip:
		for user in OPTIONS.skip:
			if user.lower() in user_list:  user_list.remove(user)

	for user in user_list[start_idx::]:
		MsgPrinter.print_info("Updating User: {}".format(user))
		user_timeline(user)

def retry_non_active():

	non_active = SQ.get_user_list(OPTIONS.check_again[0])
	active_users = []
	private_users = []
	accessible_users = dict()

	for i in range(ceil(len(non_active)/100)):

		try:
			returned_users = API.lookup_users(screen_names=non_active[i*100:(i+1)*100])
		except tweepy.error.TweepError:
			continue

		for user in returned_users:
			if user.protected:
				if user.following: 
					active_users.append(user.screen_name.lower())
				else: 
					private_users.append(user.screen_name.lower())
			else:
				active_users.append(user.screen_name.lower())

	logging.info("Function: RETRY_NON_ACTIVE(): Iterating over ACTIVE_USERS list")
	for user in active_users:
		MsgPrinter.print_info("Checking {}".format(user))
		user_timeline(user)
		UQ.update_user(user, status='Active')
		non_active.remove(user)

	logging.info("Function: RETRY_NON_ACTIVE(): Iterating over PRIVATE_USERS list")
	for user in private_users:
		MsgPrinter.print_info("Checking {}".format(user))
		UQ.update_user(user, status='Protected')
		non_active.remove(user)

	logging.info("Function: RETRY_NON_ACTIVE(): Iterating over NON_ACTIVE list")
	users_with_no_tweets = []
	for user in non_active:

		random_tweet = SQ.get_random_tweet(user)

		if random_tweet:
			MsgPrinter.print_info("Checking {}".format(user))
			tweet_id = random_tweet[1]
			
			try:
				status = API.get_status(tweet_id)
				new_name = status.author.screen_name
				accessible_users[user] = new_name
				MsgPrinter.print_warning("Found new name for [ {} ]: {}\n".format(user, new_name))

			except tweepy.error.TweepError as err:

				if err.response.status_code == 429:
					error_message = 'The request limit for this resource has been reached.'
					IQ.error(username, 'RateLimit', 429)
					MsgPrinter.print_warning(error_message)

				else:
					error_code, error_message = err.response.json()['errors'][0].values()

					if error_code == 63:	# User Suspended
						MsgPrinter.print_warning(error_message)
						UQ.update_user(user, status='Suspended')
						IQ.error(user, 'Suspended', error_code)

					elif error_code in (144, 34):	# Tweet Deleted

						if OPTIONS.deep_check:
							user_tweets = SQ.get_ids_from_user(user)
							is_accesible = False

							for i in range(ceil(len(user_tweets)/100)):
								returned_status = API.statuses_lookup(user_tweets[i*100:(i+1)*100])

								if len(returned_status) != 0:
									accessible_users[user] = returned_status[0].author.screen_name
									is_accesible = True
									break
								else:
									time.sleep(20)

							if not is_accesible:
								IQ.error(user, 'Deleted', error_code)
								MsgPrinter.print_warning("User has been deleted and / or deleted their old tweets")

						else:
							MsgPrinter.print_warning("The random tweet check didn't return anything. Try using the --deep_check option to check all past tweets from this user.")
							logging.warning(error_message)
							UQ.update_user(user, status='Not Accessible')

					elif error_code == 179:	# User Private
						MsgPrinter.print_warning("You are not authorized to see this user's tweets.")
						IQ.error(user, 'Protected', error_code)
						UQ.update_user(user, status='Protected')

					else:
						print(err)
						MsgPrinter.print_error(error_message)

				print()
		else:
			users_with_no_tweets.append(user)

	if len(users_with_no_tweets) != 0:
		print("Users that we could not check because there are no tweets saved under their name:", *users_with_no_tweets)

	logging.info("Users that will be renamed:")
	for k,v in accessible_users.items(): logging.info("{} > {}".format(k,v))

	for old_name, new_name in accessible_users.items():
		try:
			UQ.rename_user(old_name, new_name, COMMAND_ARGUMENTS)
			MsgPrinter.print_info("Updating User: {}".format(user))
			user_timeline(new_name)
			UQ.update_user(new_name, status='Active')
			
		except MsgPrinter.UserExists as err:
			print(err)
			print("Try using the --fuse_users option to merge both users.")

		except MsgPrinter.FolderExists as err:
			print(err)
			print("Try moving / deleting the following folder before any rename takes place:", os.path.join(os.getcwd(), new_name))

def follow_users():
	for user in OPTIONS.follow:
		try:
			API.create_friendship(user)
			time.sleep(30)
		except tweepy.error.TweepError as err:
			MsgPrinter.print_error("{} ---> {}".format(user, err.response.json()['errors'][0]['message']))

def search_tweets():
	save_folder = os.path.join('_____SEARCH_____', ''.join([ch if ch not in '\\/:"*?<>|' else '_' for ch in OPTIONS.search[0].strip()]))
	os.makedirs(save_folder, exist_ok=True) 

	for tweet in tweepy.Cursor(API.search, q=' '.join(OPTIONS.search), count=100, include_entities=True, tweet_mode='extended').items(): 
		process_tweet(tweet, save_folder)

def single_tweet():
	os.makedirs('_____SINGLE_____', exist_ok=True)

	for tweet in OPTIONS.single:
		try:
			process_tweet(API.get_status(tweet, tweet_mode='extended'), '_____SINGLE_____')
		except tweepy.error.TweepError as err:
			MsgPrinter.print_error("{} ---> {}".format(tweet, err.response.json()['errors'][0]['message']))

def my_timeline():

	save_folder = "{}'s Timeline".format(AUTHENTICATED_USER.screen_name)
	os.makedirs(save_folder, exist_ok=True)

	tweets = API.home_timeline(count=200, 
		exclude_replies=OPTIONS.no_replies, 
		include_rts=OPTIONS.no_retweets, 
		tweet_mode='extended',
		max_id=OPTIONS.start_at_id[0] if OPTIONS.start_at_id else None)

	while len(tweets) > 0:

		for tweet in tweets: process_tweet(tweet, save_folder)

		tweets = API.home_timeline(count=200, 
			exclude_replies=OPTIONS.no_replies, 
			include_rts=OPTIONS.no_retweets, 
			tweet_mode='extended',
			max_id=(tweets[-1].id - 1))

def user_timeline(username):

	save_folder = username
	os.makedirs(username, exist_ok=True)

	try:
		tweets = API.user_timeline(screen_name=username,
			count=200,
			exclude_replies=OPTIONS.no_replies,
			include_rts=OPTIONS.no_retweets,
			tweet_mode='extended',
			max_id=OPTIONS.start_at_id[0] if OPTIONS.start_at_id else None)

		while len(tweets) > 0:
			
			for tweet in tweets: process_tweet(tweet, save_folder)

			tweets = API.user_timeline(screen_name=username,
				count=200,
				exclude_replies=OPTIONS.no_replies,
				include_rts=OPTIONS.no_retweets,
				tweet_mode='extended',
				max_id=(tweets[-1].id - 1))

		if SQ.get_user(username) is None:
			IQ.user(username)

		#UQ.update_user(username, status='Active')

	except tweepy.error.TweepError as err:

		if err.response.status_code == 429:
			error_message = 'The request limit for this resource has been reached.'
			IQ.error(username, 'RateLimit', 429)

		else:
			error_code, error_message = err.response.json()['errors'][0].values()
			
			if error_code == 63:	# User Suspended
				UQ.update_user(username, status='Suspended')
				IQ.error(username, 'Suspended', error_code)

			elif error_code == 144:	# Tweet Deleted
				UQ.update_user(username, status='Deleted')
				IQ.error(username, 'Deleted', error_code)

			elif error_code == 179: # User Private
				UQ.update_user(username, status='Protected')
				IQ.error(username, 'Protected', error_code)

		MsgPrinter.print_error(error_message)

	except (MsgPrinter.MaxDupesFound, MsgPrinter.MaxTweetsFetched) as err:
		global DUPES_COUNT, FETCHED_TWEETS_COUNT
		DUPES_COUNT = 0 
		FETCHED_TWEETS_COUNT = 0 
		MsgPrinter.print_warning(err)

	except Exception as err:
		MsgPrinter.print_error(err)

def process_tweet(tweet, save_folder):
	global DUPES_COUNT, FETCHED_TWEETS_COUNT
	FETCHED_TWEETS_COUNT += 1

	if OPTIONS.max_dups:
		if DUPES_COUNT >= OPTIONS.max_dups[0]:
			raise MsgPrinter.MaxDupesFound("Reached {} duplicated tweets.".format(DUPES_COUNT))

	if OPTIONS.max_fetch:
		if FETCHED_TWEETS_COUNT >= OPTIONS.max_fetch[0]:
			raise MsgPrinter.MaxTweetsFetched("Fetched {} tweets.".format(DUPES_COUNT))

	if hasattr(tweet, "retweeted_status"):
		tweet = tweet.retweeted_status

	date = tweet.created_at.strftime('%Y-%m-%d %X')
	
	try:
		if SQ.already_downloaded(tweet.id):
			MsgPrinter.print_warning(">>>>> Already downloaded: {} {}".format(tweet.author.screen_name, tweet.id_str))
			DUPES_COUNT += 1
			return

		if tweet.extended_entities['media']:

			for media_count, media in enumerate(tweet.extended_entities['media']):

				if OPTIONS.no_video and OPTIONS.no_image:
					return

				if 'video_info' in media and not OPTIONS.no_video:
					bitrate = 0

					for item in media["video_info"]["variants"]:
						if item["content_type"] == "video/mp4" and item["bitrate"] >= bitrate:
							bitrate = item["bitrate"]
							url = item["url"]
					
					file_extension = url.split('.')[-1]

				elif 'video_info' not in media and not OPTIONS.no_image:
					url = media['media_url']
					file_extension = url.split('.')[-1]
					url += ':orig'

				else:
					break

				if '?' in file_extension:	# Special case
					file_extension = file_extension.split('?')[0]

				try:
					content = requests.get(url, stream=True, timeout=1) 

				except Exception as err:
					MsgPrinter.print_error(err)
					logging.info("## Tweet Author: {}".format(tweet.author.screen_name))
					logging.info("## Tweet ID: {}".format(tweet.id_str))
					logging.info("## File Format: {}".format(file_extension))
					logging.info("## Media URL: {}".format(url))
					return

				file_name = "{} {} [{}].{}".format(tweet.author.screen_name, tweet.id_str, media_count+1, file_extension)
				file_path = os.path.join(save_folder, file_name)
				save_file(file_path, content, date)

				'''
				if OPTIONS.save_to_user_folder:

					if SQ.get_user(tweet.author.screen_name) is not None:   
						file_path = os.path.join(os.getcwd(), tweet.author.screen_name, file_name)

					elif OPTIONS.only_db:   
						break

					else:   
						file_path = save_folder + '\\' + file_name
				else:
					file_path = save_folder + '\\' + file_name

				if OPTIONS.into is not None:
					if os.path.isdir(OPTIONS.into[0]):
						if OPTIONS.split:
							db_path = OPTIONS.into[0] + '\\' + 'IN_DB'
							not_db_path = OPTIONS.into[0] + '\\' + 'NOT_IN_DB'
							os.makedirs(db_path, exist_ok=True)
							os.makedirs(not_db_path, exist_ok=True)
							if SQ.get_user(tweet.author.screen_name) is not None:   file_path = db_path + '\\'+ file_name
							else:   file_path = not_db_path + '\\' + file_name
						else:
							file_path = OPTIONS.into[0] + '\\' + file_name

				'''

			IQ.download(tweet, COMMAND_ARGUMENTS[:97] + '...' if len(COMMAND_ARGUMENTS) > 100 else COMMAND_ARGUMENTS)

	#except sqlite3.IntegrityError as err:

	except AttributeError as err:
		pass
		#logging.error("{} has no extended_entities => Can't be downloaded".format(tweet.id_str))
	
def save_file(file_path, data, date):

	global FILE_COUNT
	_, filename = os.path.split(file_path)

	if os.path.exists(file_path) and os.path.getsize(file_path) == len(data.content):
		MsgPrinter.print_warning("Already saved: {}".format(filename))
		return

	MsgPrinter.print_info("Saving: {}".format(filename))
	
	try:
		with open(file_path, 'wb') as f:
			f.write(data.content)
			FILE_COUNT += 1

		os.utime(file_path, (os.stat(file_path).st_mtime, time.mktime(time.strptime(date, '%Y-%m-%d %X'))))

	except requests.exceptions.ConnectionError as err:
		MsgPrinter.print_error(err)

	'''
	if OPTIONS.store_in_tmp:
		db_path = 'D:' + '\\' + 'TEMP' + '\\' + 'IN_DB'
		not_db_path = 'D:' + '\\' + 'TEMP' + '\\' + 'NOT_IN_DB'

		if SQ.get_user(filename.split()[0]) is not None:   
			file_path = db_path + '\\'+ filename
		else:   
			file_path = not_db_path + '\\' + filename

		try:
			with open(file_path, 'wb') as f: 
				f.write(data.content)
		except requests.exceptions.ConnectionError as err:
			MsgPrinter.print_error(err)
	'''
	
def main():
	global API, AUTHENTICATED_USER
	start_time = time.time()        #Change to time.localtime()
	script_start = time.strftime("%X", time.localtime())
	print()
	
	try:
		if OPTIONS.keys is not None:
			
			credentials = json.load(open(OPTIONS.keys[0]))
			auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
			auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
			API = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
			AUTHENTICATED_USER = API.verify_credentials()

			#if OPTIONS.lookup_id is not None:		lookup_tweet()
			if OPTIONS.search is not None:			search_tweets()
			if OPTIONS.retweet is not None:			id_queue('retweet')
			if OPTIONS.unretweet is not None:		id_queue('unretweet')
			if OPTIONS.like is not None:			id_queue('like')
			if OPTIONS.dislike is not None:			id_queue('dislike')
			if OPTIONS.single is not None:			single_tweet()
			if OPTIONS.follow is not None:			follow_users()
			if OPTIONS.update_all:					update_all()
			if OPTIONS.check_again is not None:		retry_non_active()
			if OPTIONS.my_timeline:					my_timeline()
			if OPTIONS.user_timeline:				user_timeline(OPTIONS.user_timeline[0])

			# Windows only
			if(OPTIONS.sleep):   
				os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
		
	except (MsgPrinter.MaxDupesFound, MsgPrinter.MaxTweetsFetched) as err:
		pass

	except KeyboardInterrupt:	
		raise

	except tweepy.error.TweepError as err:
		MsgPrinter.print_error(err.response.json()['errors'][0]['message'])

	except TimeoutError as err:		
		MsgPrinter.print_error(err)

	except Exception as err:
		logging.exception(err)		

	if OPTIONS.print_downloads_text:		PQ.downloaded_tweets(include_command=True)
	if OPTIONS.print_downloads:				PQ.downloaded_tweets(include_command=False) 
	if OPTIONS.print_renamed:				PQ.renamed_users(include_command=True)
	if OPTIONS.print_deleted:				PQ.deleted_users()
	if OPTIONS.print_errors:				PQ.errors()
	if OPTIONS.print_users is not None:		PQ.users(OPTIONS.print_users[0]) 
	if OPTIONS.print_likes is not None:		PQ.likes(OPTIONS.print_likes[0])

	if OPTIONS.add_user is not None:		IQ.user(user=OPTIONS.add_user[0])
	if OPTIONS.remove_user is not None:		UQ.delete_user(OPTIONS.remove_user[0])
	if OPTIONS.rename_user is not None:		UQ.rename_user(OPTIONS.rename_user[0], OPTIONS.rename_user[1], COMMAND_ARGUMENTS)
	if OPTIONS.fuse_users is not None:		UQ.fuse_users(OPTIONS.fuse_users[0], OPTIONS.fuse_users[1])
	if OPTIONS.update_status is not None:	UQ.update_user(OPTIONS.update_status[0], status=OPTIONS.update_status[1])
	#if OPTIONS.rescan_user is not None:	db_operations.rescan_user(OPTIONS.rescan_user[0])
	#if OPTIONS.rescan_all:					db_operations.rescan_all()    

	print()

	end_time = time.strftime("%X", time.localtime())
	run_time = time.strftime("%X", time.gmtime(time.time() - start_time))

	if FETCHED_TWEETS_COUNT != 0:
		MsgPrinter.print_info("Fetched {} tweets".format(FETCHED_TWEETS_COUNT))
		MsgPrinter.print_info("Saved {} files".format(FILE_COUNT))
		MsgPrinter.print_info("Found {} duplicate tweets".format(DUPES_COUNT))

	MsgPrinter.print_info("Started at: {}".format(script_start))
	MsgPrinter.print_info("Ended at: {}".format(end_time))
	MsgPrinter.print_info("Run time: {}".format(run_time))	
	#winsound.PlaySound('doves.wav', winsound.SND_FILENAME)	

if __name__== "__main__":
	
	with open('TIG_commands_history.txt', 'a', encoding='utf-8') as history:
		history.write(time.strftime("%d/%m/%y %X", time.localtime()) + ' ---- ' + COMMAND_ARGUMENTS + '\n')

	os.makedirs("______LOGS______", exist_ok=True)
	logpath = '[LOG] ' + time.strftime("%y-%m-%d %H.%M.%S", time.localtime()) + '.txt'
	logpath = os.path.join("______LOGS______", logpath)

	logging.basicConfig(handlers=[logging.FileHandler(logpath, 'w', 'utf-8')],
		level=logging.INFO,
		format="%(asctime)s %(levelname)-4s %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S")
	logging.info("Starting TIG\n")

	parser = argparse.ArgumentParser()

	# Basic OPTIONS
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

	# Advanced OPTIONS
	parser.add_argument('-nrt', '--no_retweets', help='Prevents retweets from being downloaded', action='store_false')
	parser.add_argument('-nrp', '--no_replies', help='Prevents replies from being downloaded', action='store_true')
	parser.add_argument('-nimg', '--no_image', help='Prevents images from being downloaded (Only gif/videos will be downloaded)', action='store_true')
	parser.add_argument('-nvid', '--no_video', help='Prevents videos/gif from being downloaded', action='store_true')
	parser.add_argument('-mxd', '--max_dups', help='Stops the download after it finds more than N duplicate files.',type=int, nargs=1,metavar=('N'))
	parser.add_argument('-mxf', '--max_fetch', help='Stops the download after it fetches N duplicate tweets.',type=int, nargs=1,metavar=('N'))
	parser.add_argument('-nd', '--no_dups', help='Exits the script after finding the first duplicate image', action='store_true')
	parser.add_argument('--skip', help='Used with --update-all. It will try to update all users from the database except for those specified in this list', nargs='+', metavar=('USER_NAME'))
	parser.add_argument('--start_at_user', help='When used with -utl, the script will only download tweets with an ID number lower than the one provided. When used with --update-all, ----------- ---------- ---------', nargs=1, metavar=('TWEET_ID / USER_NAME'))
	parser.add_argument('--start_at_id', help='When used with -utl, the script will only download tweets with an ID number lower than the one provided. When used with --update-all, ----------- ---------- ---------', nargs=1, metavar=('TWEET_ID / USER_NAME'))
	parser.add_argument('--save_to_user_folder', help="If a tweet's author is in the database, it will download the tweet into their user folder, instead of the default folder.", action='store_true')
	parser.add_argument('--only_db', help='Only saves media from tweets whose author is in the database', action='store_true')
	parser.add_argument('--sleep', help='Puts the computer to sleep once the script finishes.', action='store_true')
	#parser.add_argument('--dup_info', help="It will print a message (both in console and logging file) whenever it tries to download a tweet that's already stored in it's respective folder", action='store_true')
	parser.add_argument('--delete_tweets', help='Deletes the specified tweet(s), as long as they belong to the user authenticated', nargs='+', metavar=('TWEET_ID'))
	parser.add_argument('--lookup_id', help='Checks a single tweet and prints its information', nargs="+", metavar=('TWEET_ID'))
	parser.add_argument('--check_last_id', help='If the user is in the DB, the script will stop downloading tweets whenever it find a tweet with an ID lower than the one stored in the DB', action='store_true')
	#parser.add_argument('--log', help="If used, the script will create a log file.", action='store_true')
	parser.add_argument('--into', help="When providing a valid path, the script will proceed to download all media into the specified folder path", nargs=1, metavar=('FOLDER_PATH'))
	parser.add_argument('--split', action='store_true', help=argparse.SUPPRESS)
	#parser.add_argument('--check_table', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--print_downloads', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--print_downloads_text', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--store_in_tmp', action='store_true', help=argparse.SUPPRESS)
	parser.add_argument('--time', nargs=1, type=int, metavar=('SECONDS'), help=argparse.SUPPRESS)

	# Database OPTIONS
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
	#parser.add_argument('--rescan_user', help='Scans the user folder in order to update its Last_id field in the database.',nargs=1, metavar=('USER_NAME'))
	#parser.add_argument('--rescan_all', help="Scans all users' folders in order to update their Last_id field in the database.", action='store_true')
	#parser.add_argument('--forced', help="", action='store_true')
	parser.add_argument('--deep_check', help="", action='store_true')
	parser.add_argument('--check_again', help='Tries to download media from those users whose status match with the one provided',nargs=1, metavar=('STATUS'))

	OPTIONS = parser.parse_args()
	main()