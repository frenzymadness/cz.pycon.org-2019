from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse


class Speaker(models.Model):
    full_name = models.CharField(max_length=200)
    bio = models.TextField()
    short_bio = models.TextField('Short bio', blank=True, help_text='For keynote speakers')
    twitter = models.CharField(max_length=255, blank=True)
    github = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    photo = models.ImageField(upload_to='programme/speakers/')
    talks = models.ManyToManyField('Talk', blank=True, related_name='talk_speakers')
    workshops = models.ManyToManyField('Workshop', blank=True, related_name='ws_speakers')
    display_position = models.PositiveSmallIntegerField(default=0, help_text='sort order on frontend displays')
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ('display_position', 'full_name',)

    def __str__(self):
        return self.full_name

    def _talkws_export(self, type_):
        qs = self.talks.all() if type_ == 'talk' else self.workshops.all()
        return '\n'.join([
            '%s | %s' % (
                t.title, 'https://cz.pycon.org'
                + reverse('session_detail', kwargs={'type': type_, 'talk_id': t.id}),
            )
            for t in qs
        ])

    def talks_export(self):
        return self._talkws_export('talk')

    def workshops_export(self):
        return self._talkws_export('workshop')


class Talk(models.Model):
    DIFFICULTY = (
        ('beginner', 'Beginner'),
        ('advanced', 'Advanced'),
    )

    LANGUAGES = (
        ('en', 'English (preferred)'),
        ('cs', 'Czechoslovak'),
    )

    type = 'talk'  # for symmetry with workshops/sprints
    order = models.SmallIntegerField(unique=True, help_text='display order on front end, has to be unique')
    title = models.CharField(max_length=200)
    og_image = models.ImageField(upload_to='programme/talks/', null=True, blank=True, help_text='og:image (social media image) 1200×630 pixels')
    abstract = models.TextField()
    language = models.CharField(max_length=2, choices=LANGUAGES, default='en')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default='beginner')
    video_id = models.CharField(max_length=100, default='', blank=True, help_text='youtube')
    is_backup = models.BooleanField(default=False, blank=True)
    is_keynote = models.BooleanField(default=False, blank=True)
    is_public = models.BooleanField(default=False, blank=True)
    in_data_track = models.BooleanField('PyData Track', default=False, blank=True)
    private_note = models.TextField(default='', blank=True, help_text='DO NOT SHOW ON WEBSITE')

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.title

    @property
    def speakers(self):
        return self.talk_speakers.all()

    @property
    def speakers_display(self):
        return '; '.join(map(str, self.speakers))

    @property
    def video_embed_url(self):
        return 'https://www.youtube.com/embed/' + self.video_id


class Workshop(models.Model):
    DIFFICULTY = (
        ('beginner', 'Beginner'),
        ('advanced', 'Advanced'),
    )

    TYPE = (
        ('workshop', 'Workshop'),
        ('sprint', 'Sprint'),
    )

    LENGTH = (
        ('1h', '1 hour'),
        ('2h', '2 hours'),
        ('3h', '3 hours'),
        ('1d', 'Full day (most sprints go here!)'),
        ('xx', 'Something else! (Please leave a note in the abstract!)')
    )

    LANGUAGES = (
        ('en', 'English (preferred)'),
        ('cs', 'Czech/Slovak'),
    )

    REGISTRATION = (
        ('without', 'Without'),
        ('free', 'Free'),
        ('paid', 'Paid'),
    )

    type = models.CharField(max_length=10, choices=TYPE, default='sprint')
    order = models.SmallIntegerField(unique=True, help_text='display order on front end, has to be unique')
    title = models.CharField(max_length=200, verbose_name='Title')
    og_image = models.ImageField(upload_to='programme/workshops/', null=True, blank=True, help_text='og:image (social media image) 1200×630 pixels')
    abstract = models.TextField()
    requirements = models.TextField('What should attendees bring, install and know?', default='', blank=True, help_text='Include even the most obvious stuff: laptops, git, python')
    language = models.CharField(max_length=2, choices=LANGUAGES, default='en')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default='beginner', )
    length = models.CharField(max_length=2, choices=LENGTH, blank=True, )
    attendee_limit = models.PositiveSmallIntegerField('Atendee limit', default=False, blank=True, help_text='Maximum number of attendees allowed')
    tito_id = models.SlugField('Ticket ID in ti.to', null=True, blank=True, help_text='Tickets are called releases in API')
    registration = models.CharField(max_length=10, choices=REGISTRATION, default='free', blank='free')
    is_backup = models.BooleanField(default=False, blank=True)
    is_public = models.BooleanField(default=False, blank=True)
    in_data_track = models.BooleanField('PyData Track', default=False, blank=True)
    private_note = models.TextField(default='', blank=True, help_text='DO NOT SHOW ON WEBSITE')

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.title

    @property
    def speakers(self):
        return self.ws_speakers.all()

    @property
    def speakers_display(self):
        return '; '.join(map(str, self.speakers))


class Slot(models.Model):
    start = models.DateTimeField()
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    description = models.CharField(max_length=100, blank=True, default='', help_text='will be markdowned')
    room = models.PositiveSmallIntegerField(choices=settings.ALL_ROOMS)
    end = models.DateTimeField()

    class Meta:
        ordering = ('start', 'room',)


class EndTime(models.Func):
    template = 'LAG(date) OVER (PARTITION BY room ORDER BY date DESC)'

    def __init__(self):
        super().__init__(output_field=models.DateTimeField())

    def get_group_by_cols(self):
        return []

class Utility(models.Model):
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
            verbose_name = 'Utility'
            verbose_name_plural = 'Utilities'