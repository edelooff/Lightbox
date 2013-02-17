#!/usr/bin/python
"""Lightbox JSON API Plugin which updates colors based on color name found
in Tweets that contain a certain hash tag.

This module uses the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.1'

# Standard modules
import itertools
import Queue
import random
import re
import requests
import simplejson
import threading
import time

# Custom modules
from frack.projects.lightbox import utils
import color_names

JSON_API = 'http://localhost:8000/'
HASHTAGS = 'mf050', 'maker', 'makerfaire', 'frack'


class TwitterSearcher(threading.Thread):
  """Searches for tweets matching HASHTAGS and dumps them on a queue."""
  def __init__(self, tweet_queue):
    """Initializes the TwitterSearcher."""
    super(TwitterSearcher, self).__init__(name='TwitterSearcher')
    self.tweets = tweet_queue
    self.last_tweet = 0
    # Daemonize and GO!
    self.daemon = True
    self.start()

  def run(self):
    """Run this until we die."""
    while True:
      # Checl for tweets, then wait a short while so Twitter doesn't ban us :)
      self.CheckNewTweets()
      time.sleep(6)

  def CheckNewTweets(self):
    """Checks for new tweets and dumps colors on the queue."""
    for tweet in TwitterSearch(self.last_tweet):
      self.last_tweet = tweet['id']
      color, source = ColorFromMessage(tweet['text'])
      self.tweets.put((tweet['text'], color, source))


def ColorFromMessage(string, color_mapping=None):
  """Returns the first color found in the string, or one based on its hash.

  This function will ALWAYS return a color, from one of three ways:
    1) If the message contains an HTML color
    2) The `color_mapping` is checked against all words in the string. If any of
       the words in the string are found in that mapping, the value for one of
       the matches is returned (decision by random.choice)
    3) If all else fails, a hash is generated from the message, which is then
       taken modulo 2^24, returning a 24-bit color value
  """
  if color_mapping is None:
    color_mapping = color_names.COLOR_NAMES
  # Attempt to find HTML color hash
  html_color = re.search('(#[0-9a-f]{6})', string, flags=re.I)
  if html_color:
    return html_color.group(1), 'html-color'
  # Search for color words in the string
  string = string.lower()
  color_words = set(color_mapping) & set(re.split('(\w+)', string))
  if color_words:
    return color_mapping[random.choice(list(color_words))], 'word'
  # Return a hash-based color
  return '#%06x' % (hash(string) % 2 ** 24), 'hash'


def RandomColors():
  """Generates a large amount of random colors to fade through initially."""
  colors = []
  for step in range(200):
    colors.append({'color': utils.RandomColor(saturate=True),
                   'channel': step % 5, 'steps': 5, 'opacity': 1})
  return colors

def TwitterSearch(since_id):
  """Returns the result of our Twitter search query for the hash tags."""
  response = requests.get('http://search.twitter.com/search.json', params={
      'q': ' OR '.join('#%s' % tag for tag in HASHTAGS),
      'since_id': since_id})
  return reversed(response.json['results'])


def main():
  """Starts the Twitter search plugin for Lightbox API."""
  print 'Cycling some colors to draw attention ...'
  requests.post(JSON_API, data={'json': simplejson.dumps(RandomColors())})
  print 'Running Twitter search plugin for Lightbox API ...'
  print 'Hashtags we\'re searching: %s' % ', '.join(HASHTAGS)
  tweet_queue = Queue.Queue()
  TwitterSearcher(tweet_queue)
  for iteration in itertools.count():
    tweet, color, source = tweet_queue.get()
    print '\nNew color: [%s] (based on %s) (%d remaining)\nTWEET: %s' % (
        color, source, tweet_queue.qsize(), tweet)
    requests.post(JSON_API, data={'json': simplejson.dumps({
        'color': utils.HexToRgb(color),
        'channel': iteration % 5,
        'steps': 50})})
    time.sleep(2)


if __name__ == '__main__':
  main()
