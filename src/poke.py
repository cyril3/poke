#!/usr/bin/env python3

import requests
from feeds import Feeds
import argparse
import feedparser
import time
import datetime
import os
import sys
import io
import logging

poke_path = None
feed_file = None
log_path = None
feeds = None

def fetch_feed(url):
    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        return None
    d = feedparser.parse(r.text)
    return d

# sub routine
def poke_sub(args):
    # get subscribed feeds
    f = feeds.get_feeds()
    # if already have the same feed with the new one, exit.
    if args.url in [r['rss'] for r in f]:
        print('\'%s\' has already been subscribed to.' % args.url)
        return
    print("Checking for %s..." % args.url)

    d = fetch_feed(args.url)
    if d is None:
        print('Subscribe failed.')
        return
    f.append({
        'rss': args.url,
        'title': d.feed.title,
        'update_time': int(time.mktime(d.feed.updated_parsed)),
        'link': d.feed.link,
        'description': d.feed.description,
        'poke_time': 0,
    })

    # the path to store the feed's download files
    feed_path = os.path.join(poke_path, d.feed.title)
    if not os.path.isdir(feed_path):
        os.makedirs(feed_path)

    feeds.set_feeds(f)
    feeds.save()
    print('Subscribe successfully!')
    print('Title:', d.feed.title)
    print('Update time:', int(time.mktime(d.feed.updated_parsed)))
    print('Link:', d.feed.link)
    print('Description:', d.feed.description)
    print()

# list routine
def poke_list(args):
    f = feeds.get_feeds()
    print("{0:<5}{1:<33}{2:<43}".format('No', 'title', 'description'))
    for i in range(len(f)):
        if len(f[i]['title']) > 30:
            f[i]['title'] = f[i]['title'][0:30]+'...'
        if len(f[i]['description']) > 40:
            f[i]['description'] = f[i]['description'][0:40]+'...'
        print("{0:<5}{1:<33}{2:<43}".format(
            i+1, f[i]['title'], f[i]['description']))

# unsub routine
def poke_unsub(args):
    f = feeds.get_feeds()
    index = int(args.index)
    del(f[index-1])
    feeds.set_feeds(f)
    feeds.save()
    print('Unsubscribed to podcast %d.' % index)

def update_feed(feed_body, feed):
    feed_title = feed['title']
    feed_path = os.path.join(poke_path, feed_title)
    poke_time = feed['poke_time']

    logging.info('%s: %d items are found.' % (feed_title, len(feed_body.entries)))
    feed_body.entries.sort(key=lambda entry: entry.published_parsed)

    for item in feed_body.entries:
        logging.info('%s: Processing item: %s' % (feed_title, item.title))
        publish_time = int(time.mktime(item.published_parsed))
        if publish_time <= poke_time:
            logging.debug('%s: Skip %s publish time: %d, poke time: %d' %
                (feed_title, item.title, publish_time, poke_time))
            continue
        poke_time = publish_time
        if item.enclosures[0].type != 'audio/mpeg' and item.enclosures[0].type != 'audio/mp3':
            logging.error('%s: Invalid file type: %s, skiped.' % (feed_title, item.enclosures[0].type))
            continue

        try:
            r = requests.get(item.enclosures[0].href)
        except Exception as e:
            logging.error('%s: exception. url: %s, message: %s' % (feed_title, item.enclosures[0].href, e))
            continue
        logging.info('%s: Download Complete: %s' % (feed_title, item.title))

        file_name = feed_title + time.strftime('-%Y-%m-%d %H-%M-%S', item.published_parsed)

        if not os.path.isdir(feed_path):
            os.makedirs(feed_path)
        with open(os.path.join(feed_path, file_name)+'.mp3', 'wb') as f:
            f.write(r.content)

        logging.info('%s: %s Complete.' % (feed_title, item.title))
    feed['poke_time'] = poke_time

# update routine
def poke_update(args):
    debug_level = logging.INFO
    if args.debug:
        debug_level = logging.DEBUG
    logging.basicConfig(level       =debug_level,
                        format      ="%(asctime)s %(name)s %(levelname)s %(message)s ",
                        datefmt     ='%Y-%m-%d %H:%M:%S ',
                        filename    = os.path.join(log_path, datetime.date.today().strftime("%Y-%m-%d") + '.log'),
                        )
    feed = feeds.get_feeds()
    while True:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(level       =debug_level,
                            format      ="%(asctime)s %(name)s %(levelname)s %(message)s ",
                            datefmt     ='%Y-%m-%d %H:%M:%S ',
                            filename    = os.path.join(log_path, datetime.date.today().strftime("%Y-%m-%d") + '.log'),
                            )
        logging.info('Poke update begin.')

        for f in feed:
            logging.info('%s: Updating' % f['title'])
            logging.info('%s: Fetching %s' % (f['title'], f['rss']))
            try:
                d = fetch_feed(f['rss'])
            except Exception as e:
                logging.error('%s: fetch feed failed. %s' % (f['title'], e))
                continue

            update_feed(d, f)
        feeds.set_feeds(feed)
        feeds.save()
        logging.info('Poke update ends.')
        time.sleep(21600)

if __name__ == "__main__":

    poke_path_env = os.getenv('POKE_PATH')
    if poke_path_env != None and poke_path_env != '':
        poke_path = os.getenv('POKE_PATH')
    else:
        poke_path = os.path.join(os.path.expanduser('~'), 'poke')
    feed_file = os.path.join(poke_path, '.feed')
    log_path = os.path.join(poke_path, 'logs')
    if not os.path.isdir(log_path):
        os.makedirs(log_path)

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

    feeds = Feeds(feed_file)
    feeds.load()
    parser = argparse.ArgumentParser(
        description='poke - A command line podcast client to subscribe and download podcasts."')
    subparsers = parser.add_subparsers()

    parse_sub = subparsers.add_parser('sub', help='Subscribe to a podcast.')
    parse_sub.add_argument('url', help='The url of the RSS source.')
    parse_sub.set_defaults(func=poke_sub)

    parse_list = subparsers.add_parser(
        'list', aliases=['ls'], help='List all channels subscribed.')
    parse_list.set_defaults(func=poke_list)

    parse_unsub = subparsers.add_parser(
        'unsub', aliases=['us'], help='Unsubscribe to a podcast.')
    parse_unsub.add_argument(
        'index', help='The index of the podcast to be unsubscribed.')
    parse_unsub.set_defaults(func=poke_unsub)

    parse_update = subparsers.add_parser(
        'update', aliases=['up'], help='Update postcasts.')
    parse_update.set_defaults(func=poke_update)

    parse_update.add_argument("--debug", action="store_true",
        help="run as debug mode.")

    args = parser.parse_args()

    args.func(args)
