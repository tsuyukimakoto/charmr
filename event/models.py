from django.conf import settings
from django.db import models
from django.db.models import permalink

from django.contrib.auth.models import User
from django.dispatch import dispatcher
from django.db.models import signals

from django.utils.translation import ugettext as _

from django.contrib.markup.templatetags.markup import restructuredtext

from datetime import datetime

class EventProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    nickname = models.CharField(max_length=30)
    twitter_name = models.CharField(max_length=30, blank=True)
    pownce_name = models.CharField(max_length=30, blank=True)
    blog_url = models.URLField(blank=True)
    icon = models.ImageField('', upload_to='icon', blank=True, null=True)
    
    class Admin:
        pass
    
    def _icon_url(self):
        if self.get_icon_url():
            return settings.MEDIA_URL + '/icon/%s.png' % self.user.username
        return settings.MEDIA_URL + '/icon/anonymous.png'
    icon_url = property(_icon_url)

    def _large_icon_url(self):
        if self.get_icon_url():
            return settings.MEDIA_URL + '/icon/%s' % self.user.username + '_large.png'
        return settings.MEDIA_URL + '/icon/anonymous_large.png'
    large_icon_url = property(_large_icon_url)

class Place(models.Model):
    name = models.CharField(_(u'Place to hold'), max_length=100)
    lat = models.DecimalField(_(u'Latitude'), blank=True, null=True, max_digits=17, decimal_places=14)
    lng = models.DecimalField(_(u'Latitude'), blank=True, null=True, max_digits=17, decimal_places=14)
    link = models.URLField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    tel = models.CharField(max_length=20, blank=True)
    attention = models.CharField(max_length=200, blank=True)

    class Admin:
        list_display = ('name', 'tel', 'attention', )
    
    def __unicode__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(_(u'Event Name'), max_length=100)
    sub_title = models.CharField(_(u'Sub Title'), max_length=100)
    slug = models.SlugField(unique=True)
    time_to_start = models.DateTimeField(_('Event start time'), blank=True, null=True)
    time_to_finish = models.DateTimeField(_('Event finish taime'), blank=True, null=True)
    place = models.ForeignKey(Place)
    max_people = models.IntegerField()
    apply_from = models.DateTimeField(_(u'Date and Time to start applying'), blank=True, null=True)
    apply_to   = models.DateTimeField(_(u'Date and Time to finish applying'), blank=True, null=True)
    pos_paper  = models.TextField(_(u'Position Paper Template'), blank=True)
    owner = models.ForeignKey(User)
    staff = models.ManyToManyField(User, related_name='event_staff', filter_interface=models.HORIZONTAL, limit_choices_to={ 'is_staff': True })
    
    def is_claimable(self):
        """
        >>> e = Event(name='test_name', sub_title='test_sub_title', slug='test_slug', place_id=1, max_people=10, pos_paper = u'')
        >>> e.is_claimable()
        False
        
        >>> from datetime import timedelta
        >>> now = datetime.now()
        >>> e.apply_from = now
        >>> e.is_claimable()
        True
        
        >>> e.apply_to = now + timedelta(hours=1)
        >>> e.is_claimable()
        True
        
        >>> e.apply_from = now + timedelta(minutes=2)
        >>> e.is_claimable()
        False
        
        >>> e.apply_from = now
        >>> e.apply_to = now + timedelta(minutes=-1)
        >>> e.is_claimable()
        False
        
        >>> e.apply_from = now
        >>> e.apply_to = now + timedelta(minutes=1)
        >>> e.time_to_start = now + timedelta(minutes=1)
        >>> e.is_claimable()
        True
        
        >>> e.time_to_start = now + timedelta(minutes=-1)
        >>> e.is_claimable()
        False
        """
        now = datetime.now()
        if not self.apply_from:
            return False
        if now >= self.apply_from and (not self.apply_to or now < self.apply_to):
            if not self.time_to_start or now < self.time_to_start:
                return True
        return False

    class Admin:
        date_hierarchy = 'time_to_start'
        list_display = ('name', 'slug', 'time_to_start', 'apply_from', 'max_people', 'owner', )
        fields = (
            (_(u'Title'), { 'fields': (('name', 'sub_title'),)}),
            (_(u'URL'), { 'fields': ('slug',),}),
            (_(u'Schedule'), { 'fields': ('time_to_start', 'time_to_finish','apply_from', 'apply_to')}),
            (_(u'Info'), { 'fields': ('place', 'max_people', 'pos_paper', 'owner', 'staff',)}),
        )
    
    class Meta:
        ordering = ['id',]
    
    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return ('event_detail', (), { 'slug': self.slug })
    get_absolute_url = permalink(get_absolute_url)
    
    def get_spec_text(self):
        return '\n\n'.join([s.desc for s in self.spec_set.all()])

    def staff_list(self):
        return self.staff.all()
    
    def attendant_list(self):
        att = self.attendant_set.all()
        return att[:self.max_people]
    
    def waiting_list(self):
        att = list(self.attendant_set.all())
        return att[self.max_people:]

class Spec(models.Model):
    event = models.ForeignKey(Event, edit_inline=True)
    sort_order = models.IntegerField()
    desc = models.TextField(_(u'Specification Text'), core=True)

    class Meta:
        ordering = ['sort_order',]
    
class Attendant(models.Model):
    event = models.ForeignKey(Event)
    user  = models.ForeignKey(User)
    pos_paper = models.TextField(blank=True, help_text=_(u'Modify this structured text.'))
    apply_date = models.DateTimeField(editable=False)
    canceled = models.BooleanField(default=False)
    
    class Admin:
        list_display = ('event', 'user', 'canceled', )
    
    class Meta:
        unique_together = (('event', 'user', ), )
        ordering = ['id',]
    
    def save(self):
        if not self.id:
            self.apply_date = datetime.now()
        super(Attendant, self).save()

    
from random import choice

class ActivateKeyManager(models.Manager):
    """
    >>> keys = []
    >>> for i in range(50):
    ...     k = ActivateKey.objects.next().activate_key
    ...     assert k not in keys
    ...     keys.append(k)
    """
    def next(self):
        try:
            key = ''.join([choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(50)])
            ActivateKey.objects.get(activate_key__exact=key)
            return self.next()
        except ActivateKey.DoesNotExist:
            act = ActivateKey(activate_key=key, activated=False)
            act.save()
            return act

class ActivateKey(models.Model):
    activate_key = models.CharField(_('Activation Key'), maxlength=50, unique=True)
    activated = models.BooleanField(_('Activate Flag'), default=False)
    email     = models.EmailField(_('Email'))

    objects = ActivateKeyManager()    

    class Admin:
        list_display = ('email', 'activated', )
        list_filter = ('activated',)

class EventComment(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(User)
    date = models.DateTimeField(blank=True)
    comment = models.TextField(max_length=3000)
    
    class Admin:pass

    class Meta:
        ordering = ['-id',]

    def save(self):
        if not self.id:
            self.date = datetime.now()
        super(EventComment, self).save()

class EventTrackback(models.Model):
    event = models.ForeignKey(Event)
    date = models.DateTimeField(blank=True)
    blog_name = models.CharField(maxlength=200, blank=True)
    url = models.URLField(blank=False, verify_exists=False)
    excerpt = models.TextField(blank=False)
    
    class Admin:pass

    class Meta:
        ordering = ['-id',]
    
    def save(self):
        if not self.id:
            self.date = datetime.now()
        super(EventTrackback, self).save()


class EventFile(models.Model):
    event = models.ForeignKey(Event)
    user  = models.ForeignKey(User)
    date = models.DateTimeField(blank=True, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    document = models.FileField(upload_to=settings.MEDIA_SUFFIX + '/document/%Y/%m/%d')

    class Admin:pass

    class Meta:
        ordering = ['id',]
    
    def save(self):
        if not self.id:
            self.date = datetime.now()
        super(EventFile, self).save()

def add_user_call_back(signal, sender, instance, **kwags):
    """
    >>> from django.contrib.auth.models import User
    >>> u = User.objects.create_user('testuser', 'test@everes.net', password='password')
    >>> profile = u.get_profile()
    >>> profile.nickname
    u'testuser'
    """
    try:
        instance.get_profile()
    except EventProfile.DoesNotExist:
        profile = EventProfile()
        profile.user = instance
        profile.nickname = instance.username
        profile.save()

dispatcher.connect(
    receiver = add_user_call_back,
    signal   = signals.post_save,
    sender   = User
)
