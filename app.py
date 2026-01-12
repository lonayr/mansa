from flask import Flask, render_template, redirect, url_for, flash, session, request
from functools import wraps
from config import Config
from models import db, User, UserCat, Notification
from forms import RegisterForm, LoginForm, ProfileImageForm
from utils import save_file

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # إنشاء الجداول والتصنيفات والحسابات الافتراضية
    with app.app_context():
        db.create_all()

        # تصنيفات أساسية
        default_cats = ["مدير", "مدرس", "طالب"]
        for c in default_cats:
            if not UserCat.query.filter_by(name=c).first():
                db.session.add(UserCat(name=c, description=f"تصنيف {c}"))
        db.session.commit()

        # حساب مطوّر افتراضي
        if not User.query.filter_by(email="dev@edu.local").first():
            dev_cat = UserCat.query.filter_by(name="مدير").first()
            dev = User(
                name="المطور",
                email="dev@edu.local",
                is_developer=True,
                is_active=True,
                category_id=dev_cat.id
            )
            dev.set_password("Dev123!")
            db.session.add(dev)
            db.session.commit()

    # تمرير المستخدم والإشعارات للقوالب
    @app.context_processor
    def inject_globals():
        user = User.query.get(session["user_id"]) if "user_id" in session else None
        notif_count = 0
        if user:
            notif_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        return dict(current_user=user, notif_count=notif_count)

    # ديكوراتور: تسجيل الدخول مطلوب
    def login_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("الرجاء تسجيل الدخول.", "warning")
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        return wrapper

    # ديكوراتور: المطوّر فقط
    def dev_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = User.query.get(session.get("user_id"))
            if not user or not user.is_developer:
                flash("هذه الصفحة للمطور فقط.", "danger")
                return redirect(url_for("index"))
            return func(*args, **kwargs)
        return wrapper

    # ديكوراتور: المدير فقط
    def admin_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = User.query.get(session.get("user_id"))
            if not user or not user.is_admin or not user.is_active:
                flash("هذه الصفحة للمدير فقط.", "danger")
                return redirect(url_for("index"))
            return func(*args, **kwargs)
        return wrapper

    # الصفحة الرئيسية
    @app.route("/")
    def index():
        return render_template("index.html")

    # التسجيل
    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        cats = UserCat.query.order_by(UserCat.name.asc()).all()
        form.category.choices = [(c.id, c.name) for c in cats]

        if form.validate_on_submit():
            # تحقق من عدم تكرار البريد
            if User.query.filter_by(email=form.email.data).first():
                flash("البريد الإلكتروني مستخدم بالفعل.", "danger")
                return redirect(url_for("register"))

            # إنشاء المستخدم
            user = User(
                name=form.name.data,
                email=form.email.data,
                category_id=form.category.data
            )
            user.set_password(form.password.data)

            cat = UserCat.query.get(user.category_id)

            # منطق الموافقات والإشعارات
            if cat and cat.name == "مدير":
                user.is_admin = True
                user.is_active = False
                user.pending_approval = True
                dev = User.query.filter_by(is_developer=True).first()
                if dev:
                    db.session.add(Notification(
                        user_id=dev.id,
                        message=f"طلب جديد لإنشاء مدير: {user.name}"
                    ))

            elif cat and cat.name == "مدرس":
                user.is_active = False
                user.pending_approval = True
                admin = User.query.filter_by(is_admin=True, is_active=True).first()
                if admin:
                    db.session.add(Notification(
                        user_id=admin.id,
                        message=f"طلب جديد لإنشاء مدرس: {user.name}"
                    ))

            else:  # طالب
                user.is_active = True
                user.pending_approval = False

            db.session.add(user)
            db.session.commit()

            flash("تم إنشاء الحساب، بانتظار الموافقة إذا لزم الأمر.", "info")
            return redirect(url_for("login"))

        return render_template("register.html", form=form)

    # تسجيل الدخول
    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if not user or not user.check_password(form.password.data):
                flash("بيانات الدخول غير صحيحة.", "danger")
                return redirect(url_for("login"))
            if not user.is_active:
                flash("حسابك غير مفعل بعد. يرجى انتظار الموافقة.", "warning")
                return redirect(url_for("login"))
            session["user_id"] = user.id
            flash("تم تسجيل الدخول بنجاح.", "success")
            return redirect(url_for("index"))
        return render_template("login.html", form=form)

    # تسجيل الخروج
    @app.route("/logout")
    @login_required
    def logout():
        session.pop("user_id", None)
        flash("تم تسجيل الخروج.", "info")
        return redirect(url_for("index"))

    # لوحة المطور: طلبات المديرين
    @app.route("/developer/requests")
    @login_required
    @dev_required
    def developer_requests():
        pending_admins = User.query.filter_by(is_admin=True, pending_approval=True).all()
        return render_template("developer_requests.html", pending_admins=pending_admins)

    @app.route("/developer/approve/<int:user_id>")
    @login_required
    @dev_required
    def developer_approve(user_id):
        u = User.query.get_or_404(user_id)
        if not u.is_admin:
            flash("هذا الطلب ليس لمدير.", "warning")
            return redirect(url_for("developer_requests"))
        u.is_active = True
        u.pending_approval = False
        db.session.commit()
        flash("تمت الموافقة على المدير.", "success")
        return redirect(url_for("developer_requests"))

    @app.route("/developer/reject/<int:user_id>")
    @login_required
    @dev_required
    def developer_reject(user_id):
        u = User.query.get_or_404(user_id)
        if not u.is_admin:
            flash("هذا الطلب ليس لمدير.", "warning")
            return redirect(url_for("developer_requests"))
        db.session.delete(u)
        db.session.commit()
        flash("تم رفض طلب المدير.", "danger")
        return redirect(url_for("developer_requests"))

    # لوحة المدير: طلبات المدرسين
    @app.route("/admin/requests")
    @login_required
    @admin_required
    def admin_requests():
        pending_teachers = User.query.filter_by(pending_approval=True, is_admin=False).all()
        return render_template("admin_requests.html", pending_teachers=pending_teachers)

    @app.route("/admin/approve/<int:user_id>")
    @login_required
    @admin_required
    def admin_approve(user_id):
        u = User.query.get_or_404(user_id)
        if u.is_admin:
            flash("هذا المستخدم ليس مدرس.", "warning")
            return redirect(url_for("admin_requests"))
        u.is_active = True
        u.pending_approval = False
        db.session.commit()
        flash("تمت الموافقة على المدرس.", "success")
        return redirect(url_for("admin_requests"))

    @app.route("/admin/reject/<int:user_id>")
    @login_required
    @admin_required
    def admin_reject(user_id):
        u = User.query.get_or_404(user_id)
        if u.is_admin:
            flash("هذا المستخدم ليس مدرس.", "warning")
            return redirect(url_for("admin_requests"))
        db.session.delete(u)
        db.session.commit()
        flash("تم رفض طلب المدرس.", "danger")
        return redirect(url_for("admin_requests"))

    # رفع صورة البروفايل (مثال)
    @app.route("/profile/upload", methods=["GET", "POST"])
    @login_required
    def profile_upload():
        form = ProfileImageForm()
        if request.method == "POST":
            try:
                file = request.files.get("image")
                path = save_file(file, Config.PROFILE_UPLOAD_FOLDER, Config.IMAGE_ALLOWED_EXTENSIONS)
                if path:
                    flash("تم رفع الصورة بنجاح.", "success")
                else:
                    flash("يرجى اختيار ملف.", "warning")
            except ValueError as e:
                flash(str(e), "danger")
        return render_template("profile_upload.html", form=form)

    # الإشعارات
    @app.route("/notifications")
    @login_required
    def notifications():
        user = User.query.get(session["user_id"])
        notes = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
        return render_template("notifications.html", notifications=notes)

    @app.route("/notifications/read/<int:notif_id>")
    @login_required
    def mark_notification_read(notif_id):
        n = Notification.query.get_or_404(notif_id)
        if n.user_id != session.get("user_id"):
            flash("غير مسموح.", "danger")
            return redirect(url_for("notifications"))
        n.is_read = True
        db.session.commit()
        return redirect(url_for("notifications"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
