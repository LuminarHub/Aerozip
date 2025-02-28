from django.urls import path
from .views import *

urlpatterns =[
    path('user-home/',UserHomeView.as_view(),name='uh'),
    path('user-ship/',create_shipment,name='ship'),
    path('user-track/',TrackView.as_view(),name='track'),
    path('my-shipments/',MyShipmentView.as_view(),name='my'),
    path('track/',track_shipment,name='track'),
    path('history/',ShipmentHistoryView.as_view(),name='history'),
    path('track/<str:tracking_number>/',track_shipment_my,name='my-track'),
    path('user-address/',add_address,name='address'),
    path('shipments/<int:pk>/',shipment_details,name='shipment_view'),
    path('edit-ship/<str:tracking_number>/',edit_shipment,name='edit_ship'),
    path('address/',address_book,name='add'),
    path('add_address/',add_address,name='add_address'),
    path('edit_address/<int:address_id>/',edit_address,name='edit_address'),
    path('delete_address/<int:address_id>/',delete_address,name='delete_address'),
    path('set_default_address/<int:address_id>/',set_default_address,name='set_default_address'),
    path('shipment/<str:tracking_number>/payment/', payment_page, name='payment_page'),
    path('payment/callback/', payment_callback, name='payment_callback'),
    path('shipment/<str:tracking_number>/payment/failed/', payment_failed, name='payment_failed'),
    path('shipment/<str:tracking_number>/receipt/', view_receipt, name='view_receipt'),
    path('shipment/<str:tracking_number>/receipt/download/', download_receipt, name='download_receipt'),
    path('shipments/<str:tracking_number>/cancel/', cancel_shipment, name='cancel_shipment'),
    path('shipments/<str:tracking_number>/delete/', delete_shipment, name='delete_shipment'),
]