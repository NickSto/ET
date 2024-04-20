from django.urls import re_path

from . import views

app_name = 'ET'
urlpatterns = [
  re_path(r'monitor', views.monitor, name='monitor'),
  re_path(r'runs', views.runs, name='runs'),
  re_path(r'^(?P<type>.+)$', views.record, name='record'),
]
