from django.urls import path
from .views import *


urlpatterns = [
    path('',LoginView.as_view(),name='login'),
    path('logout/',custom_logout,name='logout'),
    path('registration/',RegisterView.as_view(),name='reg'),
    path('admin-home/',AdminHomeView.as_view(),name='ah'),
]