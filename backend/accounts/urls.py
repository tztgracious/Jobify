from django.urls import path

from .views import SignupView, login_view

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', login_view, name='login'),
]
