from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name='Название группы', max_length=200)
    slug = models.SlugField(verbose_name='Уникальный адрес группы',
                            unique=True)
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(verbose_name='Текст поста',
                            help_text='Введите текст поста')
    """pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True)"""
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, verbose_name='Сообщество',
                              on_delete=models.SET_NULL, blank=True,
                              null=True, related_name='posts',
                              help_text='Группа, к которой будет относиться '
                                        'пост')
    image = models.ImageField('Картинка', upload_to='posts/', blank=True)
    # Аргумент upload_to указывает директорию,
    # в которую будут загружаться пользовательские файлы.

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(Post, verbose_name='Пост',
                             on_delete=models.CASCADE, blank=True,
                             null=True, related_name='comments',
                             help_text='Ссылка на пост, к которому оставлен '
                                       'комментарий')
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE, blank=True,
                               null=True, related_name='comments',
                               help_text='Ссылка на автора комментария')
    text = models.TextField(verbose_name='Текст комментария',
                            help_text='Введите текст комментария')
    """created = models.DateTimeField(verbose_name='Дата публикации комментария',
                                   auto_now_add=True)"""

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             on_delete=models.CASCADE, blank=True,
                             null=True, related_name='follower',
                             help_text='Ссылка на объект пользователя, '
                                       'который подписывается')
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE, blank=True,
                               null=True, related_name='following',
                               help_text='Ссылка на объект пользователя, '
                                         'на которого подписываются')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return self.author.username
