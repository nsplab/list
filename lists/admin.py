from django.contrib import admin
from .models import *

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 3

class ListAdmin(admin.ModelAdmin):
    list_display = ('topic', 'title', 'recordDate','active','currentlyDraft')
    list_filter = ['recordDate','active','currentlyDraft']
    search_fields = ['title',]
    fieldsets = [
        (None,               {'fields': ['title','description','topic','currentlyDraft','active']}),
        ('Date information', {'fields': ['recordDate','lastEditedDate'], 'classes': ['collapse']}),
    ]
    inlines = [ListItemInline]

admin.site.register(List, ListAdmin)
