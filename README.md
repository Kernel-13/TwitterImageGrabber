# TwitterImageGrabber

Work in progress

```
Usage:
    TwitterImageGrabber.py --keys <credentials_file> --user-timeline <user> [--no-retweets] [--no-replies] [--max-dups N] [--no-video] [--no-image] [--no-dups]
    TwitterImageGrabber.py --keys <credentials_file> --my-timeline [--no-replies] [--max-dups N] [--no-video] [--no-image] [--no-dups]
    TwitterImageGrabber.py --keys <credentials_file> --single <id_to_download>
    TwitterImageGrabber.py --keys <credentials_file> --retweet <id_to_retweet>
    TwitterImageGrabber.py --keys <credentials_file> --search <#hashtag>
    TwitterImageGrabber.py -h

Options:
    -h, --help                         Shows this screen
    -k, --keys <credentials_file>      Specifies the JSON file containing your API keys
    -mtl, --my_timeline                Downloads media (800 tweets max.) from YOUR account (the account associated with the Access Token you provided)
    -mxd, --max_dups <N>               Stops the download after it finds more than N duplicate files.
    -nd, --no-dups                     Exits the script after finding the first duplicate image
    -nimg, --no-image                  Prevents images from being downloaded (Only gif/videos will be downloaded)
    -nrp, --no-replies                 Prevents replies from being downloaded
    -nrt, --no-retweets                Prevents retweets from being downloaded
    -nvid, --no-video                  Prevents videos/gif from being downloaded
    -rt, --retweet <id_to_retweet>     Retweets the specified tweet
    -s, --single <id_to_download>      Downloads media from a single tweet.
    --search <#hashtag or word>        Downloads media from tweets that include the specified #hashtag / word.
    -utl, --user-timeline <user_name>  Downloads media from the specified user (Up to 3200 tweets)

Examples:
    TwitterImageGrabber.py -k my_keys.json -utl SenbaRambu --no-replies -mxd 50 --no-video
    TwitterImageGrabber.py -k my_keys.json -mtl --no-image
    TwitterImageGrabber.py -k my_keys.json --s 983792855834603520
    TwitterImageGrabber.py --keys my_keys.json --user-timeline SenbaRambu -nrp -nvid
    TwitterImageGrabber.py --keys my_keys.json --my-timeline --max_dups 75
    TwitterImageGrabber.py --keys my_keys.json --retweet 983792855834603520
    TwitterImageGrabber.py --keys my_keys.json --search #hl3
```
