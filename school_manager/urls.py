# school_manager/school_manager/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('teacher/', include('teacher.urls')),
]