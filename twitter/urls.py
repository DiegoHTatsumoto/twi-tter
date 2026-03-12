from django.urls import path
from . import views

urlpatterns = [
    # Autenticação
    path('', views.login_view, name='login'),
    path('registro/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Feed e Postagens
    path('feed/', views.feed_view, name='feed'),
    path('post/criar/', views.create_post_view, name='create_post'),
    path('post/<int:post_id>/curtir/', views.like_post_view, name='like_post'),
    path('post/<int:post_id>/comentar/', views.comment_post_view, name='comment_post'),
    path('post/<int:post_id>/deletar/', views.delete_post_view, name='delete_post'),
    
    # Perfil
    path('perfil/editar/', views.edit_profile_view, name='edit_profile'),
    path('perfil/<str:username>/', views.profile_view, name='profile'),
    
    # Seguir/Deixar de seguir
    path('usuario/<str:username>/seguir/', views.follow_user_view, name='follow_user'),
    path('usuario/<str:username>/seguidores/', views.followers_view, name='followers'),
    path('usuario/<str:username>/seguindo/', views.following_view, name='following'),
]