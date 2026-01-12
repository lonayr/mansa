from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    name = StringField("الاسم", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("البريد الإلكتروني", validators=[DataRequired(), Email()])
    password = PasswordField("كلمة المرور", validators=[DataRequired(), Length(min=6)])
    category = SelectField("الفئة", coerce=int)
    submit = SubmitField("تسجيل")

class LoginForm(FlaskForm):
    email = StringField("البريد الإلكتروني", validators=[DataRequired(), Email()])
    password = PasswordField("كلمة المرور", validators=[DataRequired()])
    submit = SubmitField("تسجيل الدخول")

class ProfileImageForm(FlaskForm):
    image = FileField("صورة البروفايل")
    submit = SubmitField("رفع")
