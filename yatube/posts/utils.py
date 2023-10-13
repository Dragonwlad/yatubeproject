from django.core.paginator import Paginator
from django.conf import settings


def get_paginator_pages(posts, request):
    '''Получает posts и request, возвращает пагинатор с текущей страницей'''
    paginator = Paginator(posts, settings.POST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
