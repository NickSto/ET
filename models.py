from django.db import models
from utils import ModelMixin

class Event(ModelMixin, models.Model):
  type = models.CharField(max_length=200)
  visit = models.OneToOneField('traffic.Visit', models.SET_NULL, null=True, blank=True)
  project = models.CharField(max_length=200)
  script = models.CharField(max_length=200)
  version = models.CharField(max_length=200)
  run_id = models.CharField(max_length=32)
  platform = models.CharField(max_length=127)
  test = models.BooleanField(default=False)
  run_data = models.TextField()
