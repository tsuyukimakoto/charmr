from django.conf import global_settings

DEBUG = False
TEMPLATE_DEBUG = DEBUG

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))



DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = os.path.join(BASE_DIR, 'data.sqlite')             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

MEDIA_SUFFIX = 'static'
MEDIA_URL = '/%s' % MEDIA_SUFFIX

MEDIR_DIR = os.path.join(BASE_DIR, MEDIA_SUFFIX)

STATIC_REGIX = r'^%s/(?P<path>.*)' % MEDIA_SUFFIX


SECRET_KEY = 'w^^9gf9xcre==h7qlsl-i6^_zqn23)l=m*aiju2c0d*^#$ar)_'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'initial_header_level': 2,
}

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + ('charmr.event.context.event_context', )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.markup',
    'charmr.event',
)

LOGIN_URL = '/events/login/'
LOGIN_REDIRECT_URL = '/events/users/home/'

NG_USERNAME = ('admin', 'support', 'help', 'django', 'python', 'spam', 'egg', 'ham', 'fuck', 'sex', 'penis', 'manko', 'chinko', 'guido', 'adrian', )

#IF you use gmail for invitation mail comment in below and set user/password.
#Or just fill EMAIL_HOST and EMAIL_PORT for using your smtpserver.
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'xxx@gmail.com'
EMAIL_HOST_PASSWORD = 'xxxxxxxx'
EMAIL_PORT = 587

TEST_RUNNER = 'django.test.simple.run_simple_and_all_doctest'
