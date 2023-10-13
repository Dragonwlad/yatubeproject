import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='тестовая группа(имя)',
            slug='test_slig',
            description='Тест описание'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text=('Тестовый пост'),
            author=cls.user,
            group=cls.group,
            image=cls.uploaded_image,
        )
        cls.templates_public_url_access = {
            '/': 'posts/index.html',
            (f'/group/{cls.group.slug}/'): 'posts/group_list.html',
            (f'/profile/{cls.user.username}/'): 'posts/profile.html',
            (f'/posts/{cls.post.id}/'): 'posts/post_detail.html',
        }
        cls.templates_authorized_url_access = {
            '/create/': 'posts/create_post.html',
            (f'/posts/{cls.post.id}/edit/'): 'posts/create_post.html',
            ('/follow/'): 'posts/follow.html',
        }
        cls.templates_all_url = {**cls.templates_public_url_access,
                                 **cls.templates_authorized_url_access}

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_url_access_non_authorized_client(self):
        """URL-адреса доступные авторизированному пользователю"""
        for url in self.templates_all_url:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_access_authorized_client(self):
        """URL-адреса доступные неавторизированному пользователю"""
        for url in self.templates_public_url_access:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_non_authorized_client(self):
        """Страница /create/ перенаправляет
         неавторизированного пользователя."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_edit_redirect_non_authorized_client(self):
        """Страница /edit/ перенаправляет неавторизированного пользователя."""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_edit_redirect_non_authorized_client(self):
        """Страница /add_comment/ перенаправляет
        неавторизированного пользователя"""
        response = self.guest_client.get(f'/posts/{self.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_edit_redirect_stranger_client(self):
        """Страница /edit/ перенаправляет авторизированого пользователя при
         редактировании чужого поста."""
        user_2 = User.objects.create_user(username='test_user_2')
        authorized_client_2 = Client()
        authorized_client_2.force_login(user_2)
        response = authorized_client_2.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_all_url.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
