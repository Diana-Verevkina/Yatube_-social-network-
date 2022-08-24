from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
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
        cls.url_clients = (
            ('posts:index', None, '/'),
            ('posts:group_posts', (cls.group.slug,),
             f'/group/{cls.group.slug}/'),
            ('posts:profile', (cls.author_user.username,),
             f'/profile/{cls.author_user.username}/'),
            ('posts:post_detail', (cls.post.id,), f'/posts/{cls.post.id}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit', (cls.post.id,),
             f'/posts/{cls.post.id}/edit/'),
            ('posts:add_comment', (cls.post.id,),
             f'/posts/{cls.post.id}/comment/'),
            ('posts:follow_index', None,
             '/follow/'),
            ('posts:profile_follow', (cls.author_user.username,),
             f'/profile/{cls.author_user.username}/follow/'),
            ('posts:profile_unfollow', (cls.author_user.username,),
             f'/profile/{cls.author_user.username}/unfollow/'),
            ('posts:post_delete', (cls.post.id,),
             f'/posts/{cls.post.id}/delete/'),

        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(self.author_user)

    def test_error_404(self):
        """Переход по неизвестному адресу вернет ошибку 404."""
        response = self.authorized_client.get('/error_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template(self):
        """Страницы используют корректные шаблоны."""
        url_templates_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_posts', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.author_user.username,),
             'posts/profile.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
            ('posts:post_delete', (self.post.id,), 'posts/delete_post.html'),
        )
        for address, arg, template in url_templates_names:
            with self.subTest(address=address):
                response = self.post_author_client.get(
                    reverse(address, args=arg)
                )
                self.assertTemplateUsed(response, template)

    def test_urls_reverse(self):
        """Тестирование реверсов с имен на хард урл"""
        for address, arg, hard_url in self.url_clients:
            with self.subTest(address=address):
                self.assertEqual(reverse(address, args=arg), hard_url)

    def test_access_for_guest_client(self):
        """Реверс гостевого клиента для добавления, редактирования и
        удаления поста."""
        reverse_login = reverse('users:login')
        for address, arg, hard_url in self.url_clients:
            with self.subTest(address=address):
                reverse_name = reverse(address, args=arg)
                response = self.client.get(reverse(address, args=arg))
                if address in ('posts:post_edit', 'posts:post_create',
                               'posts:post_delete', 'posts:add_comment',
                               'posts:follow_index', 'posts:profile_follow',
                               'posts:profile_unfollow'):
                    self.assertRedirects(
                        response, f'{reverse_login}?next={reverse_name}'
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_for_authorized_client(self):
        """Реверс авторизованного клиента для редактирования поста."""
        for address, arg, hard_url in self.url_clients:
            with self.subTest(address=address):
                response = self.authorized_client.get(
                    reverse(address, args=arg)
                )
                if address in ('posts:post_edit', 'posts:add_comment'):
                    reverse_post_detail = reverse('posts:post_detail',
                                                  args=arg)
                    self.assertRedirects(response, reverse_post_detail)
                elif address in ('posts:profile_follow',
                                 'posts:profile_unfollow'):
                    reverse_profile = reverse('posts:profile', args=arg)
                    self.assertRedirects(response, reverse_profile)
                elif address != 'posts:post_delete':
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_for_author_client(self):
        """Авторизованному пользователю - автору постов доступны все адреса."""
        for address, arg, hard_url in self.url_clients:
            with self.subTest(address=address):
                response = self.post_author_client.get(
                    reverse(address, args=arg)
                )
                if address not in ('posts:add_comment',
                                   'posts:profile_follow',
                                   'posts:profile_unfollow'):
                    self.assertEqual(response.status_code, HTTPStatus.OK)
