from django.contrib import admin
from .models import Team, Affiliation, Player, Game, Duel, Participant, Rating, Notice
# Register your models here.


admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Game)
admin.site.register(Duel)
admin.site.register(Participant)
admin.site.register(Rating)
admin.site.register(Affiliation)
admin.site.register(Notice)
