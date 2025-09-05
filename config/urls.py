from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.views.generic import RedirectView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('app/', include('dispositivos.urls', namespace='dispositivos')),
    path('', RedirectView.as_view(url='/app/login/', permanent=True)),
]
