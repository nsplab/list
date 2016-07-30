from django.contrib import admin
from .models import *

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 3

class ListAdmin(admin.ModelAdmin):
    list_display = ('status', 'topic', 'title', 'active','dateCreated')
    list_filter = ['active','status']
    search_fields = ['title',]
    fieldsets = [
        (None,               {'fields': ['title','description','topic','status','active']}),
        ('Date information', {'fields': ['dateCreated','dateModified'], 'classes': ['collapse']}),
    ]
    inlines = [ListItemInline]

admin.site.register(List, ListAdmin)
