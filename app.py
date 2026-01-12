from flask import Flask, render_template, redirect, url_for, flash, session, request, send_from_directory
from datetime import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Course, UserCat, CourseVisit, StudentProfile, Settings
from forms import RegisterForm, LoginForm, CourseForm, UploadCourseForm, ProfileImageForm, StudentProfileForm, SettingsForm

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    for folder in (app.config["UPLOAD_FOLDER"], app.config["PROFILE_UPLOAD_FOLDER"], app.config["SETTINGS_FOLDER"]):
        os.makedirs(folder, exist_ok=True)

    with app.app_context():
        db.create_all()
        for name in ["طالب", "مدرس", "مدير"]:
            if not UserCat.query.filter_by(name=name).first():
                db.session.add(UserCat(name=name, description=f"تصنيف {name}"))
        db.session.commit()
        if not User.query.filter_by(email="admin@edu.local").first():
            admin_cat = UserCat.query.filter_by(name="مدير").first()
            admin = User(name="مدير", email="admin@edu.local", is_admin=True, category_id=admin_cat.id)
            admin.set_password("Admin123!")
            db.session.add(admin)
            db.session.commit()
        if not Settings.query.first():
            db.session.add(Settings(platform_name="منصة التعليم", platform_description="تعلم بسهولة مع محتوى عربي.", support_email="support@edu.local"))
            db.session.commit()

    @app.context_processor
    def inject_globals():
        user = User.query.get(session["user_id"]) if "user_id" in session else None
        settings = Settings.query.first()
        return dict(current_user=user, settings=settings)

    def login_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("الرجاء تسجيل الدخول للوصول إلى هذه الصفحة.", "warning")
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        return wrapper

    def admin_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("الرجاء تسجيل الدخول.", "warning")
                return redirect(url_for("login"))
            user = User.query.get(session["user_id"])
            if not user or not user.is_admin:
                flash("هذه الصفحة للمدير فقط.", "danger")
                return redirect(url_for("index"))
            return func(*args, **kwargs)
        return wrapper

    @app.route("/")
    def index():
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        courses = Course.query.order_by(Course.created_at.desc())
        if q:
            courses = courses.filter(Course.title.ilike(f"%{q}%"))
        if category:
            courses = courses.filter(Course.category.ilike(f"%{category}%"))
        return render_template("index.html", courses=courses.all(), q=q, category=category)

    @app.route("/course/<int:course_id>")
    @login_required
    def course_detail(course_id):
        course = Course.query.get_or_404(course_id)
        visit = CourseVisit(user_id=session.get("user_id"), course_id=course.id, timestamp=datetime.utcnow())
        db.session.add(visit)
        db.session.commit()
        visits_count = CourseVisit.query.filter_by(course_id=course.id).count()
        latest_visits = CourseVisit.query.filter_by(course_id=course.id).order_by(CourseVisit.timestamp.desc()).limit(10).all()
        return render_template("course_detail.html", course=course, visits_count=visits_count, latest_visits=latest_visits)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        cats = UserCat.query.order_by(UserCat.name.asc()).all()
        form.category.choices = [(c.id, c.name) for c in cats]

        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                flash("البريد الإلكتروني مستخدم بالفعل.", "danger")
                return redirect(url_for("register"))
            user = User(name=form.name.data, email=form.email.data, category_id=form.category.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            cat = UserCat.query.get(user.category_id)
            if cat and cat.name == "طالب":
                db.session.add(StudentProfile(user_id=user.id))
                db.session.commit()
            session["user_id"] = user.id
            flash("تم إنشاء الحساب وتم تسجيل دخولك تلقائيًا.", "success")
            return redirect(url_for("profile"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                session["user_id"] = user.id
                flash("تم تسجيل الدخول بنجاح.", "success")
                return redirect(url_for("profile"))
            flash("بيانات الدخول غير صحيحة.", "danger")
        return render_template("login.html", form=form)

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("تم تسجيل الخروج.", "info")
        return redirect(url_for("index"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        user = User.query.get_or_404(session["user_id"])
        image_form = ProfileImageForm()
        student_form = StudentProfileForm()
        sp = StudentProfile.query.filter_by(user_id=user.id).first()

        if request.method == "POST":
            bio = request.form.get("bio")
            if bio is not None:
                user.bio = bio

            if image_form.profile_image.data:
                filename = secure_filename(image_form.profile_image.data.filename)
                path = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename)
                image_form.profile_image.data.save(path)
                user.profile_image = filename

            if sp:
                sp.level = student_form.level.data
                sp.school = student_form.school.data
                sp.phone = student_form.phone.data
                sp.birth_date = student_form.birth_date.data
                sp.gender = student_form.gender.data
                sp.city = student_form.city.data
            else:
                sp = StudentProfile(
                    user_id=user.id,
                    level=student_form.level.data,
                    school=student_form.school.data,
                    phone=student_form.phone.data,
                    birth_date=student_form.birth_date.data,
                    gender=student_form.gender.data,
                    city=student_form.city.data
                )
                db.session.add(sp)

            db.session.commit()
            flash("تم تحديث البروفايل وبيانات الطالب.", "success")
            return redirect(url_for("profile"))

        if sp:
            student_form.level.data = sp.level
            student_form.school.data = sp.school
            student_form.phone.data = sp.phone
            student_form.birth_date.data = sp.birth_date
            student_form.gender.data = sp.gender
            student_form.city.data = sp.city

        my_courses = Course.query.filter_by(author_id=user.id).order_by(Course.created_at.desc()).all()
        my_visits = CourseVisit.query.filter_by(user_id=user.id).order_by(CourseVisit.timestamp.desc()).limit(50).all()
        return render_template("profile.html", user=user, my_courses=my_courses, my_visits=my_visits, image_form=image_form, student_form=student_form)

    @app.route("/add-course", methods=["GET", "POST"])
    @admin_required
    def add_course():
        form = CourseForm()
        if form.validate_on_submit():
            course = Course(title=form.title.data, description=form.description.data, category=form.category.data, author_id=session.get("user_id"))
            db.session.add(course)
            db.session.commit()
            flash("تم إضافة الكورس بنجاح.", "success")
            return redirect(url_for("upload_course", course_id=course.id))
        return render_template("add_course.html", form=form)

    @app.route("/upload-course/<int:course_id>", methods=["GET", "POST"])
    @admin_required
    def upload_course(course_id):
        course = Course.query.get_or_404(course_id)
        form = UploadCourseForm()
        if form.validate_on_submit():
            file = form.file.data
            if file:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(path)
                course.file_url = filename
                db.session.commit()
                flash("تم رفع ملف الكورس وربطه بنجاح.", "success")
                return redirect(url_for("course_detail", course_id=course.id))
            flash("فضلاً اختر ملفًا صالحًا.", "warning")
        return render_template("upload_course.html", course=course, form=form)

    @app.route("/admin/settings", methods=["GET", "POST"])
    @admin_required
    def admin_settings():
        settings = Settings.query.first()
        form = SettingsForm()
        if request.method == "POST" and form.validate_on_submit():
            settings.platform_name = form.platform_name.data
            settings.platform_description = form.platform_description.data
            settings.support_email = form.support_email.data
            if form.logo.data:
                filename = secure_filename(form.logo.data.filename)
                path = os.path.join(app.config["SETTINGS_FOLDER"], filename)
                form.logo.data.save(path)
                settings.logo_filename = filename
            db.session.commit()
            flash("تم تحديث إعدادات المنصة.", "success")
            return redirect(url_for("admin_settings"))

        form.platform_name.data = settings.platform_name
        form.platform_description.data = settings.platform_description
        form.support_email.data = settings.support_email
        return render_template("settings.html", form=form, settings=settings)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/profile_images/<path:filename>")
    def profile_image(filename):
        return send_from_directory(app.config["PROFILE_UPLOAD_FOLDER"], filename)

    @app.route("/settings_files/<path:filename>")
    def settings_file(filename):
        return send_from_directory(app.config["SETTINGS_FOLDER"], filename)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
