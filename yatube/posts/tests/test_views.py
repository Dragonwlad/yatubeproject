# posts/tests/test_views.py
import shutil
import tempfile

from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Comment, Group, Post, User, Follow
from ..forms import CommentForm, PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_follower = User.objects.create_user(
            username='test_user_follower')
        cls.user_no_follower = User.objects.create_user(
            username='test_user__no_follower')
        cls.group = Group.objects.create(
            title='тестовая группа 1',
            slug='test_slig',
            description='Тест описание'
        )
        cls.group_2 = Group.objects.create(
            title='тестовая группа 2',
            slug='test_slig_2',
            description='Тест описание_2'
        )
        cls.image_name = 'small.gif'
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name=cls.image_name,
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text=('Тестовый пост'),
            author=cls.user,
            group=cls.group,
            image=image
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=False)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names_with_html = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': f'{self.user.username}'}),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/follow.html': reverse('posts:follow_index'),
        }
        for template, reverse_name in templates_url_names_with_html.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_form_context(self, view):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(view)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)
                form_value = form.fields.get(value)
                self.assertIsInstance(form_value, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        self.check_form_context(reverse('posts:post_create'))

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        self.check_form_context(reverse('posts:post_edit',
                                        kwargs={'post_id': self.post.id}))

    def page_show_correct_context(self, response, page_obj: bool = True):
        """Шаблон сформирован с правильным контекстом."""
        if page_obj:
            page_context = response.context.get('page_obj')
            self.assertIsInstance(page_context, Page)
            self.assertTrue(page_context)
            post = page_context[0]
        else:
            post = response.context.get('post')
        # Тестирование постов
        self.assertIsInstance(post, Post)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон posts:index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.page_show_correct_context(response)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        # Тестирование постов в контексте
        response = (self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}))
        )
        self.page_show_correct_context(response, page_obj=False)
        # Тестирование комментария
        comments = response.context.get('comments')
        self.assertTrue(comments)
        for comment in comments:
            self.assertIsInstance(comment, Comment)
            self.assertEqual(comment, self.comment)
            self.assertEqual(comment.text, self.comment.text)
            self.assertEqual(comment.author, self.comment.author)
            self.assertEqual(comment.pub_date, self.comment.pub_date)
        # Тестирование формы комментариев
        form = response.context.get('form')
        self.assertIsInstance(form, CommentForm)
        form_value = form.fields.get('text')
        self.assertIsInstance(form_value, forms.fields.CharField)

    # Тестирование Group
    def test_post_created_in_group(self):
        """Пост попал в posts:group_list"""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        )
        post_group = response.context.get('group')
        self.assertEqual(post_group, self.group)
        self.page_show_correct_context(response)

    def test_post_created_in_profile(self):
        """Пост попал в posts:profile"""
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        self.assertEqual(
            response.context.get('author'),
            self.user
        )
        self.page_show_correct_context(response)

    def test_post_not_created_in_another_group(self):
        """Пост не попал в другую группу posts:group_list"""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group_2.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_follower = User.objects.create_user(
            username='test_user_follower')
        cls.user_no_follower = User.objects.create_user(
            username='test_user__no_follower')
        cls.post = Post.objects.create(
            text=('Тестовый пост'),
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.user_follower)
        self.authorized_client_no_follower = Client()
        self.authorized_client_no_follower.force_login(self.user_no_follower)

    # Тестирование Follow
    def test_post_created_follow_page(self):
        """Новая запись пользователя появилась в ленте того кто подписан
        на автора"""
        Follow.objects.create(user=self.user_follower, author=self.user)
        post_follow = Post.objects.create(
            text=('Тестовый пост для фолловера'),
            author=self.user,
        )
        response = self.authorized_client_follower.get(reverse(
            'posts:follow_index'))
        self.assertIn(post_follow, response.context['page_obj'])

    def test_post_not_created_follow_page(self):
        """Новая запись пользователя не появилась в
        ленте того кто не подписан на автора"""
        Follow.objects.create(user=self.user_follower, author=self.user)
        post_follow = Post.objects.create(
            text=('Тестовый пост для фолловера'),
            author=self.user,
        )
        response = self.authorized_client_no_follower.get(reverse(
            'posts:follow_index'))
        self.assertNotIn(post_follow, response.context['page_obj'])

    def test_following_user(self):
        """Пользователь подписался на другого пользователя"""
        Follow.objects.all().delete()
        follow_count = Follow.objects.count()
        response = self.authorized_client_follower.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}),
            follow=True,
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user_follower,
            author=self.user).exists())

    def test_unfollow_user(self):
        """Пользователь отписался от другого пользователя"""
        Follow.objects.all().delete()
        Follow.objects.create(
            user=self.user_follower,
            author=self.user)
        follow_count = Follow.objects.count()
        response = self.authorized_client_follower.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user.username}),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_yourself(self):
        """Пользователь не может подписаться на себя"""
        Follow.objects.all().delete()
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}),
            follow=True,
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_twice(self):
        """Пользователь не может подписаться дважды"""
        Follow.objects.all().delete()
        self.authorized_client_follower.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}),
            follow=True,
        )
        follow_count = Follow.objects.count()
        self.authorized_client_follower.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        self.assertEqual(follow_count, Follow.objects.count())

    # Тестирование кэша
    def test_cache_index(self):
        response_cache = self.guest_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_cache.content, response.content)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_cache.content, response.content)


class PaginatorViewsTest(TestCase):
    '''Тестирование paginator'''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='тестовая группа 1',
            slug='test_slig',
            description='Тест описание'
        )
        cls.post_on_second_page = 5
        for i in range(settings.POST_ON_PAGE + cls.post_on_second_page):
            cls.post = Post.objects.create(
                text=(f'Тестовый пост {i}'),
                author=cls.user,
                group=cls.group
            )
        cls.urls = (
            (reverse('posts:index')),
            (reverse('posts:group_list', kwargs={'slug': cls.group.slug})),
            (reverse('posts:profile', kwargs={'username': cls.user.username}))
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_contains_ten_records(self):
        '''paginator выдал 10 постов в posts:index, group_list, profile'''
        for view in self.urls:
            with self.subTest(view=view):
                response = self.guest_client.get(view)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POST_ON_PAGE)

    def test_pages_contains_ten_records(self):
        '''paginator выдал оставшиеся посты на 2
         страницу в posts:index, group_list, profile'''
        for view in self.urls:
            with self.subTest(view=view):
                response = self.guest_client.get((view + '?page=2'))
                self.assertEqual(len(response.context['page_obj']),
                                 self.post_on_second_page)
