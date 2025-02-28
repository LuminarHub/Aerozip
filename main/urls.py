from django.urls import path
from .views import *


urlpatterns = [
    path('',LoginView.as_view(),name='login'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify_otp'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    path('logout/',custom_logout,name='logout'),
    path('registration/',RegisterView.as_view(),name='reg'),
    path('admin-home/',AdminHomeView.as_view(),name='ah'),
]