from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from myadmin.lib import require_admin_and_privacy
from .models import Event
import json
import logging
log = logging.getLogger(__name__)


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
  DEFAULT_PER_PAGE = 50
  # Get query parameters.
  params = request.GET
  page = int(params.get('p', 1))
  per_page = int(params.get('per_page', DEFAULT_PER_PAGE))
  format = params.get('format', 'html')
  total_events = Event.objects.count()
  start = per_page*(page-1)
  end = per_page*page
  events = Event.objects.order_by('-id')[start:end]
  if format == 'plain':
    events_strs = []
    for event in events:
      timestamp = event.visit.timestamp.timestamp()
      events_strs.append('{id}\t{0}\t{1}\t{type}\t{project}\t{script}\t{version}\t{platform}\t'
                         '{test}\t{run_id}\t{run_data}'
                         .format(timestamp, event.visit.visitor.ip, **vars(event)))
    return HttpResponse('\n'.join(events_strs), content_type='text/plain; charset=UTF-8')
  else:
    context = {'events':events}
    if start == 0 and end >= total_events:
      context['start'] = None
      context['end'] = None
    else:
      context['start'] = max(1, total_events-end+1)
      context['end'] = total_events-start
    if page > 1:
      context['prev'] = page-1
    if end < total_events:
      context['next'] = page+1
    return render(request, 'ET/monitor.tmpl', context)


@require_admin_and_privacy
def runs(request):
  params = request.GET
  show = params.get('show')
  show_tests = show is not None and show.startswith('test')
  runs_dict = get_runs(Event.objects.order_by('id'))
  runs = sorted(runs_dict.values(), reverse=True, key=lambda run: run['time'])
  if not show_tests:
    runs = [run for run in runs if not run['test']]
  return render(request, 'ET/runs.tmpl', {'runs':runs, 'show_tests':show_tests})


def get_runs(events):
  runs = {}
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
        'failed': True,
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
      run['failed'] = False
  return runs


def fail(message):
  return HttpResponseBadRequest('Error: '+message+'\n', content_type='text/plain; charset=UTF-8')
