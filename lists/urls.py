from django.conf.urls import url
from . import views

app_name = 'listapp'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^list/search/$', views.ListSearchView.as_view(), name='list-search'),
    url(r'^list/(?P<pk>[0-9]+)/create/$', views.ListCreateView.as_view(), name='list-create'),
    url(r'^list/(?P<pk>[0-9]+)/items/$', views.ListItemsView.as_view(), name='list-items'),
]
