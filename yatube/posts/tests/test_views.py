from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, Follow

User = get_user_model()


class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.group2 = Group.objects.create(
            title='Тестовое название второй группы',
            slug='test_slug2',
            description='Тестовое описание второй группы',
        )
        # Создаем автора поста
        cls.author_user = User.objects.create_user(
            username='post_author'
        )
        # Создаем пост от имени post_author
        cls.post2 = Post.objects.create(
            text='рандомный текст',
            author=cls.author_user,
            group=cls.group2,
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='рандомный текст',
            author=cls.author_user,
            group=cls.group,
            image=uploaded,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(self.author_user)

    def not_test(self, response, post=False):
        if post:
            first_object = response.context['post']
        else:
            first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        PostPagesTests.not_test(self, response)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
        )
        PostPagesTests.not_test(self, response)
        group_context = response.context['group']
        self.assertEqual(group_context, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.author_user,))
        )
        PostPagesTests.not_test(self, response)
        group_context = response.context['author']
        self.assertEqual(group_context, self.author_user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      args=(self.post.id,)))
        PostPagesTests.not_test(self, response, True)

    def test_post_create_or_edit_form_correct_context(self):
        """Шаблон post_create/post_edit сформирован с правильным контекстом."""
        url_args = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        for url, arg in url_args:
            with self.subTest(url=url):
                response = self.post_author_client.get(
                    reverse(url, args=arg))
                self.assertIsInstance(response.context['form'], PostForm)
                self.assertIn('form', response.context)

                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value
                                               )
                        self.assertIsInstance(form_field, expected)

    def test_post_group_1_not_contained_in_group_2(self):
        """Пост не попал в группу, для которой не был предназначен."""
        count_group_1 = Post.objects.filter(group=self.group).count()
        count_group_2 = Post.objects.filter(group=self.group2).count()

        Post.objects.create(
            text='рандомный текст',
            author=self.author_user,
            group=self.group2,
        )

        response_not_this_group = self.post_author_client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
        )
        response_this_group = self.post_author_client.get(
            reverse('posts:group_posts', args=(self.group2.slug,))
        )

        self.assertEqual(len(response_not_this_group.context['page_obj']),
                         count_group_1)
        self.assertEqual(len(response_this_group.context['page_obj']),
                         count_group_2 + 1)

    def test_delete_post(self):
        """Удаление поста"""
        # Очистим базу данных
        if Post.objects.count() > 0:
            Post.objects.all().delete()
        posts_count_before = Post.objects.count()
        # Создали пост
        post = Post.objects.create(
            text='Текст поста перед гибелью',
            author=self.author_user,
            group=self.group2,
        )
        # Удалили этот пост
        response = self.post_author_client.post(
            reverse('posts:post_delete', args=(post.id,)),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, что количество постов не изменилось
        self.assertEqual(posts_count_before, Post.objects.count())
        self.assertFalse(Post.objects.filter(text=post.text))


class CommentPosts(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.author_user = User.objects.create_user(
            username='post_author'
        )
        cls.post = Post.objects.create(
            text='рандомный текст',
            author=cls.author_user,
            group=cls.group,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(self.author_user)

    def test_comment_post_may_only_authorized_clients(self):
        """Комментировать посты может только авторизованный пользователь."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post.id,
            'text': 'Тестовый комментарий',
        }
        self.client.post(
            reverse('posts:add_comment', args=(form_data['post'],)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)

        self.authorized_client.post(
            reverse('posts:add_comment', args=(form_data['post'],)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)


class CacheViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.author_user = User.objects.create_user(
            username='post_author'
        )
        cls.post = Post.objects.create(
            text='рандомный текст',
            author=cls.author_user,
            group=cls.group,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(self.author_user)

    def test_cache_index(self):
        """Кеширования главной страницы."""

        if Post.objects.count() > 0:
            Post.objects.all().delete()

        post = Post.objects.create(
            text='Кеширования главной страницы',
            author=self.author_user,
            group=self.group,
        )
        response_1 = self.post_author_client.post(
            reverse('posts:index'),
        )
        post.delete()
        response_2 = self.post_author_client.post(
            reverse('posts:index'),
        )
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()

        response_3 = self.post_author_client.post(
            reverse('posts:index'),
        )

        self.assertNotEqual(response_1.content, response_3.content)


class PaginatorCheck(TestCase):

    POSTS_COUNT = 15

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
        cls.user = User.objects.create_user(
            username='user'
        )
        for post_number in range(PaginatorCheck.POSTS_COUNT):
            Post.objects.create(
                text=f'text_{post_number}',
                author=cls.author_user,
                group=cls.group,
            )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author_user
        )

    def setUp(self):
        self.post_author_client = Client()
        self.post_author_client.force_login(self.author_user)

        self.follow_user = Client()
        self.follow_user.force_login(self.user)

    def test_page_contains_ten_records(self):
        """Страницы содержат правильное количество записей."""
        urls_args = {
            ('posts:index', None),
            ('posts:group_posts', (self.group.slug,)),
            ('posts:profile', (self.author_user.username,)),
            ('posts:follow_index', None)
        }
        page_count_of_posts = (
            ('?page=1', settings.SAMPLE_SIZE),
            ('?page=2', PaginatorCheck.POSTS_COUNT - settings.SAMPLE_SIZE),
        )
        for reverse_name, arg in urls_args:
            with self.subTest(reverse_name=reverse_name):
                for page_number, posts_count in page_count_of_posts:
                    with self.subTest(reverse_name=reverse_name):
                        response = self.follow_user.get(
                            reverse(reverse_name, args=arg) + page_number
                        )
                        self.assertEqual(
                            len(response.context['page_obj']), posts_count
                        )


class FollowAuthors(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.author_user = User.objects.create_user(
            username='post_author'
        )
        cls.post = Post.objects.create(
            text='рандомный текст',
            author=cls.author_user,
            group=cls.group,
        )
        cls.user_follow = User.objects.create_user(
            username='user_follow'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(self.author_user)

        self.follow_user = Client()
        self.follow_user.force_login(self.user)

    def test_authorized_client_can_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей."""

        follow_count = Follow.objects.count()

        self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.post.author,)),
            follow=True
        )

        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(Follow.objects.first().author, self.post.author)
        self.assertEqual(Follow.objects.first().user, self.user)

    def test_authorized_client_can_unfollow(self):
        """Авторизованный пользователь может удалять из подписок."""

        Follow.objects.all().delete()
        follow_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user,
            author=self.author_user
        )

        self.assertEqual(Follow.objects.count(), follow_count + 1)

        self.authorized_client.post(
            reverse('posts:profile_unfollow', args=(self.post.author,)),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_new_post_for_follow_and_unfollow(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан."""

        response_1 = self.authorized_client.get(reverse('posts:follow_index'))
        follow_count = len(response_1.context['page_obj'])
        self.assertEqual(follow_count, 0)

        Follow.objects.create(
            user=self.user,
            author=self.author_user
        )
        response_2 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 1)
