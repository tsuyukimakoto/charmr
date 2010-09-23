from django.conf.urls.defaults import *
from django.views import static
from django.conf import settings

urlpatterns = patterns('',
    # Example:

    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),
     (settings.STATIC_REGIX, static.serve, dict(document_root=settings.MEDIR_DIR, show_indexes=True)),
     (r'^events/', include('charmr.event.urls')),
)
