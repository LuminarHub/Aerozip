from django.shortcuts import render,redirect,get_object_or_404
from django.views.generic import TemplateView,FormView,CreateView,UpdateView,DeleteView,View
from django.http import JsonResponse
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate,login,logout
from .forms import *
from .models import *
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .utils import *

def custom_logout(request):
    auth_logout(request)
    return redirect('login')



class LoginView(FormView):
    template_name = "login.html"
    form_class = LogForm

    def post(self, request, *args, **kwargs):
        form = LogForm(data=request.POST)
        if form.is_valid():  
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            user = authenticate(request, email=email, password=password)
            
            if user:
                if user.is_verified:
                    login(request, user)
                    if user.is_superuser:
                        return redirect('ah')
                    else:
                        return redirect('uh')
                else:
                    # User exists but not verified - send OTP
                    otp = generate_otp()
                    
                    # Save OTP to database
                    OTP.objects.filter(email=email).delete()  # Delete old OTPs
                    OTP.objects.create(email=email, otp=otp)
                    
                    # Send OTP via email
                    send_otp_email(email, otp)
                    
                    # Store email in session for verification
                    request.session['verification_email'] = email
                    request.session['verification_for_login'] = True
                    
                    messages.info(request, "Please verify your account. OTP has been sent to your email.")
                    return redirect('verify_otp')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")

        return render(request, 'login.html', {"form": form})

class OTPVerificationView(FormView):
    template_name = "verify_otp.html"
    form_class = OTPVerificationForm
    
    def get(self, request, *args, **kwargs):
        if 'verification_email' not in request.session:
            messages.error(request, "Verification session expired")
            return redirect('login')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        form = OTPVerificationForm(data=request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data.get('otp')
            email = request.session.get('verification_email')
            
            # Check if OTP exists and is valid
            try:
                otp_obj = OTP.objects.get(email=email, otp=entered_otp)
                if otp_obj.is_valid():
                    # Mark user as verified
                    user = CustomUser.objects.get(email=email)
                    user.is_verified = True
                    user.save()
                    
                    # Clean up
                    OTP.objects.filter(email=email).delete()
                    
                    messages.success(request, "Account verified successfully!")
                    
                    # If this was for login, log the user in
                    if request.session.get('verification_for_login'):
                        login(request, user)
                        if user.is_superuser:
                            return redirect('ah')
                        else:
                            return redirect('uh')
                    else:
                        return redirect('login')
                else:
                    messages.error(request, "OTP has expired. Please request a new one.")
            except OTP.DoesNotExist:
                messages.error(request, "Invalid OTP. Please try again.")
                
        return render(request, 'verify_otp.html', {"form": form})

def resend_otp(request):
    """Resend OTP to the user's email"""
    if 'verification_email' in request.session:
        email = request.session.get('verification_email')
        
        # Generate and save new OTP
        otp = generate_otp()
        OTP.objects.filter(email=email).delete()  # Delete old OTPs
        OTP.objects.create(email=email, otp=otp)
        
        # Send OTP via email
        send_otp_email(email, otp)
        
        messages.success(request, "OTP resent successfully!")
    else:
        messages.error(request, "Verification session expired")
    
    return redirect('verify_otp')
    
    
class RegisterView(CreateView):
    template_name = 'reg.html'
    model = CustomUser 
    form_class = RegForm 
    success_url = reverse_lazy('login')


class AdminHomeView(TemplateView):
    template_name="admin_home.html"
    
    
