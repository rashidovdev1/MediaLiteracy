from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, Course, Lesson, LessonProgress


def course_list(request):
    """Barcha kurslar ro'yxati"""
    courses = Course.objects.filter(is_published=True)
    categories = Category.objects.all()

    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        courses = courses.filter(category__slug=category_slug)

    # Filter by difficulty
    difficulty = request.GET.get('difficulty')
    if difficulty:
        courses = courses.filter(difficulty=difficulty)

    # Search
    query = request.GET.get('q')
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': category_slug,
        'selected_difficulty': difficulty,
    }
    return render(request, 'courses/course_list.html', context)


def course_detail(request, slug):
    """Kurs tafsilotlari"""
    course = get_object_or_404(Course, slug=slug, is_published=True)
    lessons = course.lessons.all()

    # Agar user login qilgan bo'lsa, progressni ko'rsatish
    user_progress = None
    if request.user.is_authenticated:
        user_progress = course.get_student_progress(request.user)

    context = {
        'course': course,
        'lessons': lessons,
        'user_progress': user_progress,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def lesson_view(request, course_slug, lesson_id):
    """Darsni ko'rish"""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    # Progress obyektini olish yoki yaratish
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )

    # Darsni tugatish tugmasi bosilganda
    if request.method == 'POST':
        if not progress.completed:
            progress.mark_complete()
            messages.success(request, f"Tabriklaymiz! Siz {lesson.points} ball oldingiz!")
        return redirect('lesson_view', course_slug=course_slug, lesson_id=lesson_id)

    # Keyingi va oldingi darslar
    next_lesson = Lesson.objects.filter(course=course, order__gt=lesson.order).first()
    prev_lesson = Lesson.objects.filter(course=course, order__lt=lesson.order).last()

    context = {
        'course': course,
        'lesson': lesson,
        'progress': progress,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
        'embed_url': lesson.get_youtube_embed_url(),
    }
    return render(request, 'courses/lesson_view.html', context)


@login_required
def my_courses(request):
    """Foydalanuvchining kurslar ro'yxati"""
    # Foydalanuvchi boshlagan kurslar
    started_lessons = LessonProgress.objects.filter(user=request.user).values_list('lesson__course', flat=True)
    courses = Course.objects.filter(id__in=started_lessons, is_published=True).distinct()

    courses_with_progress = []
    for course in courses:
        progress = course.get_student_progress(request.user)
        courses_with_progress.append({
            'course': course,
            'progress': progress
        })

    context = {
        'courses_with_progress': courses_with_progress
    }
    return render(request, 'courses/my_courses.html', context)
