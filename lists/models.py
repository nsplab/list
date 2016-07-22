from __future__ import unicode_literals

import datetime
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

class TopicTreeManager(models.Manager):
    def isRoot(self, topic_id):
        qset = super(TopicTreeManager, self).get_queryset().filter(parent=None, pk=topic_id)
        return qset.exists()

    def isParent(self, topic_id):
        qset = super(TopicTreeManager, self).get_queryset().filter(parent=topic_id)
        return qset.exists()

    def isLeaf(self, topic_id):
        return not self.isParent(topic_id)

    def getAncestors(self, topic_id):
        """Calls database stored function"""
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM get_topic_ancestors(%s)", [topic_id])
        results = []
        for row in cursor.fetchall():
            results.append({'id': row[0], 'name': row[1]})
        return results

    def getDescendants(self, topic_id):
        """Calls database stored function"""
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT level, id, name, path FROM get_topic_descendants(%s)", [topic_id])
        results = []
        for row in cursor.fetchall():
            results.append({'level': row[0], 'id': row[1], 'name': row[2], 'path': row[3]})
        return results

    def getDescendantIdsOnly(self, topic_id):
        """Calls database stored function"""
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM get_topic_descendants(%s)", [topic_id])
        results = [row[0] for row in cursor.fetchall()]
        return results

# TopicTree - A node in a tree hierarchy of topics.
#   - parent: the ID of the parent of the current node, another row in TopicTree table
#   - ancestors: an array of ID's of ancestors of the current node
#   - name: text describing the topic of this node
#   - data: a longer explanation of the topic of this node
#   - recordDate: the date and time at which this node was created
# Ex: endocrinology, thyroid diseases, adrenal diseases, etc
@python_2_unicode_compatible
class TopicTree(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True)
    ancestors = ArrayField(base_field=models.PositiveIntegerField())
    name = models.CharField(max_length=100)
    data= models.TextField()
    recordDate = models.DateTimeField()
    # custom Manager to add extra class-level methods
    objects = TopicTreeManager()

    def __str__(self):
        return self.name

    

# List - A list of items.
#   - title: the visible top-level text describing the list
#   - description: a short textual description of the list
#   - topic: the ID of the TopicTree node to which this list is associated
#   - currentlyDraft: 
#   - active: 
#   - lastEditedDate: the date and time at which the title/description of the
#     list was last edited
#   - recordDate: the date at which the list was created
@python_2_unicode_compatible
class List(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)
    topic = models.ForeignKey(TopicTree)
    currentlyDraft = models.BooleanField()
    active = models.BooleanField()
    lastEditedDate = models.DateTimeField()
    recordDate = models.DateTimeField()

    def __str__(self):
        return self.title

# ListItem - A single item in a checklist. All items belonging to the same list
#            have a defined order in that list, which can be accessed and set
#            with l.get_listitem_order() and l.set_listitem_order() where l is
#            a list.
#   - title: the visible top-level text describing the item
#   - description: a short textual description of the item visible if you click
#     on the item's title
#   - deepDive: an unbounded-length description of the item accessible from the
#     shorter description
#   - active: 
#   - lastEditedDate: the date and time at which the item was last edited
#   - recordDate: the date and time at which the item was created
#   - list: the ID of the list to which this item is associated
@python_2_unicode_compatible
class ListItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    deepDive = models.TextField(blank=True)
    active = models.BooleanField()
    lastEditedDate = models.DateTimeField()
    recordDate = models.DateTimeField()
    list = models.ForeignKey(List)

    class Meta:
        order_with_respect_to = 'list'

    def __str__(self):
        return self.title

# SubscriberGroup - A group of subscribers. This could either be a singleton
#                   group or a group corresponding to some organization that
#                   might purchase a bulk subscription.
#   - name: a text field describing the name of the group
#   - recordDate: the date and time at which this group was created
@python_2_unicode_compatible
class SubscriberGroup(models.Model):
    name = models.CharField(max_length=100)
    recordDate = models.DateTimeField()

    def __str__(self):
        return self.name

# Person - A user of our service. Effectively extends the User model.
#   - user: the ID of the User to which this Person is associated
#   - friends: the set of Persons that this Person is friends with, encoded as
#     a relation
#   - favoriteLists: the set of lists (encoded as List IDs) that are in this
#     Person's favorites.
#   - recordDate: the date and time at which this person was created
#   - degrees: a text field describing the degrees held by this person
#   - jobTitle: a text field describing the person's current job title
#   - groups: the set of groups (encoded as SubscriberGroup IDs) to which this
#     person belongs
#   - personalDescription: a text field allowing a person to describe themselves
@python_2_unicode_compatible
class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    friends = models.ManyToManyField('self')
    favoriteLists = models.ManyToManyField(List, blank=True,
        related_name='favorites')
    recordDate = models.DateTimeField()
    degrees = models.CharField(max_length=100, blank=True)
    jobTitle = models.CharField(max_length=100, blank=True)
    groups = models.ManyToManyField(SubscriberGroup, blank=True)
    personalDescription = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

# Subscription - Something that grants access to a given topic and all subtopics
#                of that topic to a particular subscriber group for a certain
#                period of time.
#   - group: the ID of the SubscriberGroup to which this subscription is
#     associated
#   - recordDate: the date and time at which this subscription began
#   - expirationDate: the date and time at which this subscription ends
#   - topic: the topic (as a TopicTree ID) to which this subscription is
#     associated
#   - active: a Boolean indicating whether this subscription is currently active
#   - editPower: a Boolean indicating whether this subscription grants editing
#     privileges to the users in the subscriber group
#   - price: the price in USD that was paid for this subscription
class Subscription(models.Model):
    group = models.ForeignKey(SubscriberGroup)
    recordDate = models.DateTimeField()
    expirationDate = models.DateTimeField()
    topic = models.ForeignKey(TopicTree)
    active = models.BooleanField(default=True)
    editPower = models.BooleanField(default=False)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=10)
