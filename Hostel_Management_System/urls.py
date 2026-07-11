from django.contrib import admin
from django.urls import path , include

urlpatterns = [
    path('' , include('hms.urls')),
    path('student/',include('student.urls')),
    path('room/', include('room.urls')),
    path('authentication/',include('authentication.urls')),
    path('paybill/', include('paybill.urls')),
    path('leave/', include('leave.urls')),
    path('student_app/', include('student_app.urls')),
    path('warden/', include('warden.urls')),
    
    path('admin/', admin.site.urls),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
