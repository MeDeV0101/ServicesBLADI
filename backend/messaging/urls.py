from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('chat/<int:request_id>/', views.chat_view, name='chat'),
] 