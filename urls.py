from django.conf.urls import url

from . import views

app_name = 'ET'
urlpatterns = [
  url(r'monitor', views.monitor, name='monitor'),
  url(r'runs', views.runs, name='runs'),
  url(r'^(?P<type>.+)$', views.record, name='record'),
]
