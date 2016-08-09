import json
import datetime
from elasticsearch import Elasticsearch
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .forms import *

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

def json_serial(obj):
    if isinstance(obj, datetime.datetime):
        # for consistency, and to save space, don't return microseconds
        date = obj.replace(microsecond=0)
        return date.isoformat()
    else:
        raise TypeError ("Type not serializable")

class JsonResponse(HttpResponse):
    def __init__(self, context, status_code, **response_kwargs):
        super(JsonResponse, self).__init__(
            content=json.dumps(context, default=json_serial),
            content_type='application/json',
            status=status_code,
            **response_kwargs
        )

class JSONResponseMixin(object):
    def render_to_json_response(self, context, status_code=200, **response_kwargs):
        return JsonResponse(
            context,
            status_code,
            **response_kwargs
        )

class IndexView(generic.TemplateView):
    template_name = 'lists/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context


class ListSearchView(JSONResponseMixin, generic.View):
    http_method_names = ['options','get']
    
    def get_queryset(self):
        client = settings.ES_CLIENT
        query = self.request.GET.get('term', '')
        resp = client.suggest(
            index=settings.INDEX_NAME,
            body={
                'name_complete': {
                    "text": query,
                    "completion": {
                        "field": 'name_complete',
                    }
                }
            }
        )
        options = resp['name_complete'][0]['options']
        data = json.dumps(
            [{'id': i['payload']['pk'], 'value': i['text']} for i in options]
        )
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)
    
    """
    def get_queryset(self):
        filter_kwargs = dict(active=True, status=List.PUBLISHED) # automatic filters to be applied
        key = 'title'
        if key in self.request.GET:
            filter_kwargs['title__icontains'] = self.request.GET[key]
        topicid = None
        key = 'topic'
        if key in self.request.GET:
            topics = TopicNode.objects.filter(name__iexact=self.request.GET[key]).order_by('name')
            if topics.exists():
                topicid = topics[0].id
                if topicid:
                    if TopicEdge.objects.isLeaf(topicid):
                        # topic is a leaf node
                        filter_kwargs['topic_id'] = topicid
                    else:
                        # match against topic and any of its descendants
                        topicids = TopicEdge.objects.getDescendantIdsOnly(topicid)
                        topicids.append(topicid) # include itself
                        filter_kwargs['topic_id__in'] = topicids
        qset = List.objects.filter(**filter_kwargs).select_related('topic')
        qset = qset.order_by('-dateCreated')
        return qset"""

    """def get_context_data(self):
        # TODO: add pagination
        qset = self.object_list
        # for now, return the latest 10 results
        ##qset = qset[:10]
        # get values from queryset for the given fields
        fields = ('id','title','description','dateCreated','topic_id','topic__name')
        # cast ValuesQuerySet to list before serializing
        lists = list(qset.values(*fields))
        context = {
            'lists': lists
        }
        return context"""

    """def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_json_response(context)"""
        
    def get(self, request, *args, **kwargs):
        return self.get_queryset()
        #return self.render_to_json_response(context)


@method_decorator(csrf_exempt, name='dispatch')
#@method_decorator(login_required, name='dispatch')
class ListCreateView(JSONResponseMixin, generic.View):
    http_method_names = ['post',]

    def calcItemFormPrefixes(self):
        prefixes = []
        userdata = self.request.POST.copy()
        for key in sorted(userdata):
            if key.startswith('item-') and key.endswith('title'):
                L = key.rsplit('-', 1) # ['item-j', 'title']
                prefixes.append(L[0])
        return prefixes

    def post(self, request, *args, **kwargs):
        user = User.objects.get(username='faria')
        listForm = ListCreateForm(request.POST)
        if listForm.is_valid():
            # save list
            self.list = listForm.save(commit=False)
            self.list.user = user
            self.list.save()
            # list items
            self.listItems = []
            prefixes = self.calcItemFormPrefixes()
            for px in prefixes:
                itemForm = ListItemCreateForm(request.POST, prefix=px)
                if itemForm.is_valid():
                    listItem = itemForm.save(commit=False)
                    listItem.list = self.list
                    listItem.save()
                    self.listItems.append(listItem)
            context = {
                'id': self.list.pk,
                'title': self.list.title,
                'description': self.list.description,
                'dateCreated': self.list.dateCreated,
                'topic_id': self.list.topic_id,
                'topic__name': self.list.topic.name
            }
            return self.render_to_json_response(context)
        else:
            print(listForm.errors)
            context = {
                'error_message': 'Invalid list data.'
            }
            return self.render_to_json_response(context, status_code=400)


class ListItemsView(JSONResponseMixin, generic.View):
    """Returns the items for a single List pk in url"""
    http_method_names = ['get',]

    def get_queryset(self):
        filter_kwargs = dict(active=True, list=self.pk)
        qset = ListItem.objects.filter(**filter_kwargs)
        return qset

    def get_context_data(self):
        qset = self.object_list
        fields = ('id','_order', 'title','description', 'deepDive', 'list_id','dateCreated','dateModified')
        items = list(qset.values(*fields))
        context = {
            'listItems': items
        }
        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_json_response(context)
