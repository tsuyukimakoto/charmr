from django.utils.translation import ugettext as _

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader, Context, RequestContext
from django.core.urlresolvers import reverse
from django import newforms as forms
from django.views.generic import list_detail
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site

from forms import InviteForm, RegistForm, clean_icon

from utils import resize_image
import new

from models import EventComment, EventTrackback, EventFile, Attendant, Event, EventProfile, ActivateKey

def claim(request, slug):
    event = get_object_or_404(Event, slug=slug)
    attendants = Attendant.objects.filter(event=event.id)
    user_id_list = [a.user_id for a in attendants]
    AttendantForm = forms.form_for_model(Attendant)
    if not event.is_claimable():
        return HttpResponseRedirect(event.get_absolute_url())
    if not request.user.id in user_id_list:
        if request.method == "POST":
            new_data = request.POST.copy()
            new_data.update({'user': request.user.id, 'event': event.id, 'cancel': False})
            form = AttendantForm(new_data)
            if form.is_valid():
                #attendant = Attendant()
                #attendant.user = requeset.user
                #attendant.event = event
                #attendant.cancel = False
                #attendant.pos_paper = 
                #attendant.cache_html = ""
                #attendant.save()
                form.save()
                request.user.message_set.create(
                    message=_(u'You made a reservation to %(event_name)s . Check your status.') % {'event_name': event.name })
                if event.max_people <= len(attendants):
                    request.user.message_set.create(
                        message=_(u'You are put on a waiting list for cancellation'))
                return HttpResponseRedirect(event.get_absolute_url())
        else:
            del AttendantForm.base_fields['user']
            del AttendantForm.base_fields['event']
            del AttendantForm.base_fields['canceled']
            AttendantForm.base_fields['pos_paper'].widget = forms.Textarea(attrs={'cols':'80'})
            AttendantForm.base_fields['pos_paper'].label = ''
            form = AttendantForm(initial={'pos_paper': event.pos_paper})
            if event.max_people <= len(attendants):
                request.user.message_set.create(
                    message=_(u'Capacity is full already. You are going to putting on a waiting list for cancellation') % {'event_name': event.name })
            request.user.message_set.create(
                message=_(u'Will you attend %(event_name)s ?') % {'event_name': event.name })
    else:
        request.user.message_set.create(
            message=_('You already joined event "%(event_name)s".') % {'event_name': event.name})
        return HttpResponseRedirect(event.get_absolute_url())
    return render_to_response('event/claim.html', context_instance=RequestContext(request, {'object': event, 'form': form}))
claim = login_required(claim)

def cancel(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if not event.is_claimable():
        request.user.message_set.create(
            message=_("You can make a cancel only claimable period."))
        return HttpResponseRedirect(event.get_absolute_url())
    attendants = Attendant.objects.filter(event=event.id, user=request.user.id)
    if len(attendants) == 0:
        raise Http404()
    if request.method == "POST":
        attendant = attendants[0]
        attendant.delete()
        request.user.message_set.create(
            message=_('Your claim was removed from "%(event_name)s".') % {'event_name': event.name})
        return HttpResponseRedirect(event.get_absolute_url())
    return render_to_response('event/cancel_confirm.html', context_instance=RequestContext(request, {'object': event}))
cancel = login_required(cancel)

def edit_position_paper(request, slug):
    event = get_object_or_404(Event, slug=slug)
    attendants = Attendant.objects.filter(event=event.id, user=request.user.id)
    if len(attendants) == 0:
        raise Http404()
    PaperEdit = forms.form_for_instance(attendants[0])
    del PaperEdit.base_fields['user']
    del PaperEdit.base_fields['event']
    del PaperEdit.base_fields['canceled']
    if request.method == "POST":
        form = PaperEdit(request.POST.copy())
        if form.is_valid():
            form.save()
            request.user.message_set.create(
                message=_(u'Your Position Paper successfully updated.'))
            return HttpResponseRedirect(event.get_absolute_url())
    else:
        form = PaperEdit()
    return render_to_response('event/edit_position_paper.html', context_instance=RequestContext(request, {'object': event, 'form': form}))
edit_position_paper = login_required(edit_position_paper)

def upload_document(request, slug):
    event = get_object_or_404(Event, slug=slug)
    attendants = Attendant.objects.filter(event=event.id, user=request.user.id)
    user_id_list = [a.user_id for a in attendants]
    if not request.user.id in user_id_list:
        staff_list = event.staff.all()
        if not [a.id for a in staff_list if request.user.id == a.id]:
            request.user.message_set.create(
                message=_(u'Only Attendant or Staff can add document.'))
            return HttpResponseRedirect(reverse('event_detail', kwargs=dict(slug=slug)))
    EventFileForm = forms.form_for_model(EventFile)
    if request.method == "POST":
        new_data = request.POST.copy()
        print request.FILES
        new_data.update({'event': event.id, 'user': request.user.id})
        form = EventFileForm(new_data, request.FILES)
        if form.is_valid():
            form.save()
            request.user.message_set.create(
                message=_(u'Document upload successfully.'))
            return HttpResponseRedirect(event.get_absolute_url())
    else:
        del EventFileForm.base_fields['user']
        del EventFileForm.base_fields['event']
        form = EventFileForm()
    return render_to_response('event/upload_document.html', context_instance=RequestContext(request, {'object': event, 'form': form}))
upload_document = login_required(upload_document)


def invite(request):
    if request.POST:
        form = InviteForm(request.POST)
        if form.is_valid():
            site = Site.objects.get(pk=settings.SITE_ID)
            key = ActivateKey.objects.next()
            key.email = form.cleaned_data['email']
            key.save()
            activate_url = '%s%s' % (site.domain, reverse('regist', kwargs=dict(activate_key=key.activate_key)))
            t = loader.get_template('event/mail/invite.mail')
            c = RequestContext(request, {'domain': site.name, 'activate_url': activate_url })
            mail = EmailMessage(_(u'Invitation from %s') % site.name, t.render(c), to = [form.cleaned_data['email']])
            mail.send()
            #request.user.message_set.create(
            #    message=_('Sent invitation message to %(address)s') % {'address': form.cleaned_data['email']})
            #return HttpResponseRedirect(URL_HOME)
            return HttpResponseRedirect(reverse('invite_email_sent'))
    else:
        form = InviteForm()
    return render_to_response('event/invite.html', context_instance=RequestContext(request, {'form': form}))


def regist(request, activate_key):
    act = list(ActivateKey.objects.filter(activate_key__exact=activate_key, activated=False))
    if not act:
        raise Http404()
    act = act[0]
    if request.method == 'POST':
        new_data = request.POST.copy()
        new_data.update({'email': act.email})
        form = RegistForm(new_data)
        if form.is_valid():
            user = form.save()
            user.email = act.email
            user.save()
            act.activated = True
            act.save()
            #return HttpResponseRedirect(URL_HOME)
            return HttpResponseRedirect(reverse('login'))
    else:
        form = RegistForm()
    return render_to_response('event/regist.html', context_instance=RequestContext(request, {'form': form}))


def user_home(request):
    user = request.user
    profile = user.get_profile()
    ProfileEdit = forms.form_for_instance(profile)
    del ProfileEdit.base_fields['user']
    del ProfileEdit.base_fields['icon']
    if request.method == 'POST':
        new_data = request.POST.copy()
        profile_form = ProfileEdit(new_data)
        if profile_form.is_valid():
            profile_form.save()
            request.user.message_set.create(
                message=_('Profile update successfully.'))
            return HttpResponseRedirect(reverse('user_home'))
    else:
        profile_form = ProfileEdit()
    return render_to_response('auth/user_home.html', context_instance=RequestContext(request, {'profile_form': profile_form}))
user_home = login_required(user_home)


def upload_icon(request, username):
    thumb_icon_width = 64
    large_icon_width = 128
    user = request.user
    profile = user.get_profile() 
    ProfileEdit = forms.form_for_instance(profile)
    del ProfileEdit.base_fields['user']
    del ProfileEdit.base_fields['nickname']
    del ProfileEdit.base_fields['twitter_name']
    del ProfileEdit.base_fields['pownce_name']
    del ProfileEdit.base_fields['blog_url']
    #ProfileEdit.base_fields['icon'].widget = forms.FileInput()
    #ProfileEdit.base_fields['icon'].clean = new.instancemethod(clean_icon,
    #                                                ProfileEdit.base_fields['icon'],
    #                                                ProfileEdit.base_fields['icon'].__class__)
    if request.method == 'POST':
        if 'icon' in request.FILES:
            thumb_path = 'icon/%s.png' % user.username
            large_path = 'icon/%s_large.png' % user.username
            new_data = request.POST.copy()
            file_data = request.FILES.copy()
            try:
                file_data['icon']['filename'] = '%s.png' % user.username
                profile_form = ProfileEdit(new_data, file_data)
                if profile_form.is_valid():
                    if 'icon' in ProfileEdit.base_fields:  
                        from StringIO import StringIO  
                        from PIL import Image  
                        icon = Image.open(StringIO(request.FILES['icon']['content']))  
                        icon = icon.convert("RGB")
                        x, y = icon.size
                        thumb_im = resize_image(icon, x, y, thumb_icon_width)
                        large_im = resize_image(icon, x, y, large_icon_width)
                        thumb_icon_path = '%s/%s' % (settings.MEDIR_DIR, thumb_path)  
                        large_icon_path = '%s/%s' % (settings.MEDIR_DIR, large_path)  
                        thumb_im.save(thumb_icon_path, 'png')
                        large_im.save(large_icon_path, 'png')
                        #profile_form.cleaned_data['icon'] = thumb_path
                    profile_form.save()
                    request.user.message_set.create(
                        message=_('Profile image update successfully.'))
            except:
                pass
    return HttpResponseRedirect(reverse('user_home'))

CommentForm = forms.form_for_model(EventComment)

def add_comment(request, slug):
    event = get_object_or_404(Event, slug=slug)
    attendants = Attendant.objects.filter(event=event.id)
    user_id_list = [a.user_id for a in attendants]
    if not request.user.id in user_id_list:
        staff_list = event.staff.all()
        if not [a.id for a in staff_list if request.user.id == a.id]:
            request.user.message_set.create(
                message=_(u'Only Attendant or Staff can add comment.'))
            return HttpResponseRedirect(reverse('event_detail', kwargs=dict(slug=slug)))
    if request.method == "POST":
        new_data = request.POST.copy()
        new_data.update({'event': event.id, 'user': request.user.id})
        form = CommentForm(new_data)
        if form.is_valid():
            if request.POST.get("mode", "preview") == "post":
                form.save()
                request.user.message_set.create(
                    message=_(u'Your comment successfully added. thanx!'))
                return HttpResponseRedirect(reverse('event_detail', kwargs=dict(slug=slug)))
            else:
                return render_to_response('event/add_comment.html', context_instance=RequestContext(request, {'form': form, 'object': event, 'preview_data': request.POST.get('comment', '')}))
    else:
        form = CommentForm()
    return render_to_response('event/add_comment.html', context_instance=RequestContext(request, {'form': form, 'object': event}))
add_comment = login_required(add_comment)

TrackbackForm = forms.form_for_model(EventTrackback)
#TODO check url whther event attendant or not

def tbping(request, slug) :
    if request.POST :
        try:
            event = get_object_or_404(Event, slug=slug)
            msg = ''
            error = ''
            new_data = request.POST.copy()
            new_data.update({'event': event.id})
            url = new_data.get('url', '')
            #TODO move this check to TrackbackForm
            profile_list = EventProfile.objects.exclude(blog_url="").filter(user__event__id=event.id)
            profile_exist = [p for p in profile_list if p.blog_url in url]
            if len(profile_exist) == 0:
                error = _(u"You don't have permission to trackback this entry")
                msg   = _(u"Trackback to %(event_name)s is permitted only attendant.") % {'event_name': event.name}
            else :
                form = TrackbackForm(new_data)
                if form.is_valid():
                    form.save()
                    msg = 'thanx!'
                    print 'success Trackback'
                else:
                    error = form.errors
                    msg = _(u"Your Trackabck has input error(s)")
            response = HttpResponse(mimetype='text/xml')
            t = loader.get_template('tbping.xml')
            c = Context({
                'error': error,
                'msg': msg,
            })
            response.write(t.render(c))
            return response
        except Exception, e:
            print e
            raise e
    else :
        return HttpResponseRedirect(reverse('event_detail', kwargs=dict(slug=slug)))
