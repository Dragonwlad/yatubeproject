from django.shortcuts import render
# Create your views here.

def index(request):
    template = 'posts\index.html'
    title = 'yatube для друей тайтл'
    context = {
        'title': title,
        'text': 'Главная страница',
        'slug_id': 'cats',
    }
    return render(request, template, context)

def group_posts(request):
    title = 'yatube группы'
    context = {
        'title': title,
        'text': 'Здесь будет информация о группах проекта Yatube',
    }
    template = 'posts\group_posts.html'
    return render(request, template, context)

def groups(request, slug):
    template = 'posts\group_name.html'
    #title = 'Страница с постами отфильтроваными по группам'
    return render(request, template)
   #return HttpResponse(f'Группа -{slug}-')
