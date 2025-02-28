from django.shortcuts import render,redirect,get_object_or_404
from django.views.generic import TemplateView
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from main.models import *
from main.forms import *
import uuid
from datetime import datetime, timedelta
import json
from django.http import JsonResponse,HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db.models import ProtectedError
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

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
            to_airport_code = request.POST.get("to_airport")
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
            messages.success(request, 'Shipment created successfully!')
            return redirect('my')

        except Address.DoesNotExist:
            messages.error(request, "Invalid address selection.")
        except ValueError:
            messages.error(request, "Invalid weight value.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    international = InternationalAirports.objects.all()
    domestic = DomesticAirports.objects.all()
    addresses = Address.objects.filter(user=request.user)

    context = {
        'international': international,
        'domestic': domestic,
        'addresses': addresses,
    }
    return render(request, 'shipment.html', context)



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



class MyShipmentView(LoginRequiredMixin, ListView):
    template_name = "myshipments.html"
    context_object_name = "shipments"
    paginate_by = 10
    
    def get_queryset(self):
        # Get shipments for the logged-in user
        queryset = Shipment.objects.filter(user=self.request.user).exclude(status='cancelled').order_by('-created_at')
        
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
        user_shipments = Shipment.objects.filter(user=self.request.user).exclude(status="cancelled")
        
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


class ShipmentHistoryView(LoginRequiredMixin, ListView):
    template_name = "history.html"
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

def shipment_details(request, pk):
    shipment = get_object_or_404(Shipment, id=pk, user=request.user)
    payment_exists = Payment.objects.filter(shipment=shipment, status='completed').exists()
    
    context = {
        'shipment': shipment,
        'payment_exists': payment_exists
    }
    
    return render(request, 'view_shipment.html', context)
    
    
def edit_shipment(request, tracking_number):
    # Fetch the shipment based on tracking number
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number)

    # Fetch addresses and airports for the dropdown
    addresses = Address.objects.all()
    domestic_airports = DomesticAirports.objects.all()  # Adjust according to your model
    international_airports = InternationalAirports.objects.all()  # Adjust according to your model

    # If the form is submitted (POST request)
    if request.method == 'POST':
        # Handle the form submission and validate
        sender_address = request.POST.get('sender_address')
        recipient_address = request.POST.get('recipient_address')
        shipment_type = request.POST.get('shipment_type')
        weight = request.POST.get('weight')
        shipping_speed = request.POST.get('shipping_speed')
        notes = request.POST.get('notes')

        # Domestic or International airport data
        if shipment_type == 'domestic':
            from_airport = request.POST.get('from_airport_domestic')
            to_airport = request.POST.get('to_airport_domestic')
        else:
            from_airport = request.POST.get('from_airport_international')
            to_airport = request.POST.get('to_airport_international')

        # Update the shipment instance with the new data
        shipment.sender_address = get_object_or_404(Address, id=sender_address)
        shipment.recipient_address = get_object_or_404(Address, id=recipient_address)
        shipment.shipment_type = shipment_type
        shipment.weight = weight
        shipment.shipping_speed = shipping_speed
        shipment.notes = notes
        shipment.from_airport_code = from_airport
        shipment.to_airport_code = to_airport

        # Save the updated shipment data
        shipment.save()

        # Add a success message and redirect to shipment detail page
        messages.success(request, 'Shipment updated successfully!')
        return redirect('shipment_view', shipment.id)

    # If it's a GET request, render the form with the current shipment data
    return render(request, 'edit_shipment.html', {
        'shipment': shipment,
        'addresses': addresses,
        'domestic': domestic_airports,
        'international': international_airports,
    })
    
    
def track_shipment(request):
    tracking_number = request.GET.get('tracking_number', '').strip()
    history = TrackingSearchHistory.objects.filter(user=request.user)
    if tracking_number:
        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
            if shipment.status == 'cancelled':
                messages.error(request, "Please enter a valid tracking number.")
                return redirect('track')
            TrackingSearchHistory.objects.get_or_create(user=request.user,shipment=shipment)
            tracking_updates = ShipmentTrackingUpdate.objects.filter(shipment=shipment).all()
            context = {
                'shipment': shipment,
                'tracking_updates': tracking_updates,
                'tracking_number': tracking_number
            }
            return render(request, 'tracking.html', context)
        except Shipment.DoesNotExist:
            messages.error(request, "Please enter a valid tracking number.")
            return render(request, 'tracking.html', {'history':history})
    else:
        messages.error(request, "Please enter a valid tracking number.")
        return render(request, 'tracking.html', {'history':history})
    

def track_shipment_my(request,tracking_number):
    if tracking_number:
        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
            if shipment.status == 'cancelled':
                messages.error(request, "Please enter a valid tracking number.")
                return redirect('track')
            TrackingSearchHistory.objects.get_or_create(user=request.user,shipment=shipment)
            tracking_updates = ShipmentTrackingUpdate.objects.filter(shipment=shipment).all()
            context = {
                'shipment': shipment,
                'tracking_updates': tracking_updates,
                'tracking_number': tracking_number
            }
            return render(request, 'tracking.html', context)
        except Shipment.DoesNotExist:
            messages.error(request, "Please enter a valid tracking number.")
            return render(request, 'tracking.html', {})
    else:
        messages.error(request, "Please enter a valid tracking number.")
        return render(request, 'tracking.html', {})
    

@login_required
def address_book(request):
    """View to display all addresses for the current user"""
    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()
    
    context = {
        'addresses': addresses,
        'default_address': default_address,
    }
    return render(request, 'address.html', context)

@login_required
def add_address(request):
    """View to add a new address"""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is set as default, unset any existing default
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
                
            address.save()
            return redirect('add')
    else:
        form = AddressForm()
    
    return render(request, 'add_form.html', {'form': form, 'title': 'Add New Address'})

@login_required
def edit_address(request, address_id):
    """View to edit an existing address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            # If this is set as default, unset any existing default
            if form.cleaned_data.get('is_default'):
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
                
            form.save()
            return redirect('add')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'add_form.html', {
        'form': form, 
        'title': 'Edit Address',
        'address': address
    })




@login_required
def delete_address(request, address_id):
    """View to delete an address, handling ProtectedError"""
    address = get_object_or_404(Address, id=address_id, user=request.user)

    try:
        address.delete()
        messages.success(request, "Address deleted successfully.")
    except ProtectedError:
        messages.error(request, "Cannot delete this address because it is linked to an active shipment.")

    return redirect('add')

@login_required
def set_default_address(request, address_id):
    """View to set an address as default"""
    if request.method == 'POST':
        # First, unset any existing default address
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # Set the selected address as default
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.is_default = True
        address.save()
        
    return redirect('add')
from django.urls import reverse


client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def payment_page(request, tracking_number):
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    
    # Check if already paid
    if Payment.objects.filter(shipment=shipment, status='completed').exists():
        return redirect('view_receipt', tracking_number=tracking_number)
    
    # Calculate amount (in paise - Razorpay uses smallest currency unit)
    amount = int(float(shipment.shipping_cost) * 100)
    
    # Create Razorpay order
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': f'receipt_{tracking_number}',
        'notes': {
            'Shipping_ID': tracking_number,
            'Customer': request.user.email
        }
    }
    
    # Create Razorpay Order
    order = client.order.create(data=order_data)
    
    # Save to database
    payment, created = Payment.objects.get_or_create(
        shipment=shipment,
        defaults={
            'amount': float(shipment.shipping_cost),
            'order_id': order['id'],
            'status': 'pending'
        }
    )
    
    # If not created, update the order ID
    if not created:
        payment.order_id = order['id']
        payment.status = 'pending'
        payment.save()
    
    context = {
        'shipment': shipment,
        'order_id': order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': amount,
        'currency': 'INR',
        'callback_url': request.build_absolute_uri(reverse('payment_callback')),
        'user_email': request.user.email,
        'user_name': f"{request.user.name} ",
        'user_phone': request.user.phone if hasattr(request.user, 'profile') else ''
    }
    
    return render(request, 'payment_page.html', context)

@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        # Verify signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
            
            # Update payment status
            payment = Payment.objects.get(order_id=order_id)
            payment.payment_id = payment_id
            payment.status = 'completed'
            payment.save()
            
            # Create receipt
            shipment = payment.shipment
            ship = Shipment.objects.get(id=shipment)
            ship.is_paid = True
            ship.save()
            receipt = Receipt.objects.create(
                payment=payment,
                shipment=shipment,
                amount=payment.amount,
                transaction_id=payment_id
            )
            
            # Redirect to receipt page
            return redirect('view_receipt', tracking_number=shipment.tracking_number)
        except:
            # Failed verification
            return redirect('payment_failed', tracking_number=payment.shipment.tracking_number)
    
    return HttpResponse("Invalid request", status=400)

@login_required
def payment_failed(request, tracking_number):
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    return render(request, 'payment_failed.html', {'shipment': shipment})

@login_required
def view_receipt(request, tracking_number):
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    
    try:
        payment = Payment.objects.get(shipment=shipment, status='completed')
        receipt = Receipt.objects.get(payment=payment)
    except (Payment.DoesNotExist, Receipt.DoesNotExist):
        return redirect('payment_page', tracking_number=tracking_number)
    
    context = {
        'shipment': shipment,
        'payment': payment,
        'receipt': receipt
    }
    
    return render(request, 'receipt.html', context)

@login_required
def download_receipt(request, tracking_number):
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    
    try:
        payment = Payment.objects.get(shipment=shipment, status='completed')
        receipt = Receipt.objects.get(payment=payment)
    except (Payment.DoesNotExist, Receipt.DoesNotExist):
        return redirect('payment_page', tracking_number=tracking_number)
    
    # Generate PDF receipt here (using a library like ReportLab or WeasyPrint)
    # For this example, we'll just return a rendered HTML template
    context = {
        'shipment': shipment,
        'payment': payment,
        'receipt': receipt,
        'for_pdf': True
    }
    
    return render(request, 'receipt_pdf.html', context)


@login_required
def cancel_shipment(request, tracking_number):
    """View to handle shipment cancellation."""
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    
    # Check if shipment is already canceled or delivered
    if shipment.status == 'cancelled':
        messages.error(request, "This shipment has already been cancelled.")
        return redirect('shipment_detail', tracking_number=tracking_number)
    
    if shipment.status == 'delivered':
        messages.error(request, "Cannot cancel a shipment that has already been delivered.")
        return redirect('shipment_detail', tracking_number=tracking_number)
    
    # Display the cancellation form
    if request.method == 'GET':
        return render(request, 'cancel_shipment.html', {
            'shipment': shipment
        })
    
    # Process the cancellation
    elif request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason')
        other_reason = request.POST.get('other_reason', '')
        
        # Store the cancellation reason
        if cancel_reason == 'other' and other_reason:
            reason_text = other_reason
        else:
            # Map the reason codes to human-readable text
            reason_mapping = {
                'mistake': 'Created by mistake',
                'other_service': 'Using different shipping service',
                'delayed': 'Shipment delayed too long',
                'changed_mind': 'Changed my mind',
                'address_error': 'Address error',
                'other': 'Other reason'
            }
            reason_text = reason_mapping.get(cancel_reason, 'Unspecified reason')
        
        # Record cancellation fee if applicable
        cancellation_fee = 0
        if shipment.status in ['in_transit', 'out_for_delivery']:
            # Apply a cancellation fee for shipments already in transit
            # Calculate based on shipping cost and status
            if shipment.status == 'in_transit':
                cancellation_fee = shipment.shipping_cost * 0.5  # 50% fee
            else:  # out_for_delivery
                cancellation_fee = shipment.shipping_cost * 0.75  # 75% fee
        
        # Update shipment status
        shipment.status = 'cancelled'
        shipment.cancellation_reason = reason_text
        shipment.cancellation_date = timezone.now()
        shipment.cancellation_fee = cancellation_fee
        shipment.save()
        
        # Send notification (can be implemented as needed)
        # notify_shipment_cancelled(shipment)
        
        messages.success(request, f"Shipment {tracking_number} has been successfully cancelled.")
        return redirect('shipment_list')
    
    
@login_required
def delete_shipment(request, tracking_number):
    """Process shipment cancellation and redirect to appropriate page."""
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    
    # Check if shipment can be deleted (only pending or cancelled shipments)
    if shipment.status not in ['pending', 'cancelled']:
        messages.error(request, "Only pending or cancelled shipments can be deleted.")
        return redirect('shipment_detail', tracking_number=tracking_number)
    
    if request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason')
        other_reason = request.POST.get('other_reason', '')
        
        # Store cancellation reason before deletion if needed for records
        if cancel_reason == 'other' and other_reason:
            reason_text = other_reason
        else:
            reason_mapping = {
                'mistake': 'Created by mistake',
                'other_service': 'Using different shipping service',
                'delayed': 'Shipment delayed too long',
                'changed_mind': 'Changed my mind',
                'address_error': 'Address error',
                'other': 'Other reason'
            }
            reason_text = reason_mapping.get(cancel_reason, 'Unspecified reason')
        
        # You could log the deletion in a separate model if needed
        # ShipmentLog.objects.create(
        #     tracking_number=shipment.tracking_number,
        #     user=request.user,
        #     action="deletion",
        #     reason=reason_text
        # )
        
        # Delete the shipment
        shipment.status="cancelled"
        shipment.save()
        
        messages.success(request, f"Shipment {tracking_number} has been successfully deleted.")
        return redirect('my')
    
    # If not POST, redirect to the cancel page
    return redirect('cancel_shipment', tracking_number=tracking_number)


@login_required
def review_list(request):
    """View to display the user's reviews and all public reviews"""
    user_reviews = Review.objects.filter(user=request.user)
    recent_reviews = Review.objects.exclude(user=request.user)[:5]
    
    context = {
        'user_reviews': user_reviews,
        'recent_reviews': recent_reviews,
    }
    
    return render(request, 'review.html', context)

@login_required
def add_review(request):
    """View to add a new review"""
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been submitted successfully!')
            return redirect('review_list')
    else:
        form = ReviewForm()
    
    return render(request, 'edit_review.html', {'form': form})

@login_required
def edit_review(request, review_id):
    """View to edit an existing review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated successfully!')
            return redirect('review_list')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'edit_review.html', {'form': form, 'review': review})


@login_required
def delete_review(request, review_id):
    """View to delete a review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted successfully!')
        return redirect('review_list')
    
    return render(request, 'delete_review.html', {'review': review})