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
from pathlib import Path

dups_count = 0
file_count = 0
tweet_count = 0

def fetch_tweets(credentials, options):
    
    auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
    auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    tweets = []
    user = api.verify_credentials()
    
    try:
        if options['id_to_retweet'] != '':
            try:
                api.retweet(options['id_to_retweet'])
                return
            except tweepy.error.TweepError:
                print('ERROR    ---    You have already retweeted this Tweet.')
                sys.exit()
        elif options['my_timeline']:
            if options['no_replies']:
                tweets = api.home_timeline(count=200,exclude_replies=True)
            else:
                tweets = api.home_timeline(count=200)
            save_folder = user.screen_name + "'s Timeline"
        elif options['single'] != '':
            twt = api.get_status(options['single'])
            save_folder = '_tmp'
            tweets.append(twt)
        else:
            save_folder = options['user']
            if options['no_replies'] and options['no_retweets']:
                tweets = api.user_timeline(screen_name=options['user'],count=200,exclude_replies=True,include_rts=False)
            elif options['no_replies'] and not options['no_retweets']:
                tweets = api.user_timeline(screen_name=options['user'],count=200,exclude_replies=True)
            elif not options['no_replies'] and options['no_retweets']:
                tweets = api.user_timeline(screen_name=options['user'],count=200,include_rts=False)
            else:
                tweets = api.user_timeline(screen_name=options['user'],count=200)
    except tweepy.TweepError as e:
        print ('\n    ---    Error    ---')
        print ('Error Code: ' + str(e.args[0][0]['code']))
        print ('Error Message: ' + e.args[0][0]['message'])
        print ('For more info about this error, check https://developer.twitter.com/en/docs/basics/response-codes')
        return
          
    try: 
        oldest = tweets[-1].id - 1     
        os.makedirs(save_folder, exist_ok=True)
    except IndexError:
        return
    
    global tweet_count
    while len(tweets) > 0:
        for twt in tweets:
            try:
                date = str(twt.created_at)
                if hasattr(twt, "retweeted_status"):
                    twt = twt.retweeted_status
            
                if hasattr(twt, "extended_entities"):
                    if twt.extended_entities['media']:
                        count = 1
                        for media in twt.extended_entities['media']:
                            if 'video_info' in media and options['get_videos']:
                                bitrate = 0
                                url = ''
                                videos = media["video_info"]["variants"]
                                for i in videos:
                                    if i["content_type"] == "video/mp4" and i["bitrate"] >= bitrate:
                                        bitrate = i["bitrate"]
                                        url = i["url"]
                            elif options['get_images']:
                                url = media['media_url']
                            else:
                                break
                            content = requests.get(url, stream=True) 
                            file_extension = url.rsplit('.', 1)[1]
                            if '?' in file_extension:                           # Special case
                                file_extension = file_extension.split('?')[0]
                            file_name = twt.author.screen_name + ' ' + twt.id_str + ' ['+ str(count) + '].' + file_extension
                            save_file(save_folder + '\\' + file_name, content, date)
                            count += 1
                            
                            if options['no_dups'] and dups_count > 0:
                                return
                            
                if options['max_dups'] != 0 and dups_count >= options['max_dups']:
                    print('\nDone    ---    Reached the max. number of duplicate files (' + str(options['max_dups']) + ')')
                    return
            except AttributeError:
                print('ERROR ---- Twitter User: ' + twt.author.screen_name + ' ----- Tweet ID: ' + twt.id_str)

            tweet_count += 1

        if options['single']:
            break

        if options['my_timeline']:
            if options['no_replies']:
                tweets = api.home_timeline(count=200,exclude_replies=True,max_id=oldest)
            else:
                tweets = api.home_timeline(count=200,max_id=oldest)
        else:
            if options['no_replies'] and options['no_retweets']:
                tweets = api.user_timeline(screen_name=options['user'],count=200,exclude_replies=True,include_rts=False,max_id=oldest)
            elif options['no_replies'] and not options['no_retweets']:
                tweets = api.user_timeline(screen_name=options['user'],count=200,exclude_replies=True,max_id=oldest)
            elif not options['no_replies'] and options['no_retweets']:
                tweets = api.user_timeline(screen_name=options['user'],count=200,include_rts=False,max_id=oldest)
            else:
                tweets = api.user_timeline(screen_name=options['user'],count=200,max_id=oldest)

        if len(tweets) > 0:
            oldest = tweets[-1].id - 1
    
    print('\nDone')
    return None

def save_file(file_path, data, date):
    file = Path(file_path)
    filename = file_path.rsplit('\\', 1)[1]
    if not file.exists() or os.path.getsize(file_path) != len(data.content):
        print('Saving: ' + filename)
        with open(file_path, 'wb') as f:
            f.write(data.content)
        global file_count
        file_count += 1
    else:
        print('Already exists: ' + filename)
        global dups_count 
        dups_count += 1
    d = time.mktime(time.strptime(date, '%Y-%m-%d %H:%M:%S'))
    stinfo = os.stat(file_path)
    os.utime(file_path,(stinfo.st_atime, d))    

def print_help(program_name):
    help_text = '\nUsage:\n'
    help_text += '    ' + program_name + ' --keys <credentials_file> --user-timeline <user> [--no-retweets] [--no-replies] [--max-dups N] [--no-video] [--no-image] [--no-dups]\n'
    help_text += '    ' + program_name + ' --keys <credentials_file> --my-timeline [--no-replies] [--max-dups N] [--no-video] [--no-image] [--no-dups]\n'
    help_text += '    ' + program_name + ' --keys <credentials_file> --single <id_to_download>\n'
    help_text += '    ' + program_name + ' --keys <credentials_file> --retweet <id_to_retweet>\n'
    help_text += '    ' + program_name + ' -h\n'
    
    help_text += '\nOptions:\n'
    help_text += '    ' + '{:<35}'.format('-h, --help') + 'Shows this screen\n'
    help_text += '    ' + '{:<35}'.format('-k, --keys <credentials_file>') + 'Specifies the JSON file containing your API keys\n'
    help_text += '    ' + '{:<35}'.format('-utl, --user-timeline <user_name>') + 'Downloads media from the specified user (Up to 3200 tweets)\n'
    help_text += '    ' + '{:<35}'.format('-mtl, --my_timeline') + 'Downloads media (800 tweets max.) from YOUR account (the account associated with the Access Token you provided)\n'
    help_text += '    ' + '{:<35}'.format('-nrt, --no-retweets') + 'Prevents retweets from being downloaded\n'
    help_text += '    ' + '{:<35}'.format('-nrp, --no-replies') + 'Prevents replies from being downloaded\n'
    help_text += '    ' + '{:<35}'.format('-nd, --no-dups') + 'Exits the script after finding the first duplicate image\n'
    help_text += '    ' + '{:<35}'.format('-nvid, --no-video') + 'Prevents videos/gif from being downloaded\n'
    help_text += '    ' + '{:<35}'.format('-nimg, --no-image') + 'Prevents images from being downloaded (Only gif/videos will be downloaded)\n'
    help_text += '    ' + '{:<35}'.format('-s, --single <id_to_download>') + 'Downloads media from a single tweet.\n'
    help_text += '    ' + '{:<35}'.format('-rt, --retweet <id_to_retweet>') + 'Retweets the specified tweet\n'
    help_text += '    ' + '{:<35}'.format('-mxd, --max_dups <N>') + 'Stops the download after it finds more than N duplicate files.\n'
    
    help_text += '\nExamples:\n'
    help_text += '    ' + program_name + ' -k my_keys.json -utl SenbaRambu --no-replies -mxd 50 --no-video\n'
    help_text += '    ' + program_name + ' -k my_keys.json -mtl --no-image\n'
    help_text += '    ' + program_name + ' -k my_keys.json --s 983792855834603520\n'
    help_text += '    ' + program_name + ' --keys my_keys.json --user-timeline SenbaRambu -nrp -nvid\n'
    help_text += '    ' + program_name + ' --keys my_keys.json --my-timeline --max_dups 75\n'
    help_text += '    ' + program_name + ' --keys my_keys.json --retweet 983792855834603520\n'
    
    print(help_text)
    return

def main(argv):
    
    credentials = {}
    options = {}
    options['no_retweets'] = False
    options['no_replies'] = False
    options['get_videos'] = True
    options['get_images'] = True
    options['my_timeline'] = False
    options['single'] = ''
    options['id_to_retweet'] = ''
    options['no_dups'] = False
    options['max_dups'] = 0
    
    count = 1
    try:
        while count < len(argv):
            if argv[count] in ("-h", "--help"):
                print_help(argv[0])
                sys.exit()
            elif argv[count] in ("-rt","--retweet"):
                count += 1  
                options['id_to_retweet'] = argv[count]
            elif argv[count] in ("-mtl", "--my-timeline"):
                options['my_timeline'] = True
            elif argv[count] in ("-k", "--keys"):
                count += 1
                credentials = json.load(open(argv[count]))
                credentials['json'] = argv[count]
            elif argv[count] in ("-utl", "--user-timeline"):
                count += 1
                options['user'] = argv[count]
            elif argv[count] in ('-nrt', '--no-retweets'):
                options['no_retweets'] = True
            elif argv[count] in ('-nrp', '--no-replies'):
                options['no_replies'] = False
            elif argv[count] in ('-nvid', '--no-video'):
                options['get_videos'] = False
            elif argv[count] in ('-nimg', '--no-image'):
                options['get_images'] = False
            elif argv[count] in ('-nd', '--no-dups'):
                options['no_dups'] = True
            elif argv[count] in ("-mxd", "--max-dups"):
                count += 1
                options['max_dups'] = abs(int(argv[count]))
            elif argv[count] in ("-s", "--single"):
                count += 1
                options['single'] = argv[count]
            else:
                print('Parameter not recognized: ' + argv[count])
                sys.exit()
            count += 1
    except ValueError:
        print('\n    ---    An error occurred\n')
        print('Check if the file containing your keys has the right format')
        print('Or if you entered an invalid value for some of the parameters')
        print('e.g. Using letters when using the --retweet option')
        print('     Using letters when using the --single option')
        print('     Using letters when using the --max-dups option')
        print()
        sys.exit()
    
        
    if not options['get_images'] and not options['get_videos']:
        print('\nNothing to download\n')

    try:
        print('')
        fetch_tweets(credentials, options)
        print('')
    except KeyboardInterrupt:
        print('Closing...\n')
        
    print('    Fetched ' + str(tweet_count) + ' tweets')
    print('    Saved ' + str(file_count) + ' images / gifs / videos')
    print('    Found ' + str(dups_count) + ' duplicate files')
    
    time.sleep(1)
    
if __name__== "__main__":
    main(sys.argv)