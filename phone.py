#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import sys
import ssl
import json
import errno
import string
import socket
import random
import logging
import httplib
import urlparse
import argparse

HEADERS = {'User-Agent':'ET phone home', 'Content-Type':'application/json; charset=utf-8'}
APP_PATH = '/ET'
START_PATH = APP_PATH+'/start'
END_PATH = APP_PATH+'/end'
ALPHABET_DEFAULT = string.ascii_letters + string.digits + '+/'
RUN_ID_LEN = 24

ARG_DEFAULTS = {'domain':'nstoler.com', 'project':'et', 'script':'phone.py', 'version':'0.0',
                'secure':True, 'log':sys.stderr, 'volume':logging.ERROR}
DESCRIPTION = """"""


def make_argparser():

  parser = argparse.ArgumentParser(description=DESCRIPTION)
  parser.set_defaults(**ARG_DEFAULTS)

  parser.add_argument('-d', '--domain')
  parser.add_argument('-p', '--project')
  parser.add_argument('-s', '--script')
  parser.add_argument('-v', '--version')
  parser.add_argument('-i', '--insecure', dest='secure', action='store_false',
    help='Don\'t check TLS certificates.')
  parser.add_argument('-l', '--log', type=argparse.FileType('w'),
    help='Print log messages to this file instead of to stderr. Warning: Will overwrite the file.')
  parser.add_argument('-q', '--quiet', dest='volume', action='store_const', const=logging.CRITICAL)
  parser.add_argument('-V', '--verbose', dest='volume', action='store_const', const=logging.INFO)
  parser.add_argument('-D', '--debug', dest='volume', action='store_const', const=logging.DEBUG)

  return parser


def main(argv):

  parser = make_argparser()
  args = parser.parse_args(argv[1:])

  logging.basicConfig(stream=args.log, level=args.volume, format='%(message)s')
  tone_down_logger()

  send_start(args.domain, args.project, args.script, args.version, secure=args.secure)


def send_start(domain, project, script, version, secure=True):
  data = {'project':project, 'script':script, 'version':version}
  run_id = make_blob(RUN_ID_LEN)
  data['run'] = {'id':run_id}
  data_json = json.dumps(data)
  send_data(domain, START_PATH, data_json, secure=secure)
  return run_id


def send_end(domain, project, script, version, run_id, run_time, input_size, secure=True):
  run_data = {'id':run_id, 'time':run_time, 'input_size':input_size}
  data = {'project':project, 'script':script, 'version':version, 'run':run_data}
  data_json = json.dumps(data)
  send_data(domain, END_PATH, data_json, secure=secure)


def send_data(domain, path, data, secure=True):
  if secure:
    conex = httplib.HTTPSConnection(domain)
  else:
    context = ssl._create_unverified_context()
    conex = httplib.HTTPSConnection(domain, context=context)
  logging.info('Sending to https://{}{}:\n{}'.format(domain, path, data))
  try:
    conex.request('POST', path, data, HEADERS)
  except socket.gaierror:
    sys.stderr.write('Error requesting "https://{}{}"\n'.format(domain, path))
    raise
  response = conex.getresponse()
  logging.info('HTTP response {}'.format(response.status))
  logging.info(response.read())
  if response.status != 200:
    fail('Sending data failed: HTTP response {}.'.format(response.status))
  else:
    return True


def split_url(url):
  # parse the URL's components
  scheme, domain, path, query_str, frag = urlparse.urlsplit(url)
  if path == '':
    path = '/'
  if query_str:
    path += '?'+query_str
  return scheme, domain, path


def make_blob(length, alphabet=ALPHABET_DEFAULT):
  chars = [random.choice(alphabet) for i in range(length)]
  return ''.join(chars)


def tone_down_logger():
  """Change the logging level names from all-caps to capitalized lowercase.
  E.g. "WARNING" -> "Warning" (turn down the volume a bit in your log files)"""
  for level in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG):
    level_name = logging.getLevelName(level)
    logging.addLevelName(level, level_name.capitalize())


def fail(message):
  logging.critical(message)
  if __name__ == '__main__':
    sys.exit(1)
  else:
    raise Exception('Unrecoverable error')


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except IOError as ioe:
    if ioe.errno != errno.EPIPE:
      raise
