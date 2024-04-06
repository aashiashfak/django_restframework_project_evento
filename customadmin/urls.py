from django.urls import path
from .views import SuperUserLoginView

urlpatterns = [
    path('login/', SuperUserLoginView.as_view(), name='superuser-login'),
]
