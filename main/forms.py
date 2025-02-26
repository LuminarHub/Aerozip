from django import forms
from .models import *


class LogForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={"placeholder":"Email","class":"form-control","style":"border-radius: 0.75rem; "}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={"placeholder":"Password","class":"form-control","style":"border-radius: 0.75rem; "}))


class RegForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
        
        

# class ShipmentForm(forms.ModelForm):
#     recipient_address = forms.ModelChoiceField(queryset=None)
    
#     class Meta:
#         model = Shipment
#         fields = ['user','shipment_type','from_airport','to_airport','sender_address','recipient_address', 'shipping_speed', 'notes','weight']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['recipient_address'].queryset = Address.objects.filter(user=user)