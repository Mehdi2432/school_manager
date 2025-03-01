from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hmac
import hashlib

class AcademicYear(models.Model):
    year = models.CharField(max_length=9, unique=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.year

class License(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_key = models.CharField(max_length=50, unique=True, blank=True)
    license_file = models.FileField(upload_to='licenses/', null=True, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_trial = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        if not self.license_key and not self.license_file:
            import uuid
            self.license_key = str(uuid.uuid4())[:8].upper()
        if not self.start_date:
            self.start_date = timezone.now()
        if self.is_trial and not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
    def is_active(self):
        return self.end_date > timezone.now() if self.end_date else True
    def validate_license(self):
        if self.license_file:
            return self.license_key == "VALID_LICENSE"
        return self.is_active()
    def __str__(self):
        return f"{self.user.username} - {self.license_key or 'Trial'}"

class UserProfile(models.Model):
    ROLES = (
        ('school', 'مدرسه'),
        ('teacher', 'معلم'),
        ('parent', 'والدین'),
        ('student', 'دانش‌آموز'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES)
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class School(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=50)
    address = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.name} - {self.academic_year}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    schools = models.ManyToManyField(School, related_name='teachers')
    def __str__(self):
        return self.name

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    def __str__(self):
        return self.name

class StudentUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=100)
    grade = models.CharField(max_length=10)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class Student(models.Model):
    name = models.CharField(max_length=100)
    grade = models.CharField(max_length=10)
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    school = models.ForeignKey('School', on_delete=models.CASCADE)
    student_user = models.ForeignKey('StudentUser', on_delete=models.SET_NULL, null=True, blank=True)
    attendance = models.BooleanField(default=True)
    def __str__(self):
        return self.name

class Class(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    grade = models.CharField(max_length=10)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    students = models.ManyToManyField('Student')
    def __str__(self):
        return f"{self.subject} - {self.grade} - {self.name}"

class Session(models.Model):
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    session_number = models.PositiveIntegerField(default=1)
    class Meta:
        unique_together = ('class_obj', 'date')
    def save(self, *args, **kwargs):
        if not self.pk:
            last_session = Session.objects.filter(class_obj=self.class_obj).order_by('-session_number').first()
            if last_session and last_session.date != self.date:
                self.session_number = last_session.session_number + 1
            elif not last_session:
                self.session_number = 1
        super().save(*args, **kwargs)
    def __str__(self):
        return f"جلسه {self.session_number} - {self.date}"

class StudentSession(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    attendance = models.BooleanField(default=True)
    daily_grade = models.FloatField(null=True, blank=True)
    discipline = models.CharField(max_length=10, choices=[('positive', 'مثبت'), ('negative', 'منفی')], null=True, blank=True)
    activity = models.ForeignKey('ClassActivity', on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        unique_together = ('session', 'student')
    def __str__(self):
        return f"{self.student.name} - {self.session}"

class Schedule(models.Model):
    class_session = models.ForeignKey(Class, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=[
        ('شنبه', 'شنبه'), ('یکشنبه', 'یکشنبه'), ('دوشنبه', 'دوشنبه'),
        ('سه‌شنبه', 'سه‌شنبه'), ('چهارشنبه', 'چهارشنبه'), ('پنج‌شنبه', 'پنج‌شنبه'),
        ('جمعه', 'جمعه')
    ])
    period = models.IntegerField(choices=[(1, 'زنگ 1'), (2, 'زنگ 2'), (3, 'زنگ 3'), (4, 'زنگ 4')])
    def __str__(self):
        return f"{self.class_session} - {self.day} - زنگ {self.period}"

class TeacherSettings(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)  # اجازه می‌ده تنظیمات عمومی یا خاص کلاس باشه
    grade_min = models.FloatField(default=0)
    grade_max = models.FloatField(default=20)
    positive_value = models.FloatField(default=1)
    negative_value = models.FloatField(default=1)
    def __str__(self):
        if self.class_obj:
            return f"تنظیمات {self.teacher.name} برای کلاس {self.class_obj.name}"
        return f"تنظیمات عمومی {self.teacher.name}"

class ClassActivity(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)  # اضافه کردن فیلد class_obj
    name = models.CharField(max_length=100)
    value = models.FloatField(default=0)
    def __str__(self):
        return self.name