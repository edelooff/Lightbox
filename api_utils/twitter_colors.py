#!/usr/bin/python
"""Lightbox JSON API Plugin which updates colors based on color name found
in Tweets that contain a certain hash tag.

This application interacts with the JSON API for Lightbox.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.2'

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
import color_names


class TwitterSearcher(threading.Thread):
  """Searches for tweets matching hashtags and dumps them on a queue."""
  def __init__(self, tweet_queue, hashtags):
    """Initializes the TwitterSearcher."""
    super(TwitterSearcher, self).__init__(name='TwitterSearcher')
    self.tweets = tweet_queue
    self.hashtags = hashtags
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
    for tweet in self.SearchResults():
      self.last_tweet = tweet['id']
      color, source = ColorFromMessage(tweet['text'])
      self.tweets.put((tweet['text'], color, source))

  def SearchResults(self):
    """Returns the result of our Twitter search query for the hash tags."""
    response = requests.get('http://search.twitter.com/search.json', params={
        'q': ' OR '.join('#%s' % tag for tag in self.hashtags),
        'since_id': self.last_tweet})
    return reversed(response.json()['results'])


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


def TwitterColors(host, port, hashtags, delay, layer):
  """Updated Lightbox outputs based on tweets posted on configured hashtags."""
  api_address = 'http://%s:%d' % (host, port)
  print 'Running Twitter search plugin for Lightbox API ...'
  print 'Hashtags we\'re searching: %s' % ', '.join(hashtags)
  tweet_queue = Queue.Queue()
  TwitterSearcher(tweet_queue, hashtags)
  for iteration in itertools.count():
    tweet, color, source = tweet_queue.get()
    print '\nNew color: [%s] (based on %s) (%d remaining)\nTWEET: %s' % (
        color, source, tweet_queue.qsize(), tweet)
    outputs = requests.get(api_address + '/api').json()['outputCount']
    command = {'output': iteration % outputs,
               'layer': layer,
               'color': color,
               'steps': 50}
    requests.post(api_address, data={'json': simplejson.dumps(command)})
    time.sleep(delay)


def main():
  """Processes commandline input to setup the API server."""
  import optparse
  parser = optparse.OptionParser()
  parser.add_option('--host', default='localhost',
                    help='Lightbox API server address (default localhost).')
  parser.add_option('--port', type='int', default=8000,
                    help='Lightbox API server port (default 8000).')
  parser.add_option('-l', '--layer', type='int', default=0,
                    help='Layer to target with color commands.')
  parser.add_option('-t', '--tag', action='append', dest='tags',
                    help='Hashtag to search for. Can be defined more than once')
  parser.add_option('-d', '--delay', type='int', default=5,
                    help='Minimum time between successive strip updates.')
  options, _arguments = parser.parse_args()
  TwitterColors(options.host, options.port,
                options.tags, options.delay, options.layer)


if __name__ == '__main__':
  main()
