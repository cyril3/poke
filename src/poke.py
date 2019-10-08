import requests
from feeds import Feeds
from hurry.filesize import size as husize
import argparse
import feedparser
import time
import os
import sys
import io
import config
import configparser

feed_file = '.feed'
feeds = None
conf = config.Config()
# fetch feed and parse it using feedparser


def fetch_feed(url):
    try:
        r = requests.get(url, timeout=5)
    except Exception as e:
        print(e)
        return None
    if r.status_code != 200:
        print("Error: status code %d." % r.status_code)
        return None
    print("%s done." % husize(len(r.content)))

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
    })
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

# update routine


def poke_update(args):
    f = feeds.get_feeds()
    # for every feed
    for feed in f:
        # the path to store the feed's download files
        feed_path = os.path.join(conf.feed_path, feed['title'])
        if not os.path.isdir(feed_path):
            os.mkdir(feed_path)

        print('Updating \'%s\'...' % feed['title'])
        print('Fetching feed \'%s\'... ' % feed['rss'], end='', flush=True)
        d = fetch_feed(feed['rss'])
        if d is None:
            print('Get feed failed, skiped.')
            continue
        print('%d items are found.' % len(d.entries))
        # for every items of this feed
        for item in d.entries:
            print('Fetching \'%s\'...' % item.title)
            # an item will be renamed to 'feed title + time', because some of podcast's item title can't be used to name a file
            file_name = feed['title'] + \
                time.strftime('-%Y-%m-%d %H-%M-%S', item.published_parsed)
            if os.path.exists(os.path.join(feed_path, file_name)+'.txt'):
                print('Already downloaded, skiped.')
                continue
            # for now we only support audio/mpeg and audio/mp3, we will deal with other types later.
            if item.enclosures[0].type != 'audio/mpeg' and \
                    item.enclosures[0].type != 'audio/mp3':
                print('Invalid file type: %s, skiped.' %
                      item.enclosures[0].type)
                continue
            # create an mp3 file for writing
            with open(os.path.join(feed_path, file_name)+'.mp3', 'wb') as f:
                try:
                    with requests.get(item.enclosures[0].href, stream=True, timeout=5) as r:
                        # get file length from response header
                        total_length = r.headers.get('content-length')
                        dl = 0  # how many bytes have been recieved
                        done = 0  # how many '='s should be shown in the progress bar
                        if total_length is None:
                            print('Unknown file size.')
                            print('Downloading \'%s\'...' % item.title)
                            for chunk in r.iter_content(chunk_size=4096):
                                dl += len(chunk)
                                f.write(chunk)
                                print('\r{1:<10} recieved'.format(
                                    husize(dl), end=''))
                        else:
                            print('Downloading \'%s\'...' % item.title)
                            print('\r[{0:<50}]'.format('='*done), end='')
                            total_length = int(total_length)
                            for chunk in r.iter_content(chunk_size=4096):
                                dl += len(chunk)
                                f.write(chunk)
                                done = int(50 * dl / total_length)
                                print('\r[{0:<50}] {1}/{2:<10}'.format('='*done,
                                                                       husize(dl), husize(total_length)), end='')
                except Exception as e:
                    print(e)
                    break
            print()
            print('Complete.')
            # after download completely create a txt file the same name with the media file.
            # check this file before the next time updating this item, we shall know if there is need to download it.
            with open(os.path.join(feed_path, file_name)+'.txt', 'w') as f:
                config = configparser.ConfigParser(interpolation=None)
                config['item'] = {
                    'title': item.title,
                    'description': item.description,
                    'link': item.link,
                    'published': item.published,
                    'file': item.enclosures[0]['href'],
                }
                config.write(f)


if __name__ == "__main__":

    conf.load()

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

    args = parser.parse_args()

    args.func(args)
