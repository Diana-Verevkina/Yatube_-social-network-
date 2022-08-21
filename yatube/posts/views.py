from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow
from .utils import pages

User = get_user_model()


def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = pages(request, post_list)
    contex = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', contex)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = pages(request, post_list)
    contex = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', contex)


def profile(request, username):
    selected_user = get_object_or_404(User, username=username)
    user_posts = selected_user.posts.select_related('group').all()
    page_obj = pages(request, user_posts)
    post_count = user_posts.count()
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        'author': selected_user,
        'post_count': post_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    Post.objects.filter(id=post_id).delete()
    return render(request, 'posts/delete_post.html')


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = pages(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    redirect_page = redirect('posts:profile', username=username)
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect_page
    follower = Follow.objects.filter(user=request.user, author=author)
    if follower:
        return redirect_page
    Follow.objects.create(user=request.user, author=author)
    return redirect_page


@login_required
def profile_unfollow(request, username):
    redirect_page = redirect('posts:profile', username=username)
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect_page
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect_page
