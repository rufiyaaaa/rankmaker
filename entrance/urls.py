from django.urls import path

from . import views

app_name = 'entrance'
urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('app_detail', views.AppDetailView.as_view(), name="app_detail"),
    path('inquiry/', views.InquiryView.as_view(), name="inquiry"),
]
