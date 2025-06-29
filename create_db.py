from app import app, db

with app.app_context():
    # إنشاء جميع الجداول
    db.create_all()
    print("تم إنشاء قاعدة البيانات بنجاح!")
    print("الجدول الجديد 'TIP' تم إنشاؤه مع العلاقة مع المستخدم.") 