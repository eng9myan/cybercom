from django.urls import path

from products.cycom.livechat import views

urlpatterns = [
    path("<slug:slug>/sessions/", views.public_session_create, name="livechat-public-session-create"),
    path("<slug:slug>/sessions/<str:token>/messages/", views.public_messages, name="livechat-public-messages"),
]
