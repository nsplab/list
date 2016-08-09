from __future__ import unicode_literals

import datetime
import django
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

django.db.models.options.DEFAULT_NAMES += (
    'es_index_name', 'es_type_name', 'es_mapping'
)


@python_2_unicode_compatible
class TopicNode(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.name
        
    class Meta:
        es_index_name = settings.INDEX_NAME
        es_type_name = 'topicnode'
        es_mapping = {
            'properties': {
                'name': {'type': 'string', 'index': 'analyzed'},
                'description': {'type': 'string', 'index': 'analyzed'},
                'dateCreated': {'type': 'date'},
                'dateModified': {'type': 'date'},
                'name_complete': {
                    'type': 'completion',
                    'analyzer': 'simple',
                    'payloads': True,
                    'preserve_separators': True,
                    'preserve_position_increments': True,
                    'max_input_length': 30,
                }
            }
        }
        
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.pk
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
        
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value
        
    def get_es_name_complete(self):
        return {"input": [self.name], 'payload': {"pk": self.pk}}

class TopicEdgeManager(models.Manager):
    def isParent(self, topic_id):
        qset = super(TopicEdgeManager, self).get_queryset().filter(parent=topic_id)
        return qset.exists()

    def isChild(self, topic_id):
        qset = super(TopicEdgeManager, self).get_queryset().filter(child=topic_id)
        return qset.exists()

    def isLeaf(self, topic_id):
        return self.isChild(topic_id) and not self.isParent(topic_id)

    def isRoot(self, topic_id):
        return self.isParent(topic_id) and not self.isChild(topic_id)

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
        cursor.execute("SELECT DISTINCT id FROM get_topic_descendants(%s)", [topic_id])
        results = [row[0] for row in cursor.fetchall()]
        return results

    def isAncestorOf(self, ancestor_id, child_id):
        """Calls database stored function"""
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM get_topic_descendants_until(%s,%s)", [ancestor_id, child_id])
        cursor.fetchall() # cursor.rowcount is updated after the fetch
        return cursor.rowcount == 0

@python_2_unicode_compatible
class TopicEdge(models.Model):
    parent = models.ForeignKey(TopicNode, related_name='parent_set', db_index=True)
    child = models.ForeignKey(TopicNode, related_name='child_set', db_index=True)
    description = models.CharField(max_length=100)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)
    # custom Manager to add extra table-level methods
    objects = TopicEdgeManager()

    class Meta:
        unique_together = ('parent', 'child')

    def __str__(self):
        return self.parent.name + ':' + self.child.name

    def clean(self):
        if self.parent.pk == self.child.pk:
            raise ValidationError({
                'child': _('A topic node may not be connected to itself.')})


# List - A list of items.
#   - title: the visible top-level text describing the list
#   - description: a short textual description of the list
#   - topic: the TopicNode to which this list belongs
#   - active: if False, the list is obsolete
#   - status: one of Draft/Submitted/Published.
#   - creator: User who created the list
#   - lockUser: User who locks the list for edits.
#   - parentList: the List ID that was cloned to create a new list
#   - version: version number
#   - dateCreated: timestamp of row creation
#   - dateModified: timestamp of when the row was last modified

# Rules
# When list is in DRAFT status: only the creator may view/edit it. Creator can change status to SUBMITTED.
# When list is in SUBMITTED status:
#   - An editor assigned to the list topic may view it and claim it for review (set lockUser to editor userid).
#   - The editor may (1) release the lock (reset lockUser to null).
#   - If lockUser is null, the creator may return it to DRAFT mode to make it private again, and make any changes as needed.
#   - The editor may (2) publish the list (set status = PUBLISHED). At this point, no further edits are allowed. User may clone the list, and upgrade the version.
@python_2_unicode_compatible
class List(models.Model):
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    PUBLISHED = 'PUBLISHED'
    STATUS_CHOICES = (
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted for review'),
        (PUBLISHED, 'Published')
    )

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)
    topic = models.ForeignKey(TopicNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True
    )
    active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=DRAFT
    )
    creator = models.ForeignKey(User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name='list_creators'
    )
    lockUser = models.ForeignKey(User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name='lock_users'
    )
    parentList = models.ForeignKey('self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_index=True
    )
    version = models.IntegerField(default=1)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.title
        
    class Meta:
        es_index_name = settings.INDEX_NAME
        es_type_name = 'list'
        es_mapping = {
            'properties': {
                'title': {'type': 'string', 'index': 'analyzed'},
                'description': {'type': 'string', 'index': 'analyzed'},
                'topic': {'type': 'object',
                          'properties': {
                              'name': {'type': 'string', 'index': 'analyzed'},
                              'description': {'type': 'string', 'index': 'analyzed'},
                          }
                },
                'active': {'type': 'boolean', 'include_in_all': False},
                'status': {'type': 'string', 
                           'index': 'not_analyzed', 
                           'include_in_all': False
                },
                'creator': {'type': 'string', 
                            'index': 'not_analyzed',
                            'include_in_all': False
                },
                'lockUser': {'type': 'string', 
                             'index': 'not_analyzed',
                             'include_in_all': False
                },
                'dateCreated': {'type': 'date', 'include_in_all': False},
                'dateModified': {'type': 'date', 'include_in_all': False},
                'listItems': {'type': 'object',
                              'properties': {
                                  'title': {'type': 'string', 'index': 'analyzed'},
                                  'description': {'type': 'string', 'index': 'analyzed'},
                                  'deepdive': {'type': 'string', 'index': 'analyzed'},
                                  'active': {'type': 'boolean', 'include_in_all': False},
                                  'datecreated': {'type': 'date', 'include_in_all': False},
                                  'datemodified': {'type': 'date', 'include_in_all': False},
                              }
                }
            }
        }
        
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.pk
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
        
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value

# ListItem - A single item in a checklist. All items belonging to the same list
#            have a defined order in that list, which can be accessed and set
#            with l.get_listitem_order() and l.set_listitem_order() where l is
#            a list.
#   - title: the visible top-level text describing the item
#   - description: a short textual description of the item visible if you click
#     on the item's title
#   - deepDive: an unbounded-length description of the item accessible from the
#     shorter description
#   - active: if False, this item is obsolete (but it still uses up an integer in the listitem ordering...)
#   - list: the ID of the list to which this item is associated
#   - dateCreated: timestamp of row creation
#   - dateModified: timestamp of when the row was last modified
@python_2_unicode_compatible
class ListItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    deepDive = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    list = models.ForeignKey(List,
        on_delete=models.CASCADE,
        db_index=True
    )
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        order_with_respect_to = 'list'

    def __str__(self):
        return self.title

# List Comments - comments made on a list (for example by an editor during review)
class ListComment(models.Model):
    message = models.TextField()
    list = models.ForeignKey(List,
        on_delete=models.CASCADE,
        db_index=True
    )
    creator = models.ForeignKey(User,
        on_delete=models.CASCADE,
        db_index=True
    )
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)


# SubscriberGroup - A group of subscribers. This could either be a singleton
#                   group or a group corresponding to some organization that
#                   might purchase a bulk subscription.
#   - name: a text field describing the name of the group
#   - dateCreated: timestamp of row creation
#   - dateModified: timestamp of when the row was last modified
@python_2_unicode_compatible
class SubscriberGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.name

# Subscription - grants access to a given topic and all of its subtopics
#                to a particular subscriber group.
#   - group: the SubscriberGroup ID to which this subscription belongs
#   - topic: the topicNode ID to which this subscription belongs
#   - active: a Boolean indicating whether this subscription is currently active
#   - editPower: a Boolean indicating whether this subscription grants editing
#     privileges to the users in the subscriber group
#   - price: the price in USD that was paid for this subscription
#   - dateExpire: timestamp of Subscription expiration
#   - dateCreated: timestamp of row creation
#   - dateModified: timestamp of when the row was last modified
class Subscription(models.Model):
    group = models.ForeignKey(SubscriberGroup,
        on_delete=models.CASCADE,
        db_index=True
    )
    topic = models.ForeignKey(TopicNode,
        on_delete=models.CASCADE,
        db_index=True
    )
    active = models.BooleanField(default=True)
    editPower = models.BooleanField(default=False)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    dateExpire = models.DateTimeField(null=True, blank=True)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.group.name + ':' + self.topic.name


# Person - A user of our service. Effectively extends the User model.
#   - user: the ID of the User to which this Person is associated
#   - friends: the set of Persons that this Person is friends with (stored in a separate table)
#   - favoriteLists: the set of lists that comprise this Person's favorites (stored in a separate table).
#   - degrees: a text field describing the degrees held by this person
#   - jobTitle: a text field describing the person's current job title
#   - groups: the set of groups (encoded as SubscriberGroup IDs) to which this
#     person belongs
#   - personalDescription: a text field allowing a person to describe themselves
#   - dateCreated: timestamp of row creation
#   - dateModified: timestamp of when the row was last modified
@python_2_unicode_compatible
class Person(models.Model):
    user = models.OneToOneField(User,
        on_delete=models.CASCADE,
        primary_key=True
    )
    friends = models.ManyToManyField('self')
    favoriteLists = models.ManyToManyField(List,
        through='FavoriteList',
        related_name='favorites')
    degrees = models.CharField(max_length=200, blank=True)
    jobTitle = models.CharField(max_length=100, blank=True)
    groups = models.ManyToManyField(SubscriberGroup, through='Subscriber')
    personalDescription = models.TextField(blank=True)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.user.username

# The model description of the intermediary table for the ManyToManyField favoriteLists in Person
@python_2_unicode_compatible
class FavoriteList(models.Model):
    person = models.ForeignKey(Person,
        on_delete=models.CASCADE,
        db_index=True
    )
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.list.title

# The model description of the intermediary table for the ManyToManyField groups in Person
@python_2_unicode_compatible
class Subscriber(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    group = models.ForeignKey(SubscriberGroup, on_delete=models.CASCADE)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.group.name


# Contribution - made by a user to specific objects in List, ListItem, and extendable to other contenttypes in the future.
class Contribution(models.Model):
    content_type = models.ForeignKey(ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    contributor = models.ForeignKey(User,
        on_delete=models.CASCADE,
        db_index=True
    )
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)

#BountyType
@python_2_unicode_compatible
class BountyType(models.Model):
    name = models.CharField(max_length=200, unique=True)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.name

# Bounty
# title, description, specification, bountytype
# issuer - A null value is defined as a system-issued bounty.
#          e.g. a system-issued bounty generated on a List
#          every 6 months.
# claimer - User who collects the reward (this action sets dateCompleted)
# target  - The target (or scope) can be a particular List/User/Topic
#           and extensible to other contenttypes.
# active  - Boolean. If false, is no longer valid.
#           Q: Can an already-claimed bounty be made invalid?
class Bounty(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    specification = models.TextField()
    bountytype = models.ForeignKey(BountyType,
        on_delete=models.PROTECT,
        db_index=True
    )
    issuer = models.ForeignKey(User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_index=True,
        related_name='bounty_issuers'
    )
    claimer = models.ForeignKey(User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_index=True,
        related_name='bounty_claimers'
    )
    content_type = models.ForeignKey(ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    active = models.BooleanField(default=True)
    reward = models.IntegerField()
    solicited = models.BooleanField(default=False)
    dateExpire = models.DateTimeField()
    dateCompleted = models.DateTimeField(null=True, blank=True)
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.name

# Proposal - used to petition editor for a bounty for an existing List.
# Users with edit power can create new lists and submit them to an
# editor for approval via a proposal.
# This includes the List ID (via GenericForeignKey) along with a
# message and a proposed reward. At the time of creation, the Proposal
# is unfulfilled.
# An editor can view the currently unfulfilled Proposals on the Editor
# Dasboard and choose to issue bounty. Once the bounty has been issued,
# the proposal is updated with the associated Bounty ID, which fulfills
# it.
class Proposal(models.Model):
    message = models.CharField(max_length=1000)
    suggestedReward = models.IntegerField()
    content_type = models.ForeignKey(ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    bounty = models.ForeignKey(Bounty,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True
    )
    creator = models.ForeignKey(User,
        on_delete=models.CASCADE,
        db_index=True
    )
    dateCreated = models.DateTimeField(auto_now_add=True, blank=True)
    dateModified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.message
