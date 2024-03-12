
from django.urls import path
from rest.views import search_controller, admin_controller, update_data_solr_controller

urlpatterns = [
    path('api/search', search_controller),
    path('api/crawler/info', admin_controller),
    path('api/crawler/start', admin_controller),
    path('api/crawler/stop', admin_controller),
    path('api/solr/update', update_data_solr_controller)
]
