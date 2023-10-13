import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client, TestCase, override_settings

from ..models import Comment, Post, Group, User
from ..models import IMAGE_DIRECTORY


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test_slig',
            description='Тест описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def image_create(self, image_name):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name=image_name,
            content=small_gif,
            content_type='image/gif'
        )
        return uploaded

    def test_create_post(self):
        '''Пост создается в базе и происходит redirect'''
        Post.objects.all().delete()
        post_count = Post.objects.count()
        image_name = 'small.gif'
        uploaded_image = self.image_create(image_name)
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded_image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        first_post = Post.objects.first()
        self.assertEqual(first_post.text, form_data['text'])
        self.assertEqual(first_post.group.id, form_data['group'])
        self.assertEqual(
            first_post.image,
            (f'{IMAGE_DIRECTORY}{image_name}')
        )

    def test_edit_post(self):
        '''Пост редактируется в базе данных и происходит redirect'''
        image_name = 'small_2.gif'
        form_data = {
            'text': 'Новый заголовок',
            'group': self.group.id,
            'image': self.image_create(image_name),
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        modified_post = Post.objects.get(id=self.post.id)
        self.assertEqual(modified_post.text, form_data['text'])
        self.assertEqual(modified_post.group.id, form_data['group'])
        self.assertEqual(modified_post.group.id, form_data['group'])
        self.assertEqual(
            modified_post.image,
            (f'{IMAGE_DIRECTORY}{image_name}')
        )

    def test_comment_create(self):
        '''Комментарий создается в базе и происходит redirect'''
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        first_comment = Comment.objects.first()
        self.assertEqual(first_comment.text, form_data['text'])

    def test_stranger_cant_create_comment(self):
        '''Не авторизованный пользователь не может комментировать'''
        Comment.objects.all().delete()
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
