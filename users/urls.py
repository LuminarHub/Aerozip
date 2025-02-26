from django.urls import path
from .views import *

urlpatterns =[
    path('user-home/',UserHomeView.as_view(),name='uh'),
    path('user-ship/',create_shipment,name='ship'),
    path('user-track/',TrackView.as_view(),name='track'),
    path('my-shipments/',MyShipmentView.as_view(),name='my'),
    path('user-address/',add_address,name='address'),
    path('shipments/<int:pk>/',ViewShipment.as_view(),name='shipment_view'),
]