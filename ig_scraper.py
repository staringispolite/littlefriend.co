#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import codecs
import datetime
import json
import unicodecsv as csv
import urllib

# Format to match https://docs.google.com/spreadsheets/d/1EFz3YGFkkUY1_tb8oG2VcA2poO1Fiu8C4hP_ONQKX9U/edit#gid=0&fvid=345584700
COL_NAME = 0
COL_URL = 1
COL_CLASS = 2
COL_STATUS = 3
COL_DESCRIPTION = 4
COL_DIVIDER = 5
COL_SEARCH_URL = 6
COL_INSTAGRAM_COMPATIBLE = 7
COL_INSTAGRAM_HANDLE = 8

# Command line args
parser = argparse.ArgumentParser(description="Grab Instagram's public data for the given accounts")
parser.add_argument('-i', dest='csvFilename',
    help="The full path to a CSV with handles in the appropriate column")
parser.add_argument('-o', dest='outputFilename', default='output.csv',
    help="The full path to write CSV output to")
parser.add_argument('-v', dest='verbose', default=False,
    action="store_true", help="Print details as it goes")
args = parser.parse_args()

# Utility functions
def buildInstagramJSONURL(handle):
  return "https://www.instagram.com/%s/?__a=1" % handle

def getInstagramData(handle):
  """ Given a handle, get the JSON data for the profile, and return
  a json object
  """
  url = buildInstagramJSONURL(handle)
  if args.verbose:
    print "Getting JSON from %s" % url
  response = urllib.urlopen(url)
  data = json.loads(response.read())
  return data

def computeAvgPostingFrequency(nodes):
  """ Given the "user.media.nodes" array as parsed from json,
  compute the avg days between posts.
  Instagram stores post dates as linux timestamps (seconds from the epoch)
  """
  avg = "N/A"
  if len(nodes) > 1:
    # Start simple: time difference of all the posts they'll show us here / # posts
    total_posts = len(nodes)
    first_post_date = int(nodes[total_posts - 1]["date"]) 
    latest_post_date = int(nodes[0]["date"])
    total_days_posting = (latest_post_date - first_post_date) / 60 / 60 / 24
    avg = total_days_posting / total_posts
  return avg

# Import CSV data
instagram_data = []
with open(args.csvFilename, 'rb') as csvfile:
  reader = csv.reader(csvfile)
  # Discard the row of labels
  reader.next()
  # Grab the Instagram data for each
  for row in reader:
    handle = row[COL_INSTAGRAM_HANDLE]
    if handle is None or handle == "" or handle == "N/A":
      if args.verbose:
        print "Skipping %s. No valid handle found" % row[COL_NAME]
      instagram_data.append([row[COL_NAME], handle, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
    else:
      if args.verbose:
        print "pulling data for @%s" % handle
      jsonData = getInstagramData(handle)
      if args.verbose:
        print json.dumps(jsonData, indent=2, sort_keys=True)
      user = jsonData["user"]
      media = user["media"]
      media_count = int(media["count"])
      last_post_date = "N/A"
      last_post_likes = "N/A"
      if media_count > 0:
        last_post_date = media["nodes"][0]["date"]
        last_post_date = datetime.datetime.fromtimestamp(int(last_post_date)).strftime("%m/%d/%Y")
        last_post_likes = media["nodes"][0]["likes"]["count"]
      instagram_data.append([
          row[COL_NAME],
          handle,
          user["full_name"],
          user["biography"],
          user["followed_by"]["count"],
          user["follows"]["count"],
          media_count,
          last_post_date,
          last_post_likes,
          computeAvgPostingFrequency(media["nodes"])
      ])

# Output results to file
with open(args.outputFilename, 'wb') as f:
  csv_writer = csv.writer(f, encoding='utf-8')
  for co in instagram_data:
    if args.verbose:
      print co
    csv_writer.writerow(co)

