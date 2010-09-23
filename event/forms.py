# -*- coding: utf-8 -*-
from django import newforms as forms
from django.contrib.auth.models import User

from django.conf import settings

import re

class InviteForm(forms.Form):
    email = forms.EmailField(label=_('Email'))

class RegistForm(forms.Form):
    username = forms.CharField(label=_('Username'), min_length=4, max_length=30)
    password1 = forms.CharField(label=_('Password'), min_length=6, max_length=60, widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirm Passowrd'), min_length=6, max_length=60, widget=forms.PasswordInput)
    
    
    def clean_username(self):
        value = self.cleaned_data.get('username')
        if not alnum_re.search(value):
            raise forms.ValidationError, _(u"This value must contain only letters, numbers and underscores.")
        ng = [u for u in settings.NG_USERNAME if u in value.lower()]
        if ng:
            raise forms.ValidationError, _(u"You can't use this username(prohibited).")
        try:
            User.objects.get(username__iexact=value)
            raise forms.ValidationError, _(u"Username already taken.")
        except User.DoesNotExist:
            return self.cleaned_data.get('username')
    
    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if not (p1 == p2):
            raise forms.ValidationError, _(u"Confirm password.")
        return p2

    def save(self):
        user = User.objects.create_user(self.cleaned_data.get('username'), '', self.cleaned_data.get('password1'))
        return user

def clean_icon(self, value):
    if 'content-type' in value:  
        main, sub = value['content-type'].split('/')  
        if not (main == 'image' and sub in ['jpeg', 'gif', 'png']):  
            raise forms.ValidationError(_('JPEG, PNG, GIF only.'))  
    return value  

alnum_re = re.compile(r'^\w+$')

def isAlphaNumeric(field_data, all_data):
    """
    >>> var = 'ascii_123a'
    >>> isAlphaNumeric(var, None)
    """
    if not alnum_re.search(field_data):
        raise ValidationError, _(u"This value must contain only letters, numbers and underscores.")
