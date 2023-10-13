from django.utils import timezone


def year(request):
    date = timezone.now()
    date = date.year

    return {
        'year': date,
    }
