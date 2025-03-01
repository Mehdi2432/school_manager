# school_manager/core/admin.py
from django.contrib import admin
from .models import School, Teacher, Parent, Student, Class, Schedule, AcademicYear, UserProfile

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('year',)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'address', 'academic_year')
    search_fields = ('name',)
    list_filter = ('academic_year', 'level')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'get_schools', 'user')
    list_filter = ('subject',)
    search_fields = ('name', 'user__username')

    def get_schools(self, obj):
        return ", ".join([school.name for school in obj.schools.all()])
    get_schools.short_description = 'مدرسه‌ها'

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'user')
    search_fields = ('name', 'user__username')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'teacher', 'school', 'parent')
    list_filter = ('grade', 'teacher', 'school')
    search_fields = ('name',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('subject', 'grade', 'name', 'teacher', 'school')
    list_filter = ('teacher', 'school', 'grade')
    search_fields = ('subject', 'name')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('class_session', 'day', 'period')
    list_filter = ('day', 'period', 'class_session__teacher')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)