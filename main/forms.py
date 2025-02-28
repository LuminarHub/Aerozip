from django import forms
from .models import *


class LogForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={"placeholder":"Email","class":"form-control","style":"border-radius: 0.75rem; "}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={"placeholder":"Password","class":"form-control","style":"border-radius: 0.75rem; "}))


class RegForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ['user']
        
        
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['shipment_id', 'rating', 'title', 'comment', 'delivery_satisfaction']
        widgets = {
            'shipment_id': forms.TextInput(attrs={'class': 'rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'}),
            'rating': forms.Select(attrs={'class': 'rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'}),
            'title': forms.TextInput(attrs={'class': 'rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'}),
            'comment': forms.Textarea(attrs={'class': 'rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5', 'rows': 4}),
            'delivery_satisfaction': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500'})
        }
        labels = {
            'shipment_id': 'Shipment ID (Optional)',
            'delivery_satisfaction': 'Were you satisfied with the delivery?'
        }
# class ShipmentForm(forms.ModelForm):
#     recipient_address = forms.ModelChoiceField(queryset=None)
    
#     class Meta:
#         model = Shipment
#         fields = ['user','shipment_type','from_airport','to_airport','sender_address','recipient_address', 'shipping_speed', 'notes','weight']
    
    # def __init__(self, *args, **kwargs):
    #     user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)
    #     if user:
    #         self.fields['recipient_address'].queryset = Address.objects.filter(user=user)