
from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path('all/', views.all_polls, name='all'),
    path('<int:question_id>/frequency/', views.frequency, name='frequency'),
    path('statistics/', views.statistics, name='statistics'),
    path('create/', views.create_question, name='create'),

# API REST
    path('api/questions/', views.QuestionListAPIView.as_view(), name='api-questions'),
    path('api/questions/<int:question_id>/vote/', views.VoteAPIView.as_view(), name='api-vote'),
]