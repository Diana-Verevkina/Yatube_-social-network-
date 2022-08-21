import os
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.group2 = Group.objects.create(
            title='Тестовое название 2 группы',
            slug='test_slug2',
            description='Тестовое описание 2 группы',
        )
        # Создаем автора поста
        cls.author_user = User.objects.create_user(
            username='post_author'
        )
        cls.post = Post.objects.create(
            text='рандомный текст',
            author=cls.author_user,
            group=cls.group,
        )
        cls.form = PostForm()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        print(os.path.abspath('small.gif'))

    def setUp(self):
        self.post_author_client = Client()
        self.post_author_client.force_login(self.author_user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Очистим базу данных
        if Post.objects.count() > 0:
            Post.objects.all().delete()
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        # Отправляем POST-запрос
        response = self.post_author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись
        self.assertTrue(
            Post.objects.filter(
                text='Текст',
                group=self.group,
            ).exists()
        )
        self.assertTrue(Post.objects.first().image)
        post = Post.objects.filter(text='Текст', group=self.group).first()
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': self.group2.id,
        }
        # Отправляем POST-запрос
        response = self.post_author_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])

        response = self.post_author_client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            len(response.context['page_obj']), 0
        )

    def test_guest_client_cannot_create_post(self):
        """Неавторизованный пользователь не может создать пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост от неавторизованного клиента',
            'group': self.group.id,
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
