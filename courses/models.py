from django.db import models
from django.conf import settings
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    description = models.TextField(verbose_name="Ta'rif")
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon: fa-video, fa-book, etc.")
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    DIFFICULTY_CHOICES = (
        ('beginner', 'Boshlang\'ich'),
        ('intermediate', 'O\'rta'),
        ('advanced', 'Murakkab'),
    )

    title = models.CharField(max_length=200, verbose_name="Kurs nomi")
    description = models.TextField(verbose_name="Tavsif")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False, verbose_name="Nashr qilingan")
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            self.slug = slugify(self.title) + '-' + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def get_total_lessons(self):
        return self.lessons.count()

    def get_total_duration(self):
        return sum([lesson.duration for lesson in self.lessons.all()])

    def get_student_progress(self, user):
        total_lessons = self.get_total_lessons()
        if total_lessons == 0:
            return 0
        completed = LessonProgress.objects.filter(
            user=user,
            lesson__course=self,
            completed=True
        ).count()
        return int((completed / total_lessons) * 100)


class Lesson(models.Model):
    course = models.ForeignKey(Course, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="Dars nomi")
    description = models.TextField(verbose_name="Tavsif")
    youtube_url = models.URLField(verbose_name="YouTube URL")
    order = models.IntegerField(default=0, verbose_name="Tartib raqami")
    duration = models.IntegerField(help_text="Daqiqalarda", default=0)
    points = models.IntegerField(default=10, verbose_name="Balllar")
    materials = models.TextField(blank=True, verbose_name="Qo'shimcha materiallar")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dars"
        verbose_name_plural = "Darslar"
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def get_youtube_embed_url(self):
        """YouTube URL ni embed formatga o'zgartirish"""
        if 'watch?v=' in self.youtube_url:
            video_id = self.youtube_url.split('watch?v=')[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be/' in self.youtube_url:
            video_id = self.youtube_url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return self.youtube_url

    def is_completed_by(self, user):
        return LessonProgress.objects.filter(
            user=user,
            lesson=self,
            completed=True
        ).exists()


class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Dars jarayoni"
        verbose_name_plural = "Darslar jarayoni"
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"

    def mark_complete(self):
        """Darsni tugatish va ball berish"""
        if not self.completed:
            self.completed = True
            self.completed_at = timezone.now()
            self.save()

            # Foydalanuvchiga ball qo'shish
            self.user.total_points += self.lesson.points
            self.user.save()