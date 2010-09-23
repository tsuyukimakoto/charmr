from django.conf.urls.defaults import *

from django.views.generic.list_detail import object_detail, object_list
from django.views.generic.simple import direct_to_template
from django.contrib.auth.models import User
from django.contrib.auth.views import login, logout

from views import upload_icon, user_home, claim, tbping, invite, regist, add_comment, cancel, edit_position_paper, upload_document

from models import Event, EventComment, EventTrackback, EventFile

urlpatterns = patterns('',
     (r'^users/home/$', user_home,
             dict(), 'user_home'),
     (r'^users/(?P<username>.*)/upload_icon/$', upload_icon,
             dict(), 'upload_icon'),
     (r'^users/(?P<slug>.*)/$', object_detail,
             dict(queryset=User.objects.filter(is_active=True).exclude(username='admin'),
                  slug_field='username'), 'user_detail'),
     (r'^login/$', login, dict(template_name='login.html'), 'login'),
     (r'^logout/$', logout, dict(next_page='/events/'), 'logout'),
     (r'^invite/$', invite, dict(), 'invite'),
     (r'^invite_email_sent/$', direct_to_template, dict(template='event/invite_mail_sent.html'), 'invite_email_sent'),
     (r'^regist/(?P<activate_key>.*)/$', regist, dict(), 'regist'),
     (r'^(?P<slug>.*)/claim/$', claim, dict(), 'claim'),
     (r'^(?P<slug>.*)/cancel/$', cancel, dict(), 'cancel'),
     (r'^(?P<slug>.*)/tbping/$', tbping, dict(), 'tbping'),
     (r'^(?P<slug>.*)/edit_position_paper/$', edit_position_paper, dict(), 'edit_position_paper'),
     (r'^(?P<slug>.*)/add_comment/$', add_comment, dict(), 'add_comment'),
     (r'^(?P<slug>.*)/upload_document/$', upload_document, dict(), 'upload_document'),
     (r'^(?P<slug>.*)/$', object_detail, dict(queryset=Event.objects.all()), 'event_detail'),
     (r'^$',object_list, dict(queryset=Event.objects.all().order_by('-time_to_start'),
                extra_context={'recent_comment': lambda: EventComment.objects.all().order_by('-id')[:5],
                               'recent_trackback': lambda: EventTrackback.objects.all().order_by('-id')[:5],
                               'recent_document': lambda: EventFile.objects.all().order_by('-id')[:5]
                }), 'event_list'),
)
