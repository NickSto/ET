from django.conf.urls import url

from . import views

app_name = 'ET'
urlpatterns = [
  url(r'^(?P<type>.+)$', views.record, name='record'),
]
