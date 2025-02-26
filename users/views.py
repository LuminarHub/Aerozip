from django.shortcuts import render,redirect
from django.views.generic import TemplateView
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from main.models import *
from main.forms import *
import uuid
from datetime import datetime, timedelta

# shipment.tracking_number = f"AZ{uuid.uuid4().hex[:8].upper()}"
         
            
            # # Calculate estimated delivery based on shipping speed
            # today = datetime.now().date()
            # if shipment.shipping_speed == 'overnight':
            #     shipment.estimated_delivery = today + timedelta(days=1)
            # elif shipment.shipping_speed == 'express':
            #     shipment.estimated_delivery = today + timedelta(days=3)
            # else:
            #     shipment.estimated_delivery = today + timedelta(days=5)
            
            # # Calculate shipping cost (simplified example)
            # base_cost = 10
            # if shipment.shipping_speed == 'overnight':
            #     shipment.shipping_cost = base_cost * 3
            # elif shipment.shipping_speed == 'express':
            #     shipment.shipping_cost = base_cost * 2
            # else:
            #     shipment.shipping_cost = base_cost
            


@login_required
def create_shipment(request):
    if request.method == 'POST':
        try:
            # Extract POST data
            user = request.user
            sender_address = Address.objects.get(id=request.POST.get("sender_address"))
            recipient_address = Address.objects.get(id=request.POST.get("recipient_address"))
            shipment_type = request.POST.get("shipment_type")
            from_airport_code = request.POST.get("from_airport")
            # from_airport_place = request.POST.get("from_airport_place")
            # from_airport_code = request.POST.get("from_airport_code")
            to_airport_code = request.POST.get("to_airport")
            # to_airport_place = request.POST.get("to_airport_place")
            # to_airport_code = request.POST.get("to_airport_code")
            weight = float(request.POST.get("weight", 0))
            shipping_speed = request.POST.get("shipping_speed")
            notes = request.POST.get("notes")
            
            if shipment_type == 'international':
                airport = InternationalAirports.objects.get(code=from_airport_code)
                from_airport_place = airport.location
                from_airport_name = airport.name
                toairport = InternationalAirports.objects.get(code=to_airport_code)
                to_airport_place = toairport.location
                to_airport_name = toairport.name
            else:
                airport = DomesticAirports.objects.get(code=from_airport_code)
                from_airport_place = airport.location
                from_airport_name = airport.name
                toairport = DomesticAirports.objects.get(code=to_airport_code)
                to_airport_place = toairport.location
                to_airport_name = toairport.name
            
            # Create the Shipment object
            shipment = Shipment.objects.create(
                user=user,
                sender_address=sender_address,
                recipient_address=recipient_address,
                shipment_type=shipment_type,
                from_airport_name=from_airport_name,
                from_airport_place=from_airport_place,
                from_airport_code=from_airport_code,
                to_airport_name=to_airport_name,
                to_airport_place=to_airport_place,
                to_airport_code=to_airport_code,
                weight=weight,
                shipping_speed=shipping_speed,
                notes=notes
            )

            # Print confirmation
            print(f"Tracking Number: {shipment.tracking_number}")
            print(f"Estimated Delivery Date: {shipment.estimated_delivery}")
            print(f"Shipping Cost: ₹{shipment.shipping_cost}")

            # Success message & redirect
            messages.success(request, 'Shipment created successfully!')
            return redirect('my', tracking_number=shipment.tracking_number)

        except Address.DoesNotExist:
            messages.error(request, "Invalid address selection.")
        except ValueError:
            messages.error(request, "Invalid weight value.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    # Fetch data for the form
    international = InternationalAirports.objects.all()
    domestic = DomesticAirports.objects.all()
    addresses = Address.objects.filter(user=request.user)

    context = {
        'international': international,
        'domestic': domestic,
        'addresses': addresses,
    }
    return render(request, 'shipment.html', context)

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def add_address(request):
    """View for adding a new address"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)

        name = data.get('name')
        street_address = data.get('street_address')
        city = data.get('city')
        state = data.get('state')
        country = data.get('country')
        postal_code = data.get('postal_code')
        phone = data.get('phone')
        is_default = data.get('is_default', False)

        # Debugging
        # print("Processed Data:", name, street_address, city, state, country, postal_code, phone, is_default)

        try:
            Address.objects.create(
                user=request.user,  
                name=name,
                street_address=street_address,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                phone=phone,
                is_default=is_default
            )
            messages.success(request, 'Address added successfully!')
            return JsonResponse({'success': True, 'message': 'Address added successfully'}, status=201)
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({'success': False, 'message': f'Error adding address: {str(e)}'}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
        
    

@login_required
def shipment_detail(request, tracking_number):
    shipment = Shipment.objects.get(tracking_number=tracking_number)
    if shipment.user != request.user:
        messages.error(request, 'You do not have permission to view this shipment.')
        return redirect('dashboard')
    
    context = {
        'shipment': shipment,
        'tracking_updates': shipment.tracking_updates.all()
    }
    return render(request, 'shipment_detail.html', context)


class UserHomeView(TemplateView):
    template_name = "user_home.html"

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

class MyShipmentView(LoginRequiredMixin, ListView):
    template_name = "myshipments.html"
    context_object_name = "shipments"
    paginate_by = 10
    
    def get_queryset(self):
        # Get shipments for the logged-in user
        queryset = Shipment.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Apply filters if provided
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        shipment_type = self.request.GET.get('type')
        if shipment_type:
            queryset = queryset.filter(shipment_type=shipment_type)
            
        date_range = self.request.GET.get('date_range')
        if date_range:
            today = timezone.now().date()
            if date_range == '7':
                date_from = today - timedelta(days=7)
            elif date_range == '30':
                date_from = today - timedelta(days=30)
            elif date_range == '90':
                date_from = today - timedelta(days=90)
            else:
                date_from = None
                
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
                
        # Handle search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                tracking_number__icontains=search_query
            ) | queryset.filter(
                from_airport_place__icontains=search_query
            ) | queryset.filter(
                to_airport_place__icontains=search_query
            ) | queryset.filter(
                from_airport_name__icontains=search_query
            ) | queryset.filter(
                to_airport_name__icontains=search_query
            ) | queryset.filter(
                from_airport_code__icontains=search_query
            ) | queryset.filter(
                to_airport_code__icontains=search_query
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add counts for dashboard stats
        user_shipments = Shipment.objects.filter(user=self.request.user)
        
        # Get status counts
        status_counts = user_shipments.values('status').annotate(count=Count('status'))
        
        # Initialize counters
        total_count = user_shipments.count()
        pending_count = 0
        in_transit_count = 0
        delivered_count = 0
        
        # Fill counts from query results
        for status in status_counts:
            if status['status'] in ['pending', 'processing']:
                pending_count += status['count']
            elif status['status'] in ['in_transit', 'out_for_delivery']:
                in_transit_count += status['count']
            elif status['status'] == 'delivered':
                delivered_count += status['count']
        
        # Add to context
        context['total_count'] = total_count
        context['pending_count'] = pending_count
        context['in_transit_count'] = in_transit_count
        context['delivered_count'] = delivered_count
        
        # Add filter values to maintain state
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['current_date_range'] = self.request.GET.get('date_range', '7')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context

class TrackView(TemplateView):
    template_name = "tracking.html"

class ViewShipment(TemplateView):
    template_name = "view_shipment.html"
    def get_context_data(self, **kwargs):
        id=kwargs.get('pk')
        context = super().get_context_data(**kwargs)
        context['shipment']=Shipment.objects.get(id=id)
        return context