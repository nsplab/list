import json
import datetime
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.core.urlresolvers import reverse
from django.views import generic

from .models import *

class AjaxRequestMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404('request must be ajax')
        return super(AjaxRequestMixin, self).dispatch(request, *args)

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

class ListSearchView(JSONResponseMixin, generic.View):
    http_method_names = ['options','get']

    def get_queryset(self):
        filter_kwargs = dict(active=True, currentlyDraft=False) # automatic filters to be applied
        key = 'title'
        if key in self.request.GET:
            filter_kwargs['title__icontains'] = self.request.GET[key]
        topicid = None
        key = 'topic'
        if key in self.request.GET:
            topics = TopicTree.objects.filter(name__icontains=self.request.GET[key]).order_by('name')
            if topics.exists():
                topicid = topics[0].id
                if topicid:
                    if TopicTree.objects.isLeaf(topicid):
                        # topic is a leaf node
                        filter_kwargs['topic_id'] = topicid
                    else:
                        # match against topic and any of its descendants
                        topicids = TopicTree.objects.getDescendantIdsOnly(topicid)
                        topicids.append(topicid) # include itself
                        filter_kwargs['topic_id__in'] = topicids
        qset = List.objects.filter(**filter_kwargs).select_related('topic')
        qset = qset.order_by('-recordDate')
        return qset

    def get_context_data(self):
        """TODO: add pagination"""
        qset = self.object_list
        # for now, return the latest 10 results
        qset = qset[:10]
        # get values from queryset for the given fields
        fields = ('id','title','description','recordDate','topic_id','topic__name')
        # cast ValuesQuerySet to list before serializing
        lists = list(qset.values(*fields))
        if not lists:
            lists = {}
        context = {
            'lists': lists
        }
        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_json_response(context)


class IndexView(generic.TemplateView):
    template_name = 'lists/search.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['listSearchUrl'] = reverse('lists:search')
        return context

class ListDetailView(generic.DetailView):
    model = List
    template_name = 'lists/detail.html'
