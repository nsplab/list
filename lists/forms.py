from django.forms import Form, ModelForm

from .models import *

class ListCreateForm(ModelForm):
    class Meta:
        model = Article
        fields = ['topic','title','description']

class ListItemCreateForm(ModelForm):
    class Meta:
        model = ListItem
        fields = ['title','description','deepDive']
