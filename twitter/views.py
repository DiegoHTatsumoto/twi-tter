from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import User, Post, Comment, Like, Follow

def login_view(request):
    if request.user.is_authenticated: #se ja estiver logado, ele retorna e vai direto ao feed
        return redirect('feed')
    
    if request.method == 'POST': #aqui se a pessoa tiver se cadastrado, ela tenta encontrar os dados para ver se coencidem
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None: #ele vai ao feed
            login(request, user)
            return redirect('feed')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
    
    if request.method == 'POST': #pega os dados do formulario
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm: #validaçoes
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já existe.')
            return render(request, 'register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email já cadastrado.')
            return render(request, 'register.html')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, 'Conta criada com sucesso!')
        return redirect('feed')
    
    return render(request, 'register.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def feed_view(request):
    following_users = request.user.following.values_list('following', flat=True)
    posts = Post.objects.filter(
        Q(user__in=following_users) | Q(user=request.user)
    ).select_related('user').prefetch_related('likes', 'comments')

    for post in posts:
        post.liked = post.is_liked_by(request.user)
    
    users_to_follow = User.objects.exclude(
        id__in=list(following_users) + [request.user.id]
    ).order_by('?')[:3]

    context = {
        'posts': posts,
        'user': request.user,
        'users_to_follow': users_to_follow,
    }

    return render(request, 'feed.html', context)

@login_required
def create_post_view(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        if content:
            Post.objects.create(user=request.user, content=content, image=image)
            messages.success(request, 'Post criado com sucesso!')
        else:
            messages.error(request, 'O conteúdo não pode estar vazio.')
    
    return redirect('feed')

@login_required
def like_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.is_liked_by(request.user):
        Like.objects.filter(user=request.user, post=post).delete()
    else:
        Like.objects.create(user=request.user, post=post)
    
    return redirect(request.META.get('HTTP_REFERER', 'feed'))

@login_required
def comment_post_view(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get('content')
        
        if content:
            Comment.objects.create(user=request.user, post=post, content=content)
            messages.success(request, 'Comentário adicionado!')
        else:
            messages.error(request, 'O comentário não pode estar vazio.')
    
    return redirect(request.META.get('HTTP_REFERER', 'feed'))

@login_required
def delete_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.user == request.user:
        post.delete()
        messages.success(request, 'Post deletado com sucesso!')
    else:
        messages.error(request, 'Você não tem permissão para deletar este post.')
    
    return redirect(request.META.get('HTTP_REFERER', 'feed'))

@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=profile_user)
    is_following = request.user.is_following(profile_user) if request.user != profile_user else False
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'followers_count': profile_user.get_followers_count(),
        'following_count': profile_user.get_following_count(),
    }
    return render(request, 'profile.html', context)

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        user = request.user
        
        # Atualizar nome
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        bio = request.POST.get('bio')
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if bio:
            user.bio = bio
        
        # Atualizar foto de perfil
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        # Atualizar senha
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')
        
        if current_password and new_password:
            if user.check_password(current_password):
                if new_password == new_password_confirm:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Senha alterada! Faça login novamente.')
                    logout(request)
                    return redirect('login')
                else:
                    messages.error(request, 'As novas senhas não coincidem.')
                    return render(request, 'edit_profile.html')
            else:
                messages.error(request, 'Senha atual incorreta.')
                return render(request, 'edit_profile.html')
        
        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('profile', username=user.username)
    
    # Se for apenas um GET (abrir a página), renderiza o template
    return render(request, 'edit_profile.html')

@login_required
def follow_user_view(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    
    if user_to_follow == request.user:
        messages.error(request, 'Você não pode seguir a si mesmo.')
        return redirect('profile', username=username)
    
    if request.user.is_following(user_to_follow):
        Follow.objects.filter(follower=request.user, following=user_to_follow).delete()
        messages.success(request, f'Você deixou de seguir {username}.')
    else:
        Follow.objects.create(follower=request.user, following=user_to_follow)
        messages.success(request, f'Você agora está seguindo {username}.')
    
    return redirect(request.META.get('HTTP_REFERER', 'profile'))

@login_required
def followers_view(request, username):
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    context = {
        'profile_user': user,
        'followers': followers,
    }
    return render(request, 'followers.html', context)

@login_required
def following_view(request, username):
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')
    
    context = {
        'profile_user': user,
        'following': following,
    }
    return render(request, 'following.html', context)