from django.shortcuts import render, get_object_or_404
from .models import Post, Group
# Create your views here.


def index(request):
    posts = Post.objects.order_by('-pub_date')[:10]
    #group = Group.objects.all()
    template = 'posts\index.html'
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
        'text': 'Главная страница',
        'slug_id': 'cats',
        'posts': posts,
       # 'group': group,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by('-pub_date')[:10]
    title = 'Записи сообщества'
    context = {
        'title': title,
        'group': group,
        'posts': posts,
        'slug': slug,
    }
    template = 'posts\group_list.html'
    return render(request, template, context)


def groups(request):
    template = 'posts\group_posts.html'
    groups = Group.objects.all()
    title = 'Список групп'
    context = {
        'title': title,
        'groups': groups,
    }
    return render(request, template, context)
   #return HttpResponse(f'Группа -{slug}-')
