from django.urls import path

from . import views

app_name = 'multi'
urlpatterns = [
    path('home/', views.HomeView.as_view(), name="home"),
    path('ranking/', views.RankingView.as_view(), name="ranking"),
    path('game-list/', views.GameListView.as_view(), name="game_list"),
    path('game-detail/<int:pk>', views.GameDetailView.as_view(), name="game_detail"),
    path('game-create/', views.GameCreateView.as_view(), name="game_create"),
    path('game-update/<int:pk>/', views.GameUpdateView.as_view(), name="game_update"),
    path('game-delete/<int:pk>/', views.GameDeleteView.as_view(), name="game_delete"),
    # path('duel-update/<int:pk>/', views.DuelUpdateView.as_view(), name="duel_update"),
    path('player-list/', views.PlayerListView.as_view(), name="player_list"),
    path('player-detail/<int:pk>', views.PlayerDetailView.as_view(), name="player_detail"),
    path('player-create/', views.PlayerCreateView.as_view(), name="player_create"),
    path('player-update/<int:pk>/', views.PlayerUpdateView.as_view(), name="player_update"),
    path('player-delete/<int:pk>/', views.PlayerDeleteView.as_view(), name="player_delete"),
    path('team-create/', views.TeamCreateView.as_view(), name="team_create"),
    path('team-config/', views.TeamConfigView.as_view(), name="team_config"),
    path('team-delete/<int:pk>', views.TeamDeleteView.as_view(), name="team_delete"),
    path('notice-list/', views.NoticeListView.as_view(), name="notice_list"),
    path('notice/<int:pk>', views.NoticeDetailView.as_view(), name="notice"),
]
