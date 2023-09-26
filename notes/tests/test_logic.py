from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TEXT = 'Текс заметки'
    TITLE = 'Заголовок'
    SLUG = 'slug2'
    NEW_NOTE_TEXT = 'Обновленный текст'
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='author'
        )
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            slug='slug1',
            author=cls.user
        )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        
        cls.url = reverse('notes:add', None)
        cls.form_data = {
            'title':cls.TITLE,
            'text':cls.NOTE_TEXT,
            'slug':cls.SLUG
        }
        cls.new_form_data = {'title':cls.TITLE,'text': cls.NEW_NOTE_TEXT,'slug':cls.SLUG}
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        note_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.url_to_note = reverse('notes:detail', args=(cls.note.slug,))
        cls.done_url = reverse('notes:success', None)

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_user_can_create_note(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.done_url)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 2)

    def test_user_cant_use_bad_slug(self):
        bad_slug = {'title':'Заголовок', 'text':'Текс', 'slug':'slug1'}
        response = self.auth_client.post(self.url, data=bad_slug)
        self.assertFormError(
                response,
                form='form',
                field='slug',
                errors=f'slug1{WARNING}'
            )
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_author_can_delete_note(self):
        response = self.auth_client.delete(self.delete_url)
        self.assertRedirects(response, self.done_url)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        
    def test_author_can_edit_note(self):
        response = self.auth_client.post(self.edit_url, data=self.new_form_data)
        self.assertRedirects(response, self.done_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        
    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
