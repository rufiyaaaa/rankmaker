from django.urls import path

from . import views

app_name = 'duel'
urlpatterns = [
    path('home/', views.HomeView.as_view(), name="home"),
    path('match-list/', views.MatchListView.as_view(), name="match_list"),
    path('match-detail/<int:pk>', views.MatchDetailView.as_view(), name="match_detail"),
    path('match-create/', views.MatchCreateView.as_view(), name="match_create"),
    path('match-update/<int:pk>/', views.MatchUpdateView.as_view(), name="match_update"),
    path('match-delete/<int:pk>/', views.MatchDeleteView.as_view(), name="match_delete"),
    path('player-list/', views.PlayerListView.as_view(), name="player_list"),
    path('player-detail/<int:pk>', views.PlayerDetailView.as_view(), name="player_detail"),
    path('player-create/', views.PlayerCreateView.as_view(), name="player_create"),
    path('player-update/<int:pk>/', views.PlayerUpdateView.as_view(), name="player_update"),
    path('player-delete/<int:pk>/', views.PlayerDeleteView.as_view(), name="player_delete"),
    path('team-create/', views.TeamCreateView.as_view(), name="team_create"),
    path('team-config/', views.TeamConfigView.as_view(), name="team_config"),
]
