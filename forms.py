from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional
from flask_wtf.file import FileAllowed

class RegisterForm(FlaskForm):
    name = StringField("الاسم الكامل", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("البريد الإلكتروني", validators=[DataRequired(), Email()])
    password = PasswordField("كلمة المرور", validators=[DataRequired(), Length(min=6)])
    category = SelectField("التصنيف", coerce=int, validators=[DataRequired()])
    submit = SubmitField("إنشاء الحساب")

class LoginForm(FlaskForm):
    email = StringField("البريد الإلكتروني", validators=[DataRequired(), Email()])
    password = PasswordField("كلمة المرور", validators=[DataRequired()])
    submit = SubmitField("تسجيل الدخول")

class CourseForm(FlaskForm):
    title = StringField("عنوان الكورس", validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField("وصف الكورس", validators=[DataRequired(), Length(min=10)])
    category = StringField("التصنيف", validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField("إضافة الكورس")

class UploadCourseForm(FlaskForm):
    file = FileField("ملف الكورس (فيديو أو PDF)", validators=[
        DataRequired(),
        FileAllowed({"mp4", "mov", "mkv", "webm", "pdf"}, "يُسمح بملفات الفيديو أو PDF فقط.")
    ])
    submit = SubmitField("رفع الملف")

class ProfileImageForm(FlaskForm):
    profile_image = FileField("صورة البروفايل", validators=[
        FileAllowed({"png", "jpg", "jpeg", "gif"}, "يُسمح بصور PNG/JPG/GIF فقط.")
    ])
    submit = SubmitField("تحديث الصورة")

class StudentProfileForm(FlaskForm):
    level = StringField("المستوى الدراسي", validators=[Optional(), Length(max=100)])
    school = StringField("المدرسة", validators=[Optional(), Length(max=200)])
    phone = StringField("رقم الهاتف", validators=[Optional(), Length(max=30)])
    birth_date = DateField("تاريخ الميلاد", format="%Y-%m-%d", validators=[Optional()])
    gender = SelectField("الجنس", choices=[("ذكر", "ذكر"), ("أنثى", "أنثى")], validators=[Optional()])
    city = StringField("المدينة", validators=[Optional(), Length(max=100)])
    submit = SubmitField("حفظ بيانات الطالب")

class SettingsForm(FlaskForm):
    platform_name = StringField("اسم المنصة", validators=[DataRequired(), Length(max=200)])
    platform_description = TextAreaField("وصف المنصة", validators=[Optional()])
    support_email = StringField("بريد الدعم", validators=[Optional(), Length(max=200)])
    logo = FileField("شعار المنصة", validators=[
        FileAllowed({"png", "jpg", "jpeg", "gif"}, "يُسمح بصور PNG/JPG/GIF فقط.")
    ])
    submit = SubmitField("حفظ الإعدادات")
