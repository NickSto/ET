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

DEFAULT_DOMAIN = 'nstoler.com'
DEFAULT_SECURE = True
APP_PATH = '/ET'
START_PATH = APP_PATH+'/start'
END_PATH = APP_PATH+'/end'
HEADERS = {'User-Agent':'ET phone home', 'Content-Type':'application/json; charset=utf-8'}
ALPHABET_DEFAULT = string.ascii_letters + string.digits + '+/'
RUN_ID_LEN = 24

ARG_DEFAULTS = {'domain':DEFAULT_DOMAIN, 'project':'ET', 'script':'phone.py', 'version':'0.0',
                'run_data':'{}', 'secure':DEFAULT_SECURE, 'test':False, 'log':sys.stderr,
                'volume':logging.ERROR}
DESCRIPTION = """"""


def make_argparser():

  parser = argparse.ArgumentParser(description=DESCRIPTION)
  parser.set_defaults(**ARG_DEFAULTS)

  parser.add_argument('event_type', choices=('start', 'end'))
  parser.add_argument('-d', '--domain',
    help='Default: %(default)s')
  parser.add_argument('-p', '--project',
    help='Default: %(default)s')
  parser.add_argument('-s', '--script',
    help='Default: %(default)s')
  parser.add_argument('-v', '--version',
    help='Default: %(default)s')
  parser.add_argument('-i', '--run-id',
    help='The run id generated by send_start().')
  parser.add_argument('-t', '--run-time', type=int,
    help='The run time, in seconds.')
  parser.add_argument('-r', '--run-data',
    help='Tool-specific data about the run, like input size, in JSON format.')
  parser.add_argument('-T', '--test', action='store_true',
    help='Mark this run as a test.')
  parser.add_argument('-S', '--secure', action='store_true',
    help='Enforce checking TLS certificates.')
  parser.add_argument('-I', '--insecure', dest='secure', action='store_false',
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

  if args.event_type == 'start':
    print(send_start(args.project,
                     args.script,
                     args.version,
                     domain=args.domain,
                     secure=args.secure,
                     test=args.test))
  elif args.event_type == 'end':
    if not (args.run_id and args.run_time):
      fail('--run-id and --run-time and required for event_type "end".')
    try:
      run_data = json.loads(args.run_data)
    except ValueError:
      fail('Invalid --run-data. Must be valid JSON. Saw: "{}"'.format(args.run_data))
    send_end(args.project,
             args.script,
             args.version,
             args.run_id,
             args.run_time,
             run_data,
             domain=args.domain,
             secure=args.secure,
             test=args.test)


def send_start(project,
               script,
               version,
               domain=DEFAULT_DOMAIN,
               secure=DEFAULT_SECURE,
               test=False):
  data = {'project':project, 'script':script, 'version':version, 'test':test}
  run_id = make_blob(RUN_ID_LEN)
  data['run'] = {'id':run_id}
  data_json = json.dumps(data)
  send_data(domain, START_PATH, data_json, secure=secure)
  return run_id


def send_end(project,
             script,
             version,
             run_id,
             run_time,
             optional_run_data={},
             domain=DEFAULT_DOMAIN,
             secure=DEFAULT_SECURE,
             test=False):
  """Send data about the end of a run."""
  run_data = {'id':run_id, 'time':run_time}
  run_data.update(optional_run_data)
  data = {'project':project, 'script':script, 'version':version, 'test':test, 'run':run_data}
  data_json = json.dumps(data)
  send_data(domain, END_PATH, data_json, secure=secure)


def send_data(domain, path, data, secure=DEFAULT_SECURE):
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
    raise Exception(message)


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except IOError as ioe:
    if ioe.errno != errno.EPIPE:
      raise
