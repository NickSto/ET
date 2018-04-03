from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import django.core.paginator
from myadmin.lib import require_admin_and_privacy
from traffic.ipinfo import set_timezone
from utils import QueryParams, boolish
from .models import Event
import collections
import json
import pytz
import logging
from datetime import datetime
log = logging.getLogger(__name__)

DEFAULT_PER_PAGE = 50


@csrf_exempt
def record(request, type):
  if not valid_content_type(request.content_type, request.content_params):
    return fail('Wrong Content-Type ("{}")'.format(request.META.get('CONTENT_TYPE')))
  data = json.loads(str(request.body, 'utf8'))
  try:
    project = data['project']
    script = data['script']
    version = data['version']
    run_id = data['run_id']
  except KeyError:
    return fail('Missing keys in POST data ("{}")'.format(str(request.body, 'utf8')))
  platform = data.get('platform') or ''
  test = data.get('test', False)
  event = Event(type=type,
                visit=request.visit,
                project=project,
                script=script,
                version=version,
                platform=platform,
                test=test,
                run_id=run_id)
  if type == 'start':
    pass
  elif type == 'end' or type == 'prelim':
    try:
      event.run_data = json.dumps(data['run'])
    except KeyError:
      return fail('Missing "run" key in POST data ("{}")'.format(str(request.body, 'utf8')))
  else:
    return fail('Unrecognized event type "{}"'.format(type))
  event.save()
  output = 'project:\t'+project+'\nscript:\t'+script+'\nversion:\t'+version+'\nrun_id:\t'+run_id+'\n'
  return HttpResponse(output, content_type='text/plain; charset=UTF-8')


def valid_content_type(content_type, content_params):
  if content_type != 'application/json':
    return False
  charset = content_params.get('charset')
  if charset is None:
    return False
  if charset.lower() == 'utf8' or charset.lower() == 'utf-8':
    return True
  else:
    return False


@require_admin_and_privacy
def monitor(request):
  # Get query parameters.
  params = QueryParams()
  params.add('p', default=1, type=int)
  params.add('perpage', default=DEFAULT_PER_PAGE, type=int)
  params.add('format', default='html')
  params.parse(request.GET)
  events = Event.objects.order_by('-id')
  pages = django.core.paginator.Paginator(events, params['perpage'])
  try:
    page = pages.page(params['p'])
  except django.core.paginator.EmptyPage:
    return HttpResponseRedirect(reverse('ET:monitor')+str(params.but_with(p=pages.num_pages)))
  if params['format'] == 'plain':
    events_strs = []
    for event in page:
      timestamp = event.visit.timestamp.timestamp()
      events_strs.append('{id}\t{0}\t{1}\t{type}\t{project}\t{script}\t{version}\t{platform}\t'
                         '{test}\t{run_id}\t{run_data}'
                         .format(timestamp, event.visit.visitor.ip, **vars(event)))
    return HttpResponse('\n'.join(events_strs), content_type='text/plain; charset=UTF-8')
  else:
    # Construct the navigation links.
    links = collections.OrderedDict()
    if page.has_previous():
      links['< Later'] = str(params.but_with(p=page.previous_page_number()))
    if page.has_next():
      links['Earlier >'] = str(params.but_with(p=page.next_page_number()))
    context = {'events':page, 'links':links, 'timezone':set_timezone(request)}
    return render(request, 'ET/monitor.tmpl', context)


@require_admin_and_privacy
def runs(request):
  params = QueryParams()
  params.add('p', default=1, type=int)
  params.add('perpage', default=DEFAULT_PER_PAGE, type=int)
  params.add('showtests', default=False, type=boolish)
  params.parse(request.GET)
  if params['p'] < 1:
    return HttpResponseRedirect(reverse('ET:runs')+str(params.but_with(p=1)))
  params.copy()
  # Get the runs for this page.
  runs_dict = get_runs(Event.objects.order_by('id'))
  runs = sorted(runs_dict.values(), reverse=True, key=lambda run: run['time'])
  if not params['showtests']:
    runs = [run for run in runs if not run['test']]
  pages = django.core.paginator.Paginator(runs, params['perpage'])
  try:
    page = pages.page(params['p'])
  except django.core.paginator.EmptyPage:
    return HttpResponseRedirect(reverse('ET:runs')+str(params.but_with(p=pages.num_pages)))
  # Construct the navigation links.
  links = collections.OrderedDict()
  if page.has_previous():
    links['< Later'] = str(params.but_with(p=page.previous_page_number()))
  if params['showtests']:
    links['Hide tests'] = str(params.but_with(showtests=None))
  else:
    links['Show tests'] = str(params.but_with(showtests='true'))
  if page.has_next():
    links['Earlier >'] = str(params.but_with(p=page.next_page_number()))
  context = {
    'runs':page,
    'links':links,
    'showtests':params['showtests'],
    'timezone':set_timezone(request)
  }
  return render(request, 'ET/runs.tmpl', context)


def get_runs(events):
  runs = {}
  now = datetime.now(tz=pytz.utc)
  for event in events:
    try:
      run = runs[event.run_id]
    except KeyError:
      run = {
        'time': event.visit.timestamp,
        'start_time': None,
        'end_time': None,
        'duration': None,
        'data': None,
        'finished': False,
        'failed': None,
        'awol': False,
        'exception': None,
        'project': event.project,
        'script': event.script,
        'version': event.version,
        'platform': event.platform,
        'test': event.test,
        'ip': event.visit.visitor.ip,
      }
      runs[event.run_id] = run
    if event.type == 'start':
      run['start_time'] = event.visit.timestamp
      run['time'] = event.visit.timestamp
    elif event.type == 'prelim' and run['data'] is None:
      run['data'] = event.run_data
    elif event.type == 'end':
      run['end_time'] = event.visit.timestamp
      if run['start_time']:
        delta = run['end_time'] - run['start_time']
        run['duration'] = str(delta).split('.')[0]
      run['data'] = event.run_data
      run['finished'] = True
      try:
        parsed_data = json.loads(event.run_data)
        if parsed_data:
          if parsed_data.get('failed'):
            run['failed'] = True
          run['exception'] = parsed_data.get('exception')
      except ValueError:
        log.info('ValueError when attempting to parse JSON {!r}.'.format(event.run_data))
  for run in runs.values():
    if not run['finished']:
      # For unfinished runs, "duration" is how long it's been running so far.
      delta = now - run['start_time']
      # If it's been running for 2 days or longer, count it as AWOL (probably failed).
      if delta.days > 1:
        run['awol'] = True
      run['duration'] = str(delta).split('.')[0]
  return runs


def fail(message):
  return HttpResponseBadRequest('Error: '+message+'\n', content_type='text/plain; charset=UTF-8')
