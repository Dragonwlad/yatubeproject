# core/tests/test_views.py
from django.test import TestCase, Client
from http import HTTPStatus


class PostUrlTest(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """Ошибка 404 выдает кастомный шаблон."""
        response = self.guest_client.get('noadress/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_http_responce(self):
        """Переход на несуществующую страницу выдает HTTPStatus 404"""
        response = self.guest_client.get('noadress/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
