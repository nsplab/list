from django.conf.urls import url
from . import views

app_name = 'lists'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^search/$', views.ListSearchView.as_view(), name='search'),
    url(r'^(?P<pk>[0-9]+)/$', views.ListDetailView.as_view(), name='detail'),
]
