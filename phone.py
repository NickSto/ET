#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import sys
import json
import errno
import string
import socket
import random
import logging
import httplib
import urlparse
import argparse

APP_PATH = '/ET'
INVOCATION_PATH = APP_PATH+'/start'
RUN_END_PATH = APP_PATH+'/run_end'
ALPHABET_DEFAULT = string.ascii_letters + string.digits + '+/'
RUN_ID_LEN = 24

ARG_DEFAULTS = {'domain':'nstoler.com', 'log':sys.stderr, 'volume':logging.ERROR}
DESCRIPTION = """"""


def make_argparser():

  parser = argparse.ArgumentParser(description=DESCRIPTION)
  parser.set_defaults(**ARG_DEFAULTS)

  parser.add_argument('-d', '--domain',
    help='')
  parser.add_argument('-l', '--log', type=argparse.FileType('w'),
    help='Print log messages to this file instead of to stderr. Warning: Will overwrite the file.')
  parser.add_argument('-q', '--quiet', dest='volume', action='store_const', const=logging.CRITICAL)
  parser.add_argument('-v', '--verbose', dest='volume', action='store_const', const=logging.INFO)
  parser.add_argument('-D', '--debug', dest='volume', action='store_const', const=logging.DEBUG)

  return parser


def main(argv):

  parser = make_argparser()
  args = parser.parse_args(argv[1:])

  logging.basicConfig(stream=args.log, level=args.volume, format='%(message)s')
  tone_down_logger()

  scheme, domain, path = split_url(args.url)

  if scheme != 'https':
    fail('URL must be https.')


def send_invocation(domain, project, script, version):
  data = {'project':project, 'script':script, 'version':version}
  run_id = make_blob(RUN_ID_LEN)
  data['run'] = {'id':run_id}
  data_json = json.dumps(data)
  send_data(domain, INVOCATION_PATH, data_json)
  return run_id


def send_run_end(domain, project, script, version, run_id, run_time, input_size):
  run_data = {'id':run_id, 'time':run_time, 'input_size':input_size}
  data = {'project':project, 'script':script, 'version':version, 'run':run_data}
  data_json = json.dumps(data)
  send_data(domain, RUN_END_PATH, data_json)


def send_data(domain, path, data):
  conex = httplib.HTTPSConnection(domain)
  try:
    conex.request('POST', path, data)
  except socket.gaierror:
    sys.stderr.write('Error requesting "https://{}{}"\n'.format(domain, path))
    raise
  response = conex.getresponse()
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
