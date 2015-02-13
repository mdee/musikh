# -*- coding: utf-8 -*-
import logging
import re
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import datetime
import math
from pyshorteners.shorteners import Shortener

__author__ = 'MDee'

import os
import sys

try:
    logger = logging.getLogger(__name__)
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    SONG_FORMAT = 'mp3'
    S3_ACCESS_KEY_ID = os.environ['S3_ACCESS_KEY_ID'].strip()
    S3_SECRET_ACCESS_KEY = os.environ['S3_SECRET_ACCESS_KEY'].strip()
    MUSIC_BUCKET = os.environ['MUSIC_BUCKET']
    S3_HOST = 's3-us-west-1.amazonaws.com'
    END_MSG = 'Try running again with another title.'
except KeyError:
    print '\nLooks like you\'re missing some required environment variables.'
    print 'You need to specify the keys for your S3 account and the bucket name.\n'
    exit()


def percent_cb(complete, total):
    print '\t{0}% complete'.format(math.floor((float(complete) / float(total)) * 100))


def match_song_title(title, dirname, filenames):
    title_regex = r'^.*{0}.*\.{1}$'.format(title, SONG_FORMAT)
    title_matches = []
    for f in filenames:
        if re.match(title_regex, f, re.IGNORECASE):
            title_matches.append({'title': f, 'path': '{0}/{1}'.format(dirname, f)})
    return title_matches


def read_command_line_args(args):
    arg_regex = r'^--.*'
    arg_map = {}
    arg_key = None
    for a in args:
        if not re.match(arg_regex, a):
            arg_map[arg_key].append(a)
        else:
            arg_key = a[2:]
            arg_map[arg_key] = []
    return {k: ' '.join(v) for k, v in arg_map.iteritems()}


def main():
    song_format_regex = r'^.*\.' + SONG_FORMAT + r'$'
    args = read_command_line_args(sys.argv[1:])
    print '\nSearching for song title matching \'{0}\''.format(args['title'])
    matches = []
    if len(args.keys()) == 1:
        music_path = os.environ['MUSIC']
    else:
        music_path = args['path']
    for (dir, _, files) in os.walk(music_path):
        if filter(lambda f: re.match(song_format_regex, f, re.IGNORECASE), files):
            matches += match_song_title(args['title'], dir, files)
    if len(matches) == 1:
        match = matches[0]
        print 'Found exactly one match: {0}\n\t{1}'.format(match['title'], match['path'])
        confirm = raw_input('\nIs this right? (y or n) ')
        if confirm == 'y':
            upload_to_s3(match)
        else:
            print 'Well, shit. {0}'.format(END_MSG)
    elif len(matches) > 0:
        print 'More than one match was found, time to pick (Enter 0 to cancel):\n'
        for i, m in enumerate(matches):
            print '\t{0}) {1}\n\t\t{2}'.format(i + 1, m['title'], m['path'])
        choice = int(raw_input('\nPick one to upload: '))
        if choice == 0:
            print 'Ok then. {0}'.format(END_MSG)
        else:
            match = matches[choice-1]
            upload_to_s3(match)
    else:
        print 'No matches found. {0}'.format(END_MSG)


def upload_to_s3(file_dict):
    """"""
    filename = file_dict['title']
    filepath = file_dict['path']
    conn = S3Connection(S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, host=S3_HOST)
    bucket = conn.get_bucket(MUSIC_BUCKET)
    k = Key(bucket)
    today = datetime.datetime.now()
    f = open(filepath, 'r+')
    sys.stdout.flush()
    url_path = '{0}/{1}/{2}/{3}'.format(today.year, today.month, today.day, re.sub(r'\s', '+', filename))
    k.key = url_path
    print('Uploading \'{0}\''.format(filename))
    k.set_contents_from_file(f, cb=percent_cb, num_cb=10)
    print('All done uploading!')
    url = 'https://{0}/{1}/{2}'.format(S3_HOST, MUSIC_BUCKET, url_path)
    shortener = Shortener('GoogleShortener')
    print '\nShareable URL: {0}'.format(shortener.short(url))

if __name__ == '__main__':
    main()
