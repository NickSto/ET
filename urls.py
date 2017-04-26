from django.conf.urls import url

from . import views

app_name = 'et'
urlpatterns = [
  url(r'^(?P<type>.+)$', views.record, name='record'),
]
