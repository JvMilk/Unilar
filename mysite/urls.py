from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('unilar.urls')),
]
from django.conf import settings

if settings.GOOGLE_LOGIN_ATIVO:
    urlpatterns.append(path('accounts/', include('allauth.urls')))
