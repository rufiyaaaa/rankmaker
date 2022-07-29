from django.urls import path

from . import views

app_name = 'entrance'
urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('rating-system', views.RatingSystemView.as_view(), name="rating_system"),
    path('inquiry/', views.InquiryView.as_view(), name="inquiry"),
]
