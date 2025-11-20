from django.contrib import admin
from .models import Category, Course, Lesson, LessonProgress


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['order', 'title', 'youtube_url', 'duration', 'points']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'is_published', 'created_by', 'created_at']
    list_filter = ['category', 'difficulty', 'is_published', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration', 'points']
    list_filter = ['course']
    search_fields = ['title', 'description']
    ordering = ['course', 'order']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'completed', 'completed_at']
    list_filter = ['completed', 'completed_at']
    search_fields = ['user__username', 'lesson__title']