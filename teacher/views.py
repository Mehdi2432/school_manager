from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from core.models import Teacher, Class, Schedule, School, AcademicYear, UserProfile, License, Student, Parent, StudentUser, Session, StudentSession, TeacherSettings, ClassActivity
import jdatetime
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

def from_persian_numbers(num_str):
    persian_digits = {'۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'}
    return ''.join(persian_digits.get(c, c) for c in str(num_str))

def unified_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                profile = user.userprofile
                license = user.license
                if not license.is_active():
                    return render(request, 'teacher/login.html', {'error': 'لایسنس شما منقضی شده است!'})
                if profile.role == role:
                    if role == 'teacher':
                        return redirect('teacher_dashboard')
                    elif role == 'student':
                        return redirect('student_dashboard')
                else:
                    return render(request, 'teacher/login.html', {'error': 'نقش انتخاب‌شده با حساب شما مطابقت ندارد!'})
            except (UserProfile.DoesNotExist, License.DoesNotExist):
                return render(request, 'teacher/login.html', {'error': 'پروفایل یا لایسنس شما تنظیم نشده است!'})
        else:
            return render(request, 'teacher/login.html', {'error': 'نام کاربری یا رمز عبور اشتباه است!'})
    return render(request, 'teacher/login.html', {'default_role': 'teacher'})

def register(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        submit_type = request.POST.get('submit_type')
        print("Form type:", form_type, "Submit type:", submit_type)
        print("POST data:", request.POST)

        if submit_type == 'register':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name', '')
            phone_number = request.POST.get('phone_number')
            username = request.POST.get('username')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            role = request.POST.get('role')
            license_file = request.FILES.get('license_file')

            print("Received data:", {
                "first_name": first_name,
                "phone_number": phone_number,
                "username": username,
                "password": password,
                "password_confirm": password_confirm,
                "role": role,
                "license_file": license_file
            })

            if not all([first_name, phone_number, username, password, password_confirm, role]):
                return render(request, 'teacher/register.html', {'error': 'فیلدهای اجباری را پر کنید!'})
            if password != password_confirm:
                return render(request, 'teacher/register.html', {'error': 'رمز عبور و تکرارش یکسان نیستند!'})
            if User.objects.filter(username=username).exists():
                return render(request, 'teacher/register.html', {'error': 'نام کاربری قبلاً استفاده شده است!'})

            user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
            UserProfile.objects.create(user=user, role=role)
            license = License.objects.create(user=user, is_trial=not license_file)
            if license_file:
                license.license_file = license_file
                license.save()

            if role == 'teacher':
                teacher = Teacher.objects.create(user=user, name=f"{first_name} {last_name}".strip(), subject="مشخص نشده")
                TeacherSettings.objects.create(teacher=teacher)
            elif role == 'student':
                teacher = Teacher.objects.first() or Teacher.objects.create(user=User.objects.create_user('default_teacher', password='1234'), name='معلم پیش‌فرض', subject='ریاضی')
                school = School.objects.first() or School.objects.create(academic_year=AcademicYear.objects.first() or AcademicYear.objects.create(year="1403-1404"), name="مدرسه پیش‌فرض", level="دبیرستان")
                parent = Parent.objects.first() or Parent.objects.create(user=User.objects.create_user('default_parent', password='1234'), name='والد پیش‌فرض', phone_number='09123456789')
                StudentUser.objects.create(user=user, name=f"{first_name} {last_name}".strip(), grade="دوازدهم", parent=parent, teacher=teacher, school=school)

            return render(request, 'teacher/register.html', {'success': True})
        elif submit_type == 'license':
            if not request.user.is_authenticated:
                return redirect('unified_login')
            license_file = request.FILES.get('license_file')
            if license_file:
                license = request.user.license
                license.license_file = license_file
                license.is_trial = False
                license.save()
                if license.validate_license():
                    return render(request, 'teacher/register.html', {'message': {'text': 'لایسنس معتبر است!', 'success': True}})
                else:
                    return render(request, 'teacher/register.html', {'message': {'text': 'لایسنس نامعتبر است!', 'success': False}})
            return render(request, 'teacher/register.html', {'error': 'لایسنس را بارگذاری کنید!'})
    return render(request, 'teacher/register.html')

def teacher_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    try:
        teacher = request.user.teacher_profile
        schedules = Schedule.objects.filter(class_session__teacher=teacher)
        days = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        periods = [1, 2, 3, 4]
        schedule_dict = {day: {period: None for period in periods} for day in days}
        for s in schedules:
            schedule_dict[s.day][s.period] = s.class_session
        today = jdatetime.date.today().strftime('%Y/%m/%d')
    except Teacher.DoesNotExist:
        return render(request, 'teacher/error.html', {'message': 'شما معلم نیستید!'})
    return render(request, 'teacher/dashboard.html', {
        'teacher_name': teacher.name,
        'schedules': schedule_dict,
        'days': days,
        'periods': periods,
        'today': today,
    })

def my_schools(request):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    try:
        teacher = request.user.teacher_profile
        years = AcademicYear.objects.all()
        selected_year = request.GET.get('year', years.filter(is_active=True).first().id if years.filter(is_active=True).exists() else None)
        schools = teacher.schools.filter(academic_year_id=selected_year) if selected_year else School.objects.none()
    except Teacher.DoesNotExist:
        return render(request, 'teacher/error.html', {'message': 'شما معلم نیستید!'})
    return render(request, 'teacher/my_schools.html', {
        'teacher_name': teacher.name,
        'schools': schools,
        'years': years,
        'selected_year': int(selected_year) if selected_year else None,
    })

def add_school(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        level = request.POST.get('level')
        address = request.POST.get('address', '')
        year_id = request.POST.get('year')
        try:
            teacher = request.user.teacher_profile
            school = School.objects.create(
                academic_year_id=year_id,
                name=name,
                level=level,
                address=address
            )
            teacher.schools.add(school)
            return JsonResponse({'success': True, 'id': school.id, 'name': school.name, 'level': school.level, 'address': school.address})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def edit_school(request):
    if request.method == 'POST':
        school_id = request.POST.get('id')
        name = request.POST.get('name')
        level = request.POST.get('level')
        address = request.POST.get('address', '')
        try:
            school = School.objects.get(id=school_id)
            school.name = name
            school.level = level
            school.address = address
            school.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def delete_school(request):
    if request.method == 'POST':
        school_id = request.POST.get('id')
        try:
            school = School.objects.get(id=school_id)
            teacher = request.user.teacher_profile
            teacher.schools.remove(school)
            school.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def add_year(request):
    if request.method == 'POST':
        year = request.POST.get('year')
        try:
            academic_year = AcademicYear.objects.create(year=year)
            return JsonResponse({'success': True, 'id': academic_year.id, 'year': academic_year.year})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def class_detail(request, class_id):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    try:
        class_session = Class.objects.get(id=class_id)
        return render(request, 'teacher/class_detail.html', {'class': class_session})
    except Class.DoesNotExist:
        return render(request, 'teacher/error.html', {'message': 'کلاس پیدا نشد!'})

def teacher_profile(request):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    
    user = request.user
    profile = user.userprofile
    license = user.license
    today = jdatetime.date.today()
    days_left = (license.end_date.date() - today).days if license.end_date else None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            if profile.role == 'teacher':
                user.teacher_profile.name = f"{first_name} {last_name}".strip()
                user.teacher_profile.save()
            elif profile.role == 'school':
                user.school.name = f"{first_name} {last_name}".strip()
                user.school.save()
            elif profile.role == 'parent':
                user.parent_profile.name = f"{first_name} {last_name}".strip()
                user.parent_profile.save()
            return render(request, 'teacher/profile.html', {
                'user': user,
                'message': 'تغییرات با موفقیت ثبت شد',
                'days_left': days_left,
            })
        elif action == 'change_password':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            if password == password_confirm:
                user.set_password(password)
                user.save()
                update_session_auth_hash(request, user)
                return render(request, 'teacher/profile.html', {
                    'user': user,
                    'message': 'رمز عبور با موفقیت تغییر کرد',
                    'days_left': days_left,
                })
            else:
                return render(request, 'teacher/profile.html', {
                    'user': user,
                    'error': 'رمز عبور و تکرارش یکسان نیستند!',
                    'days_left': days_left,
                })
        elif action == 'upload_license':
            license_file = request.FILES.get('license_file')
            if license_file:
                license = request.user.license
                license.license_file = license_file
                license.is_trial = False
                license.end_date = today + jdatetime.timedelta(days=30)
                license.save()
                days_left = 30
                return render(request, 'teacher/profile.html', {
                    'user': user,
                    'message': 'لایسنس با موفقیت ثبت شد',
                    'days_left': days_left,
                })
            else:
                return render(request, 'teacher/profile.html', {
                    'user': user,
                    'error': 'فایل لایسنس را بارگذاری کنید!',
                    'days_left': days_left,
                })

    return render(request, 'teacher/profile.html', {
        'user': user,
        'days_left': days_left,
    })

def my_classes(request):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    
    user = request.user
    classes = Class.objects.filter(teacher=user.teacher_profile)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_class':
            name = request.POST.get('name')
            subject = request.POST.get('subject')
            grade = request.POST.get('grade')
            school_id = request.POST.get('school')
            school = School.objects.get(id=school_id)
            
            if Class.objects.filter(name=name, subject=subject, grade=grade, school=school, teacher=user.teacher_profile).exists():
                return JsonResponse({'error': 'این کلاس قبلاً تعریف شده است. لطفاً اطلاعات متفاوتی وارد کنید.'})
            
            new_class = Class.objects.create(
                name=name,
                subject=subject,
                grade=grade,
                teacher=user.teacher_profile,
                school=school
            )
            return JsonResponse({
                'success': True,
                'id': new_class.id,
                'name': new_class.name,
                'subject': new_class.subject,
                'grade': new_class.grade,
                'school': new_class.school.name
            })
        elif action == 'edit_class':
            class_id = request.POST.get('class_id')
            class_obj = Class.objects.get(id=class_id)
            new_name = request.POST.get('name')
            new_subject = request.POST.get('subject')
            new_grade = request.POST.get('grade')
            new_school_id = request.POST.get('school')
            
            if Class.objects.filter(name=new_name, subject=new_subject, grade=new_grade, school_id=new_school_id, teacher=user.teacher_profile).exclude(id=class_id).exists():
                return JsonResponse({'error': 'این کلاس قبلاً تعریف شده است. لطفاً اطلاعات متفاوتی وارد کنید.'})
            
            class_obj.name = new_name
            class_obj.subject = new_subject
            class_obj.grade = new_grade
            class_obj.school = School.objects.get(id=new_school_id)
            class_obj.save()
            return JsonResponse({'success': True})
        elif action == 'delete_class':
            class_id = request.POST.get('class_id')
            Class.objects.get(id=class_id).delete()
            return JsonResponse({'success': True})

    return render(request, 'teacher/my_classes.html', {
        'classes': classes,
        'schools': School.objects.filter(teachers=user.teacher_profile),
    })

def schedule_settings(request):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    
    user = request.user
    teacher = user.teacher_profile
    schedules = Schedule.objects.filter(class_session__teacher=teacher)
    classes = Class.objects.filter(teacher=teacher)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_schedule':
            class_id = request.POST.get('class')
            day = request.POST.get('day')
            period = request.POST.get('period')
            
            if Schedule.objects.filter(class_session__teacher=teacher, day=day, period=period).exists():
                return JsonResponse({'error': 'این زنگ در این روز قبلاً تنظیم شده است. لطفاً زنگ دیگری انتخاب کنید.'})
            
            class_session = Class.objects.get(id=class_id, teacher=teacher)
            new_schedule = Schedule.objects.create(
                class_session=class_session,
                day=day,
                period=period
            )
            return JsonResponse({
                'success': True,
                'id': new_schedule.id,
                'class_name': new_schedule.class_session.name,
                'subject': new_schedule.class_session.subject,
                'grade': new_schedule.class_session.grade,
                'school': new_schedule.class_session.school.name,
                'day': new_schedule.day,
                'period': new_schedule.period
            })
        elif action == 'edit_schedule':
            schedule_id = request.POST.get('schedule_id')
            schedule = Schedule.objects.get(id=schedule_id, class_session__teacher=teacher)
            new_class_id = request.POST.get('class')
            new_day = request.POST.get('day')
            new_period = request.POST.get('period')
            
            if Schedule.objects.filter(class_session__teacher=teacher, day=new_day, period=new_period).exclude(id=schedule_id).exists():
                return JsonResponse({'error': 'این زنگ در این روز قبلاً تنظیم شده است. لطفاً زنگ دیگری انتخاب کنید.'})
            
            schedule.class_session = Class.objects.get(id=new_class_id, teacher=teacher)
            schedule.day = new_day
            schedule.period = new_period
            schedule.save()
            return JsonResponse({'success': True})
        elif action == 'delete_schedule':
            schedule_id = request.POST.get('schedule_id')
            Schedule.objects.get(id=schedule_id, class_session__teacher=teacher).delete()
            return JsonResponse({'success': True})

    return render(request, 'teacher/schedule_settings.html', {
        'schedules': schedules,
        'classes': classes,
        'days': ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'],
        'periods': [1, 2, 3, 4]
    })

def my_students(request):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    
    teacher = request.user.teacher_profile
    schools = School.objects.filter(teachers=teacher)
    classes_by_school = {school: Class.objects.filter(teacher=teacher, school=school) for school in schools}
    return render(request, 'teacher/my_students.html', {
        'schools': schools,
        'classes_by_school': classes_by_school,
    })

def student_list(request, class_id):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    
    teacher = request.user.teacher_profile
    class_obj = Class.objects.get(id=class_id, teacher=teacher)
    
    students = class_obj.students.all()
    students = sorted(students, key=lambda x: x.name.split()[-1] if x.name.split() else x.name)
    
    classes = Class.objects.filter(teacher=teacher)
    parents = Parent.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_student':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            parent_username = request.POST.get('parent_username', None)
            student_username = request.POST.get('student_username', None)
            
            full_name = f"{first_name} {last_name}"
            if class_obj.students.filter(name=full_name).exists():
                return JsonResponse({'error': 'این دانش‌آموز قبلاً در این کلاس ثبت شده است.'})
            
            student_data = {
                'name': full_name,
                'grade': class_obj.grade,
                'teacher': teacher,
                'school': class_obj.school,
            }
            if parent_username:
                try:
                    parent = Parent.objects.get(user__username=parent_username)
                    student_data['parent'] = parent
                except Parent.DoesNotExist:
                    return JsonResponse({'error': 'نام کاربری والد با این مشخصات وجود ندارد.'})
            if student_username:
                try:
                    student_user = StudentUser.objects.get(user__username=student_username)
                    student_data['student_user'] = student_user
                except StudentUser.DoesNotExist:
                    return JsonResponse({'error': 'نام کاربری دانش‌آموز با این مشخصات وجود ندارد.'})
            
            new_student = Student.objects.create(**student_data)
            class_obj.students.add(new_student)
            return JsonResponse({
                'success': True,
                'id': new_student.id,
                'first_name': first_name,
                'last_name': last_name,
                'grade': class_obj.grade,
                'parent_username': parent_username if parent_username else '-',
                'student_username': student_username if student_username else '-',
            })
        elif action == 'edit_student':
            student_id = request.POST.get('student_id')
            student = class_obj.students.get(id=student_id)
            name = request.POST.get('name')
            grade = request.POST.get('grade')
            parent_username = request.POST.get('parent_username', None)
            student_username = request.POST.get('student_username', None)
            
            if class_obj.students.filter(name=name).exclude(id=student_id).exists():
                return JsonResponse({'error': 'این دانش‌آموز قبلاً در این کلاس ثبت شده است.'})
            
            student.name = name
            student.grade = grade
            if parent_username:
                try:
                    parent = Parent.objects.get(user__username=parent_username)
                    student.parent = parent
                except Parent.DoesNotExist:
                    return JsonResponse({'error': 'نام کاربری والد با این مشخصات وجود ندارد.'})
            else:
                student.parent = None
            if student_username:
                try:
                    student_user = StudentUser.objects.get(user__username=student_username)
                    student.student_user = student_user
                except StudentUser.DoesNotExist:
                    return JsonResponse({'error': 'نام کاربری دانش‌آموز با این مشخصات وجود ندارد.'})
            else:
                student.student_user = None
            student.save()
            return JsonResponse({'success': True})
        elif action == 'delete_student':
            student_id = request.POST.get('student_id')
            student = class_obj.students.get(id=student_id)
            class_obj.students.remove(student)
            student.delete()
            return JsonResponse({'success': True})

    return render(request, 'teacher/student_list.html', {
        'class_obj': class_obj,
        'students': students,
        'classes': classes,
        'parents': parents,
    })

def teacher_logout(request):
    logout(request)
    return redirect('unified_login')

def student_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    try:
        student = request.user.student_profile
        return render(request, 'teacher/student_dashboard.html', {'student_name': student.name})
    except StudentUser.DoesNotExist:
        return render(request, 'teacher/error.html', {'message': 'شما دانش‌آموز نیستید!'})

def class_management(request, class_id):
    if not request.user.is_authenticated:
        return redirect('unified_login')
    
    teacher = request.user.teacher_profile
    class_obj = Class.objects.get(id=class_id, teacher=teacher)
    today = timezone.now().date()
    
    session, created = Session.objects.get_or_create(
        class_obj=class_obj,
        date=today,
        defaults={'session_number': 1}
    )
    
    if created:
        last_session = Session.objects.filter(class_obj=class_obj).exclude(id=session.id).order_by('-session_number').first()
        if last_session:
            session.session_number = last_session.session_number + 1
            session.save()

    student_sessions = []
    for student in class_obj.students.all():
        student_session, _ = StudentSession.objects.get_or_create(
            session=session,
            student=student,
            defaults={'attendance': True, 'daily_grade': None, 'discipline': None}
        )
        student_sessions.append(student_session)
        logger.info(f"Student {student.id} attendance: {student_session.attendance}")

    settings, _ = TeacherSettings.objects.get_or_create(teacher=teacher, class_obj=class_obj)
    activities = ClassActivity.objects.filter(teacher=teacher, class_obj=class_obj)

    jalali_date = jdatetime.date.today().strftime('%Y/%m/%d')

    return render(request, 'teacher/class_management.html', {
        'class_obj': class_obj,
        'student_sessions': student_sessions,
        'session': session,
        'current_date': jalali_date,
        'settings': settings,
        'activities': activities,
    })

@csrf_exempt
def update_attendance(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        session_id = request.POST.get('session_id')
        attendance = request.POST.get('attendance') == 'true'
        try:
            student_session = StudentSession.objects.get(student_id=student_id, session_id=session_id)
            student_session.attendance = attendance
            student_session.save()
            logger.info(f"Updated attendance for student {student_id} in session {session_id}: {attendance}")
            return JsonResponse({'success': True})
        except StudentSession.DoesNotExist:
            logger.error(f"StudentSession not found for student {student_id} in session {session_id}")
            return JsonResponse({'success': False, 'error': 'رکورد پیدا نشد'})
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})

@csrf_exempt
def update_grade(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        session_id = request.POST.get('session_id')
        grade = request.POST.get('daily_grade')
        try:
            student_session = StudentSession.objects.get(student_id=student_id, session_id=session_id)
            if grade != '':
                grade = float(from_persian_numbers(grade))
                teacher = request.user.teacher_profile
                settings = TeacherSettings.objects.get(teacher=teacher, class_obj=student_session.session.class_obj)
                if settings.grade_min <= grade <= settings.grade_max:
                    student_session.daily_grade = grade
                else:
                    student_session.daily_grade = min(max(grade, settings.grade_min), settings.grade_max)
            else:
                student_session.daily_grade = None
            student_session.save()
            return JsonResponse({'success': True})
        except StudentSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'رکورد پیدا نشد'})
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})

@csrf_exempt
def update_discipline(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        session_id = request.POST.get('session_id')
        discipline = request.POST.get('discipline')
        try:
            student_session = StudentSession.objects.get(student_id=student_id, session_id=session_id)
            student_session.discipline = discipline if discipline else None
            student_session.save()
            return JsonResponse({'success': True})
        except StudentSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'رکورد پیدا نشد'})
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})

@csrf_exempt
def update_activity(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        session_id = request.POST.get('session_id')
        activity_id = request.POST.get('activity')
        try:
            student_session = StudentSession.objects.get(student_id=student_id, session_id=session_id)
            student_session.activity = ClassActivity.objects.get(id=activity_id) if activity_id else None
            student_session.save()
            return JsonResponse({'success': True})
        except (StudentSession.DoesNotExist, ClassActivity.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'رکورد پیدا نشد'})
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})

@csrf_exempt
def save_session(request):
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        scope = request.POST.get('scope')
        updates = json.loads(request.POST.get('updates', '[]'))
        today = timezone.now().date()
        
        teacher = request.user.teacher_profile
        classes = [Class.objects.get(id=class_id)] if scope == 'current' else Class.objects.filter(teacher=teacher)
        
        for class_obj in classes:
            session, created = Session.objects.get_or_create(
                class_obj=class_obj,
                date=today,
                defaults={'session_number': 1}
            )
            if created:
                last_session = Session.objects.filter(class_obj=class_obj).exclude(id=session.id).order_by('-session_number').first()
                if last_session:
                    session.session_number = last_session.session_number + 1
                    session.save()

            settings = TeacherSettings.objects.get(teacher=teacher, class_obj=class_obj)

            for update in updates:
                student_id = update['student_id']
                student_session, created = StudentSession.objects.get_or_create(
                    session=session,
                    student_id=student_id,
                    defaults={'attendance': True, 'daily_grade': None, 'discipline': None}
                )
                student_session.attendance = update['attendance']
                grade = update['daily_grade']
                if grade is not None and grade != '':
                    grade = float(from_persian_numbers(grade))
                    if settings.grade_min <= grade <= settings.grade_max:
                        student_session.daily_grade = grade
                    else:
                        student_session.daily_grade = min(max(grade, settings.grade_min), settings.grade_max)
                else:
                    student_session.daily_grade = None
                student_session.discipline = update['discipline'] if update['discipline'] else None
                activity_id = update['activity']
                student_session.activity = ClassActivity.objects.get(id=activity_id) if activity_id else None
                student_session.save()
                logger.info(f"Saved student {student_id} in session {session.id}: attendance={student_session.attendance}")
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})

@csrf_exempt
def update_settings(request):
    if request.method == 'POST' and request.user.is_authenticated:
        teacher = request.user.teacher_profile
        scope = request.POST.get('scope')
        class_id = request.POST.get('class_id')
        
        if scope == 'current':
            class_obj = Class.objects.get(id=class_id)
            settings, _ = TeacherSettings.objects.get_or_create(teacher=teacher, class_obj=class_obj)
        else:
            # برای همه کلاس‌ها، تنظیمات عمومی رو آپدیت می‌کنیم یا برای هر کلاس جداگانه
            settings, _ = TeacherSettings.objects.get_or_create(teacher=teacher, class_obj=None)

        grade_min = request.POST.get('grade_min')
        grade_max = request.POST.get('grade_max')
        positive_value = request.POST.get('positive_value')
        negative_value = request.POST.get('negative_value')
        
        if grade_min: settings.grade_min = float(from_persian_numbers(grade_min))
        if grade_max: settings.grade_max = float(from_persian_numbers(grade_max))
        if positive_value: settings.positive_value = float(from_persian_numbers(positive_value))
        if negative_value: settings.negative_value = float(from_persian_numbers(negative_value))
        settings.save()
        logger.info(f"Settings updated for teacher {teacher.id}: min={settings.grade_min}, max={settings.grade_max}")

        activities = json.loads(request.POST.get('activities', '[]'))
        if scope == 'current':
            ClassActivity.objects.filter(teacher=teacher, class_obj=class_obj).delete()
            target_class = class_obj
        else:
            # برای همه کلاس‌ها، یا تنظیمات عمومی یا تکثیر برای همه
            ClassActivity.objects.filter(teacher=teacher).delete()
            target_class = None

        for activity in activities:
            if activity['name'] or activity['value']:
                ClassActivity.objects.create(
                    teacher=teacher,
                    class_obj=target_class,
                    name=activity['name'] or '',
                    value=float(from_persian_numbers(activity['value'])) if activity['value'] else 0
                )
        logger.info(f"Activities updated for teacher {teacher.id}: {len(activities)} items")

        if scope == 'all':
            for class_obj in Class.objects.filter(teacher=teacher):
                class_settings, _ = TeacherSettings.objects.get_or_create(teacher=teacher, class_obj=class_obj)
                class_settings.grade_min = settings.grade_min
                class_settings.grade_max = settings.grade_max
                class_settings.positive_value = settings.positive_value
                class_settings.negative_value = settings.negative_value
                class_settings.save()
                for activity in activities:
                    if activity['name'] or activity['value']:
                        ClassActivity.objects.create(
                            teacher=teacher,
                            class_obj=class_obj,
                            name=activity['name'] or '',
                            value=float(from_persian_numbers(activity['value'])) if activity['value'] else 0
                        )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})