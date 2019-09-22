
#!/usr/bin/env python3
import pymongo
import urllib.request
import logging
import os

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
myclient = pymongo.MongoClient("mongodb://db_0:27017/")

mydb = myclient["vimeo"]
mycol = mydb["videos"]

base_url = "https://player.vimeo.com/video/"

vid_start = int(os.environ["VIMEO_ID_START"])
vid_end = int(os.environ["VIMEO_ID_END"])
for vid in range(vid_start, vid_end):
    logging.info("Checking video {}!".format(vid))
    logging.info("{} videos to go!".format(vid-vid_end))

    try:
        htmltext = urllib.request.urlopen("{}{}".format(base_url, vid)).read().decode('utf-8')
        title = str(htmltext).split('<title>')[1].split('</title>')[0]

        if title == "Private Video on Vimeo":
            logging.debug("Skiping video: {} that is Private.".format(vid))
            continue

        data = { 
            "_id": vid, 
            "title": title, 
            "url": "{}{}".format(base_url, vid)
        }
        key = {"_id": vid}
        
        logging.debug("Updating entry {} on the DB.".format(key))
        mycol.update(key, data, upsert=True)

    except urllib.error.HTTPError as err:
        if err.code == 404:
            logging.debug("Skiping (404) Not Found: {}".format(vid))
            continue
        if err.code == 403:
            logging.debug("Skiping (403) Forbidden: {}".format(vid))
            continue
        else:
            raise