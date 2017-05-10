from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from traffic.lib import add_and_get_visit
from .models import Event
import json


@add_and_get_visit
@csrf_exempt
def record(request, visit, type):
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
                visit=visit,
                project=project,
                script=script,
                version=version,
                platform=platform,
                test=test,
                run_id=run_id)
  if type == 'start':
    pass
  elif type == 'end':
    try:
      event.run_data = json.dumps(data['run'])
    except KeyError:
      return fail('Missing "run" key in POST data ("{}")'.format(str(request.body, 'utf8')))
  else:
    return fail('Unrecognized event type "{}"'.format(type))
  event.save()
  output = 'project:\t'+project+'\nscript:\t'+script+'\nversion:\t'+version+'\nrun_id:\t'+run_id+'\n'
  return HttpResponse(output, content_type='text/plain; charset=UTF-8')


def fail(message):
  return HttpResponseBadRequest('Error: '+message+'\n', content_type='text/plain; charset=UTF-8')


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
