from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('unilar.urls')),
]
from django.conf import settings

if settings.GOOGLE_LOGIN_ATIVO:
    urlpatterns.append(path('accounts/', include('allauth.urls')))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
