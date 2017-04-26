from django.db import models
from django.utils import timezone
from utils import ModelMixin

class Event(ModelMixin, models.Model):
  type = models.CharField(max_length=200)
  timestamp = models.DateTimeField(default=timezone.now)
  project = models.CharField(max_length=200)
  script = models.CharField(max_length=200)
  version = models.CharField(max_length=200)
  run_id = models.CharField(max_length=32)
  run_data = models.TextField()
