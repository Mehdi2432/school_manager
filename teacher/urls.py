from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.unified_login, name='unified_login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('schools/', views.my_schools, name='my_schools'),
    path('classes/', views.my_classes, name='my_classes'),
    path('students/', views.my_students, name='my_students'),
    path('students/class/<int:class_id>/', views.student_list, name='student_list'),
    path('schedule/', views.schedule_settings, name='schedule_settings'),
    path('add-school/', views.add_school, name='add_school'),
    path('edit-school/', views.edit_school, name='edit_school'),
    path('delete-school/', views.delete_school, name='delete_school'),
    path('add-year/', views.add_year, name='add_year'),
    path('profile/', views.teacher_profile, name='teacher_profile'),
    path('logout/', views.teacher_logout, name='logout'),
    path('class/<int:class_id>/', views.class_management, name='class_management'),
    path('update-attendance/', views.update_attendance, name='update_attendance'),
    path('update-grade/', views.update_grade, name='update_grade'),
    path('update-discipline/', views.update_discipline, name='update_discipline'),
    path('update-activity/', views.update_activity, name='update_activity'),
    path('save-session/', views.save_session, name='save_session'),
    path('update-settings/', views.update_settings, name='update_settings'),
]