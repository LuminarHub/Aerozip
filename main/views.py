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
            print("user",user)
            if user:
                login(request, user)

                if request.user.is_superuser:
                    return redirect('ah')
                else:
                    return redirect('uh')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")

        return render(request, 'login.html', {"form": form})
    
    
class RegisterView(CreateView):
    template_name = 'reg.html'
    model = CustomUser 
    form_class = RegForm 
    success_url = reverse_lazy('login')


class AdminHomeView(TemplateView):
    template_name="admin_home.html"
    
    
