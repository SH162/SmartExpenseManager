from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os
from config import Config

# استيراد المستشار المالي الذكي
try:
    from ai_advisor import AIFinancialAdvisor, get_ai_advice, get_ai_analysis, get_ai_tips
    AI_ADVISOR_AVAILABLE = True
except ImportError:
    AI_ADVISOR_AVAILABLE = False
    print("⚠️ تحذير: المستشار المالي الذكي غير متاح")

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# نماذج قاعدة البيانات
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)
    tips = db.relationship('Tip', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # income/expense
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    spent = db.Column(db.Float, default=0.0)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Tip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # saving, spending, investment, etc.
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    is_read = db.Column(db.Boolean, default=False)
    is_applied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applied_at = db.Column(db.DateTime, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# دوال مساعدة
def format_currency(amount):
    try:
        # تحويل المبلغ إلى رقم عشري
        amount = float(amount)
        # تنسيق الرقم مع فواصل الآلاف و 3 أرقام عشرية
        formatted_number = f"{amount:,.3f}"
        return f"{formatted_number} د.ل"
    except (ValueError, TypeError):
        # في حالة الخطأ، إرجاع القيمة كما هي
        return f"{amount} د.ل"

def get_month_range():
    today = datetime.now()
    month_start = datetime(today.year, today.month, 1, 0, 0, 0)
    if today.month == 12:
        next_month = datetime(today.year + 1, 1, 1, 0, 0, 0)
    else:
        next_month = datetime(today.year, today.month + 1, 1, 0, 0, 0)
    month_end = next_month - timedelta(seconds=1)  # آخر ثانية في الشهر الحالي
    return month_start, month_end

def generate_simple_tips(user_data):
    """
    توليد نصائح بسيطة بناءً على البيانات المالية
    """
    tips = []
    
    # نصيحة حول المصروفات العالية
    if user_data['monthly_expenses'] > 1000:
        tips.append({
            'title': 'مصروفاتك الشهرية مرتفعة',
            'content': f'مصروفاتك الشهرية {user_data["monthly_expenses"]} دينار مرتفعة. فكر في تقليل المصروفات غير الضرورية ووضع ميزانية أكثر صرامة.',
            'category': 'spending',
            'priority': 'high'
        })
    
    # نصيحة حول نسبة الادخار
    if user_data['savings_rate'] < 20:
        tips.append({
            'title': 'نسبة الادخار منخفضة',
            'content': f'نسبة ادخارك {user_data["savings_rate"]}% منخفضة. حاول الوصول إلى 20% على الأقل من دخلك الشهري.',
            'category': 'saving',
            'priority': 'medium'
        })
    
    # نصائح حول الفئات الأكثر إنفاقاً
    for category, amount in user_data['top_categories']:
        if amount > user_data['monthly_expenses'] * 0.3:
            tips.append({
                'title': f'إنفاق مرتفع في {category}',
                'content': f'أنت تنفق {amount} دينار في {category}، وهو ما يمثل نسبة كبيرة من مصروفاتك.',
                'category': 'spending',
                'priority': 'medium'
            })
    
    # نصيحة عامة حول الميزانية
    if user_data['budgets']:
        tips.append({
            'title': 'مراجعة الميزانيات',
            'content': 'راجع ميزانياتك الشهرية وتأكد من عدم تجاوز الحدود المحددة.',
            'category': 'budget',
            'priority': 'medium'
        })
    
    # نصيحة حول الأهداف المالية
    if user_data['goals']:
        tips.append({
            'title': 'تتبع الأهداف المالية',
            'content': 'تابع تقدم أهدافك المالية وخصص جزءاً من دخلك لتحقيقها.',
            'category': 'goals',
            'priority': 'medium'
        })
    
    return tips

# معالجة الأخطاء
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# المسارات
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            
            if not username or not email or not password:
                flash('جميع الحقول مطلوبة')
                return redirect(url_for('register'))
            
            if User.query.filter_by(username=username).first():
                flash('اسم المستخدم موجود مسبقاً')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('البريد الإلكتروني موجود مسبقاً')
                return redirect(url_for('register'))
            
            user = User(username=username, email=email, 
                       password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            
            flash('تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التسجيل')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            if not username or not password:
                flash('اسم المستخدم وكلمة المرور مطلوبان')
                return redirect(url_for('login'))
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('اسم المستخدم أو كلمة المرور غير صحيحة')
        except Exception as e:
            flash('حدث خطأ أثناء تسجيل الدخول')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # إحصائيات سريعة
        today = datetime.now().date()
        month_start, month_end = get_month_range()
        
        # إحصائيات الشهر الحالي
        monthly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= month_start,
            Transaction.date <= month_end
        ).scalar() or 0
        
        monthly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'income',
            Transaction.date >= month_start,
            Transaction.date <= month_end
        ).scalar() or 0
        
        # إحصائيات الأسبوع الحالي
        week_start = today - timedelta(days=today.weekday())
        weekly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= week_start
        ).scalar() or 0
        
        # إحصائيات اليوم
        daily_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= today
        ).scalar() or 0
        
        # المعاملات الأخيرة
        recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.date.desc()).limit(5).all()
        
        # أفضل الفئات إنفاقاً
        top_categories = db.session.query(
            Transaction.category,
            db.func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= month_start,
            Transaction.date <= month_end
        ).group_by(Transaction.category)\
         .order_by(db.func.sum(Transaction.amount).desc())\
         .limit(5).all()
        
        # حالة الميزانية
        budgets = Budget.query.filter_by(
            user_id=current_user.id,
            month=month_start.strftime('%Y-%m')
        ).all()
        
        # الأهداف المالية النشطة
        active_goals = Goal.query.filter_by(user_id=current_user.id)\
            .filter(Goal.deadline >= today)\
            .order_by(Goal.deadline).limit(3).all()
        
        return render_template('dashboard.html', 
                             today=today,
                             monthly_expenses=monthly_expenses,
                             monthly_income=monthly_income,
                             weekly_expenses=weekly_expenses,
                             daily_expenses=daily_expenses,
                             recent_transactions=recent_transactions,
                             top_categories=top_categories,
                             budgets=budgets,
                             active_goals=active_goals,
                             format_currency=format_currency)
    except Exception as e:
        flash('حدث خطأ أثناء تحميل لوحة التحكم')
        return render_template('dashboard.html', 
                             today=datetime.now().date(),
                             monthly_expenses=0,
                             monthly_income=0,
                             weekly_expenses=0,
                             daily_expenses=0,
                             recent_transactions=[],
                             top_categories=[],
                             budgets=[],
                             active_goals=[],
                             format_currency=format_currency)

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            type = request.form['type']
            category = request.form['category']
            description = request.form.get('description', '')
            date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            
            if amount <= 0:
                flash('المبلغ يجب أن يكون أكبر من صفر')
                return redirect(url_for('add_transaction'))
            
            transaction = Transaction(
                user_id=current_user.id,
                amount=amount,
                type=type,
                category=category,
                description=description,
                date=date
            )
            
            db.session.add(transaction)
            
            # تحديث الميزانية إذا كانت المعاملة إنفاقاً
            if type == 'expense':
                month_key = date.strftime('%Y-%m')
                budget = Budget.query.filter_by(
                    user_id=current_user.id,
                    category=category,
                    month=month_key
                ).first()
                
                if budget:
                    budget.spent += amount
            
            db.session.commit()
            
            flash('تم إضافة المعاملة بنجاح')
            return redirect(url_for('transactions'))
        except ValueError:
            flash('البيانات المدخلة غير صحيحة')
            return redirect(url_for('add_transaction'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة المعاملة')
            return redirect(url_for('add_transaction'))
    
    today = datetime.now().date()
    return render_template('add_transaction.html', today=today)

@app.route('/transactions')
@login_required
def transactions():
    try:
        page = request.args.get('page', 1, type=int)
        transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.date.desc()).paginate(page=page, per_page=20, error_out=False)
        return render_template('transactions.html', 
                             transactions=transactions,
                             format_currency=format_currency)
    except Exception as e:
        flash('حدث خطأ أثناء تحميل المعاملات')
        return render_template('transactions.html', 
                             transactions=None,
                             format_currency=format_currency)

@app.route('/transaction/<int:transaction_id>')
@login_required
def view_transaction(transaction_id):
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        if transaction.user_id != current_user.id:
            flash('غير مسموح لك بعرض هذه المعاملة')
            return redirect(url_for('transactions'))
        
        return jsonify({
            'id': transaction.id,
            'amount': transaction.amount,
            'type': transaction.type,
            'category': transaction.category,
            'description': transaction.description or 'لا يوجد وصف',
            'date': transaction.date.strftime('%Y-%m-%d %H:%M'),
            'formatted_amount': format_currency(transaction.amount)
        })
    except Exception as e:
        return jsonify({'error': 'حدث خطأ أثناء جلب تفاصيل المعاملة'}), 500

@app.route('/transaction/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        if transaction.user_id != current_user.id:
            flash('غير مسموح لك بتعديل هذه المعاملة')
            return redirect(url_for('transactions'))
        
        if request.method == 'POST':
            amount = float(request.form['amount'])
            type_ = request.form['type']
            category = request.form['category']
            description = request.form.get('description', '')
            date_str = request.form['date']
            
            if amount <= 0:
                flash('المبلغ يجب أن يكون أكبر من صفر')
                return redirect(url_for('edit_transaction', transaction_id=transaction_id))
            
            transaction.amount = amount
            transaction.type = type_
            transaction.category = category
            transaction.description = description
            transaction.date = datetime.strptime(date_str, '%Y-%m-%d')
            
            db.session.commit()
            flash('تم تحديث المعاملة بنجاح')
            return redirect(url_for('transactions'))
        
        # GET request - عرض نموذج التعديل
        return render_template('edit_transaction.html', 
                             transaction=transaction,
                             format_currency=format_currency)
    except ValueError:
        flash('البيانات المدخلة غير صحيحة')
        return redirect(url_for('edit_transaction', transaction_id=transaction_id))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تحديث المعاملة')
        return redirect(url_for('transactions'))

@app.route('/transaction/delete/<int:transaction_id>')
@login_required
def delete_transaction(transaction_id):
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        if transaction.user_id != current_user.id:
            flash('غير مسموح لك بحذف هذه المعاملة')
            return redirect(url_for('transactions'))
        
        db.session.delete(transaction)
        db.session.commit()
        flash('تم حذف المعاملة بنجاح')
        return redirect(url_for('transactions'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف المعاملة')
        return redirect(url_for('transactions'))

@app.route('/reports')
@login_required
def reports():
    try:
        print(f"=== تشخيص التقارير للمستخدم {current_user.id} ===")
        
        # بيانات للرسوم البيانية
        month_start, month_end = get_month_range()
        print(f"نطاق الشهر: {month_start} إلى {month_end}")
        
        # فئات الإنفاق للشهر الحالي
        categories = db.session.query(Transaction.category, db.func.sum(Transaction.amount))\
            .filter(Transaction.user_id == current_user.id, 
                    Transaction.type == 'expense',
                    Transaction.date >= month_start,
                    Transaction.date <= month_end)\
            .group_by(Transaction.category)\
            .order_by(db.func.sum(Transaction.amount).desc()).all()
        
        print(f"فئات الإنفاق للشهر الحالي: {len(categories)} فئة")
        
        # البيانات الشهرية - آخر 6 أشهر
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = db.session.query(
            db.func.strftime('%Y-%m', Transaction.date).label('month'),
            db.func.sum(db.case((Transaction.type == 'income', Transaction.amount), else_=0)).label('income'),
            db.func.sum(db.case((Transaction.type == 'expense', Transaction.amount), else_=0)).label('expense')
        ).filter(Transaction.user_id == current_user.id,
                Transaction.date >= six_months_ago)\
         .group_by(db.func.strftime('%Y-%m', Transaction.date))\
         .order_by(db.func.strftime('%Y-%m', Transaction.date)).all()
        
        print(f"البيانات الشهرية: {len(monthly_data)} شهر")
        
        # تحويل البيانات الشهرية إلى تنسيق مناسب
        formatted_monthly_data = []
        for data in monthly_data:
            month_name = datetime.strptime(data.month, '%Y-%m').strftime('%B %Y')
            formatted_monthly_data.append({
                'month': month_name,
                'income': float(data.income),
                'expense': float(data.expense)
            })
        
        # إحصائيات إضافية للشهر الحالي
        current_month_income = db.session.query(db.func.sum(Transaction.amount))\
            .filter(Transaction.user_id == current_user.id, 
                   Transaction.type == 'income',
                   Transaction.date >= month_start,
                   Transaction.date <= month_end).scalar() or 0
        
        current_month_expenses = db.session.query(db.func.sum(Transaction.amount))\
            .filter(Transaction.user_id == current_user.id, 
                   Transaction.type == 'expense',
                   Transaction.date >= month_start,
                   Transaction.date <= month_end).scalar() or 0
        
        print(f"دخل الشهر الحالي: {current_month_income}")
        print(f"مصروفات الشهر الحالي: {current_month_expenses}")
        
        # إحصائيات إجمالية
        total_income = db.session.query(db.func.sum(Transaction.amount))\
            .filter(Transaction.user_id == current_user.id, Transaction.type == 'income').scalar() or 0
        
        total_expenses = db.session.query(db.func.sum(Transaction.amount))\
            .filter(Transaction.user_id == current_user.id, Transaction.type == 'expense').scalar() or 0
        
        print(f"إجمالي الدخل: {total_income}")
        print(f"إجمالي المصروفات: {total_expenses}")
        
        # التحقق من وجود معاملات
        total_transactions = Transaction.query.filter_by(user_id=current_user.id).count()
        print(f"إجمالي المعاملات للمستخدم: {total_transactions}")
        
        # فحص المعاملات حسب النوع
        income_count = Transaction.query.filter_by(user_id=current_user.id, type='income').count()
        expense_count = Transaction.query.filter_by(user_id=current_user.id, type='expense').count()
        print(f"معاملات الدخل: {income_count}")
        print(f"معاملات المصروفات: {expense_count}")
        
        # فحص أول 3 معاملات للمستخدم
        first_transactions = Transaction.query.filter_by(user_id=current_user.id).limit(3).all()
        print("أول 3 معاملات:")
        for trans in first_transactions:
            print(f"  - {trans.type}: {trans.amount} - {trans.category} - {trans.date}")
        
        return render_template('reports.html', 
                             categories=categories, 
                             monthly_data=formatted_monthly_data,
                             total_income=total_income,
                             total_expenses=total_expenses,
                             current_month_income=current_month_income,
                             current_month_expenses=current_month_expenses,
                             format_currency=format_currency)
    except Exception as e:
        print(f"خطأ في التقارير: {e}")
        flash('حدث خطأ أثناء تحميل التقارير')
        return render_template('reports.html', 
                             categories=[], 
                             monthly_data=[],
                             total_income=0,
                             total_expenses=0,
                             current_month_income=0,
                             current_month_expenses=0,
                             format_currency=format_currency)

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    if request.method == 'POST':
        try:
            category = request.form['category']
            amount = float(request.form['amount'])
            month = request.form['month']
            
            if amount <= 0:
                flash('المبلغ يجب أن يكون أكبر من صفر')
                return redirect(url_for('budget'))
            
            # التحقق من وجود ميزانية للفئة والشهر
            existing_budget = Budget.query.filter_by(
                user_id=current_user.id,
                category=category,
                month=month
            ).first()
            
            if existing_budget:
                existing_budget.amount = amount
            else:
                budget = Budget(
                    user_id=current_user.id,
                    category=category,
                    amount=amount,
                    month=month
                )
                db.session.add(budget)
            
            db.session.commit()
            flash('تم حفظ الميزانية بنجاح')
            return redirect(url_for('budget'))
        except ValueError:
            flash('البيانات المدخلة غير صحيحة')
            return redirect(url_for('budget'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء حفظ الميزانية')
            return redirect(url_for('budget'))
    
    try:
        # الحصول على الميزانيات الحالية
        current_month = datetime.now().strftime('%Y-%m')
        budgets = Budget.query.filter_by(
            user_id=current_user.id,
            month=current_month
        ).all()
        
        # حساب المبالغ المنفقة لكل فئة
        month_start, month_end = get_month_range()
        for budget in budgets:
            spent = db.session.query(db.func.sum(Transaction.amount))\
                .filter(Transaction.user_id == current_user.id,
                       Transaction.type == 'expense',
                       Transaction.category == budget.category,
                       Transaction.date >= month_start,
                       Transaction.date <= month_end).scalar() or 0
            budget.spent = spent
        
        return render_template('budget.html', 
                             budgets=budgets,
                             current_month=current_month,
                             format_currency=format_currency)
    except Exception as e:
        flash('حدث خطأ أثناء تحميل الميزانية')
        return render_template('budget.html', 
                             budgets=[],
                             current_month=datetime.now().strftime('%Y-%m'),
                             format_currency=format_currency)

@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    if request.method == 'POST':
        try:
            title = request.form['title']
            target_amount = float(request.form['target_amount'])
            current_amount = float(request.form.get('current_amount', 0))
            deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
            description = request.form.get('description', '')
            
            if target_amount <= 0:
                flash('المبلغ المستهدف يجب أن يكون أكبر من صفر')
                return redirect(url_for('goals'))
            
            if current_amount < 0:
                flash('المبلغ الحالي لا يمكن أن يكون سالباً')
                return redirect(url_for('goals'))
            
            goal = Goal(
                user_id=current_user.id,
                title=title,
                target_amount=target_amount,
                current_amount=current_amount,
                deadline=deadline,
                description=description
            )
            
            db.session.add(goal)
            db.session.commit()
            
            flash('تم إضافة الهدف المالي بنجاح')
            return redirect(url_for('goals'))
        except ValueError:
            flash('البيانات المدخلة غير صحيحة')
            return redirect(url_for('goals'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة الهدف')
            return redirect(url_for('goals'))
    
    try:
        # الحصول على جميع الأهداف
        goals = Goal.query.filter_by(user_id=current_user.id)\
            .order_by(Goal.deadline).all()
        
        return render_template('goals.html', 
                             goals=goals,
                             format_currency=format_currency,
                             today=date.today())
    except Exception as e:
        flash('حدث خطأ أثناء تحميل الأهداف')
        return render_template('goals.html', 
                             goals=[],
                             format_currency=format_currency)

@app.route('/update_goal/<int:goal_id>', methods=['POST'])
@login_required
def update_goal(goal_id):
    try:
        goal = Goal.query.get_or_404(goal_id)
        if goal.user_id != current_user.id:
            flash('غير مسموح لك بتعديل هذا الهدف')
            return redirect(url_for('goals'))
        
        current_amount = float(request.form['current_amount'])
        if current_amount < 0:
            flash('المبلغ الحالي لا يمكن أن يكون سالباً')
            return redirect(url_for('goals'))
        
        goal.current_amount = current_amount
        
        db.session.commit()
        flash('تم تحديث الهدف بنجاح')
        return redirect(url_for('goals'))
    except ValueError:
        flash('البيانات المدخلة غير صحيحة')
        return redirect(url_for('goals'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تحديث الهدف')
        return redirect(url_for('goals'))

@app.route('/delete_goal/<int:goal_id>')
@login_required
def delete_goal(goal_id):
    try:
        goal = Goal.query.get_or_404(goal_id)
        if goal.user_id != current_user.id:
            flash('غير مسموح لك بحذف هذا الهدف')
            return redirect(url_for('goals'))
        
        db.session.delete(goal)
        db.session.commit()
        flash('تم حذف الهدف بنجاح')
        return redirect(url_for('goals'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف الهدف')
        return redirect(url_for('goals'))

@app.route('/api/chart_data')
@login_required
def chart_data():
    try:
        # بيانات للرسوم البيانية
        month_start, month_end = get_month_range()
        categories = db.session.query(Transaction.category, db.func.sum(Transaction.amount))\
            .filter(Transaction.user_id == current_user.id, 
                    Transaction.type == 'expense',
                    Transaction.date >= month_start,
                    Transaction.date <= month_end)\
            .group_by(Transaction.category)\
            .order_by(db.func.sum(Transaction.amount).desc()).all()
        
        return jsonify({
            'labels': [cat[0] for cat in categories],
            'data': [float(cat[1]) for cat in categories]
        })
    except Exception as e:
        return jsonify({'labels': [], 'data': []})

@app.route('/api/monthly_data')
@login_required
def monthly_data():
    try:
        # البيانات الشهرية - آخر 6 أشهر
        six_months_ago = datetime.now() - timedelta(days=180)
        
        monthly_data = db.session.query(
            db.func.strftime('%Y-%m', Transaction.date).label('month'),
            db.func.sum(db.case((Transaction.type == 'income', Transaction.amount), else_=0)).label('income'),
            db.func.sum(db.case((Transaction.type == 'expense', Transaction.amount), else_=0)).label('expense')
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= six_months_ago
        ).group_by(
            db.func.strftime('%Y-%m', Transaction.date)
        ).order_by(
            db.func.strftime('%Y-%m', Transaction.date)
        ).all()
        
        # تحويل البيانات إلى تنسيق مناسب
        formatted_data = []
        for data in monthly_data:
            try:
                month_date = datetime.strptime(data.month, '%Y-%m')
                month_name = month_date.strftime('%B %Y')
                arabic_months = {
                    'January': 'يناير', 'February': 'فبراير', 'March': 'مارس',
                    'April': 'أبريل', 'May': 'مايو', 'June': 'يونيو',
                    'July': 'يوليو', 'August': 'أغسطس', 'September': 'سبتمبر',
                    'October': 'أكتوبر', 'November': 'نوفمبر', 'December': 'ديسمبر'
                }
                for eng, ar in arabic_months.items():
                    month_name = month_name.replace(eng, ar)
                formatted_data.append({
                    'month': month_name,
                    'income': float(data.income),
                    'expense': float(data.expense)
                })
            except Exception as e:
                print(f"خطأ في معالجة الشهر {data.month}: {e}")
                continue
        return jsonify(formatted_data)
    except Exception as e:
        print(f"خطأ في API البيانات الشهرية: {e}")
        return jsonify([])

@app.route('/api/budget_data')
@login_required
def budget_data():
    try:
        current_month = datetime.now().strftime('%Y-%m')
        budgets = Budget.query.filter_by(
            user_id=current_user.id,
            month=current_month
        ).all()
        
        month_start, month_end = get_month_range()
        budget_data = []
        
        for budget in budgets:
            spent = db.session.query(db.func.sum(Transaction.amount))\
                .filter(Transaction.user_id == current_user.id,
                       Transaction.type == 'expense',
                       Transaction.category == budget.category,
                       Transaction.date >= month_start,
                       Transaction.date <= month_end).scalar() or 0
            
            budget_data.append({
                'category': budget.category,
                'budget': float(budget.amount),
                'spent': float(spent),
                'remaining': float(budget.amount - spent),
                'percentage': (spent / budget.amount * 100) if budget.amount > 0 else 0
            })
        
        return jsonify(budget_data)
    except Exception as e:
        return jsonify([])

@app.route('/tips')
@login_required
def tips():
    try:
        # الحصول على جميع النصائح للمستخدم
        tips = Tip.query.filter_by(user_id=current_user.id)\
            .order_by(Tip.created_at.desc()).all()
        
        # إحصائيات النصائح
        total_tips = len(tips)
        read_tips = len([tip for tip in tips if tip.is_read])
        applied_tips = len([tip for tip in tips if tip.is_applied])
        
        # تجميع النصائح حسب الفئة
        tips_by_category = {}
        for tip in tips:
            if tip.category not in tips_by_category:
                tips_by_category[tip.category] = []
            tips_by_category[tip.category].append(tip)
        
        return render_template('tips.html', 
                             tips=tips,
                             tips_by_category=tips_by_category,
                             total_tips=total_tips,
                             read_tips=read_tips,
                             applied_tips=applied_tips)
    except Exception as e:
        flash('حدث خطأ أثناء تحميل النصائح')
        return render_template('tips.html', 
                             tips=[],
                             tips_by_category={},
                             total_tips=0,
                             read_tips=0,
                             applied_tips=0)

@app.route('/tips/mark_read/<int:tip_id>')
@login_required
def mark_tip_read(tip_id):
    try:
        tip = Tip.query.get_or_404(tip_id)
        if tip.user_id != current_user.id:
            flash('غير مسموح لك بتعديل هذه النصيحة')
            return redirect(url_for('tips'))
        
        tip.is_read = True
        db.session.commit()
        flash('تم تحديد النصيحة كمقروءة')
        return redirect(url_for('tips'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تحديث النصيحة')
        return redirect(url_for('tips'))

@app.route('/tips/mark_applied/<int:tip_id>')
@login_required
def mark_tip_applied(tip_id):
    try:
        tip = Tip.query.get_or_404(tip_id)
        if tip.user_id != current_user.id:
            flash('غير مسموح لك بتعديل هذه النصيحة')
            return redirect(url_for('tips'))
        
        tip.is_applied = True
        tip.applied_at = datetime.utcnow()
        db.session.commit()
        flash('تم تحديد النصيحة كمطبقة')
        return redirect(url_for('tips'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تحديث النصيحة')
        return redirect(url_for('tips'))

@app.route('/tips/delete/<int:tip_id>')
@login_required
def delete_tip(tip_id):
    try:
        tip = Tip.query.get_or_404(tip_id)
        if tip.user_id != current_user.id:
            flash('غير مسموح لك بحذف هذه النصيحة')
            return redirect(url_for('tips'))
        
        db.session.delete(tip)
        db.session.commit()
        flash('تم حذف النصيحة بنجاح')
        return redirect(url_for('tips'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف النصيحة')
        return redirect(url_for('tips'))

@app.route('/tips/generate', methods=['POST'])
@login_required
def generate_tips():
    try:
        # تحليل بيانات المستخدم لتوليد نصائح مخصصة
        month_start, month_end = get_month_range()
        
        # إحصائيات المصروفات
        monthly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= month_start,
            Transaction.date <= month_end
        ).scalar() or 0
        
        # إحصائيات الدخل
        monthly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'income',
            Transaction.date >= month_start,
            Transaction.date <= month_end
        ).scalar() or 0
        
        # أفضل الفئات إنفاقاً
        top_categories = db.session.query(
            Transaction.category, db.func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= month_start,
            Transaction.date <= month_end
        ).group_by(Transaction.category).order_by(db.func.sum(Transaction.amount).desc()).limit(3).all()
        
        # الميزانيات
        current_month = datetime.now().strftime('%Y-%m')
        budgets = Budget.query.filter_by(
            user_id=current_user.id,
            month=current_month
        ).all()
        
        # الأهداف المالية
        goals = Goal.query.filter_by(user_id=current_user.id).all()
        
        # حساب نسبة الادخار
        savings_rate = 0
        if monthly_income > 0:
            savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100
        
        # تحضير البيانات للذكاء الاصطناعي
        user_data = {
            'monthly_expenses': monthly_expenses,
            'monthly_income': monthly_income,
            'top_categories': [(cat, amount) for cat, amount in top_categories],
            'budgets': [
                {
                    'category': budget.category,
                    'amount': budget.amount,
                    'spent': budget.spent,
                    'percentage': (budget.spent / budget.amount * 100) if budget.amount > 0 else 0
                }
                for budget in budgets
            ],
            'goals': [
                {
                    'title': goal.title,
                    'target_amount': goal.target_amount,
                    'current_amount': goal.current_amount,
                    'deadline': goal.deadline.strftime('%Y-%m-%d'),
                    'percentage': (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
                }
                for goal in goals
            ],
            'savings_rate': round(savings_rate, 1)
        }
        
        # توليد النصائح البسيطة التقليدية
        simple_tips = generate_simple_tips(user_data)
        
        # توليد النصائح الذكية باستخدام المستشار المالي الذكي
        ai_tips = []
        if AI_ADVISOR_AVAILABLE:
            try:
                advisor = AIFinancialAdvisor(db.session)
                ai_tips = advisor.get_smart_tips(current_user.id, months=1)
            except Exception as e:
                print(f"❌ خطأ في المستشار الذكي: {e}")
        
        # دمج النصائح التقليدية والذكية
        all_tips = []
        
        # إضافة النصائح الذكية أولاً (نصيحة واحدة فقط)
        if ai_tips:
            tip_data = ai_tips[0]  # فقط أول نصيحة
            tip = Tip(
                user_id=current_user.id,
                title=tip_data.get('title', 'نصيحة ذكية'),
                content=tip_data.get('content', ''),
                category=tip_data.get('category', 'ai_advice'),
                priority=tip_data.get('priority', 'high')
            )
            all_tips.append(tip)
        
        # إضافة النصائح التقليدية
        for tip_data in simple_tips:
            tip = Tip(
                user_id=current_user.id,
                title=tip_data.get('title', 'نصيحة مالية'),
                content=tip_data.get('content', ''),
                category=tip_data.get('category', 'general'),
                priority=tip_data.get('priority', 'medium')
            )
            all_tips.append(tip)
        
        # إضافة النصائح إلى قاعدة البيانات
        for tip in all_tips:
            db.session.add(tip)
        
        db.session.commit()
        
        total_tips = len(all_tips)
        ai_tips_count = len(ai_tips)
        traditional_tips_count = len(simple_tips)
        
        if ai_tips_count > 0:
            flash(f'تم توليد {total_tips} نصيحة جديدة (نصيحة ذكية واحدة + {traditional_tips_count} تقليدية) بناءً على بياناتك المالية')
        else:
            flash(f'تم توليد {total_tips} نصيحة تقليدية جديدة بناءً على بياناتك المالية')
        return redirect(url_for('tips'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء توليد النصائح: {str(e)}')
        return redirect(url_for('tips'))

@app.route('/tips/ai_advice')
@login_required
def get_ai_advice_route():
    """الحصول على نصيحة ذكية فورية"""
    try:
        if not AI_ADVISOR_AVAILABLE:
            flash('المستشار المالي الذكي غير متاح حالياً')
            return redirect(url_for('tips'))
        
        # الحصول على نصيحة ذكية
        advisor = AIFinancialAdvisor(db.session)
        advice = advisor.predict_advice(current_user.id, months=1)
        
        # الحصول على تحليل مفصل
        analysis = advisor.get_detailed_analysis(current_user.id, months=1)
        
        if not analysis:
            flash('لا توجد بيانات كافية لتقديم نصيحة ذكية')
            return redirect(url_for('tips'))
        
        # إنشاء نصيحة جديدة في قاعدة البيانات
        tip = Tip(
            user_id=current_user.id,
            title='نصيحة ذكية فورية',
            content=f"{advice}\n\nتحليل سريع:\n- إجمالي المصروفات: {format_currency(analysis['total_expenses'])}\n- إجمالي الدخل: {format_currency(analysis['total_income'])}\n- صافي الدخل: {format_currency(analysis['net_income'])}\n- نسبة الادخار: {analysis['savings_rate']:.1f}%",
            category='ai_advice',
            priority='high'
        )
        
        db.session.add(tip)
        db.session.commit()
        
        flash(f'تم إنشاء نصيحة ذكية جديدة: {advice}')
        return redirect(url_for('tips'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الحصول على النصيحة الذكية: {str(e)}')
        return redirect(url_for('tips'))

@app.route('/tips/ai_analysis')
@login_required
def get_ai_analysis_route():
    """الحصول على تحليل ذكي مفصل"""
    try:
        if not AI_ADVISOR_AVAILABLE:
            flash('المستشار المالي الذكي غير متاح حالياً')
            return redirect(url_for('tips'))
        
        # الحصول على تحليل مفصل
        advisor = AIFinancialAdvisor(db.session)
        analysis = advisor.get_detailed_analysis(current_user.id, months=1)
        
        if not analysis:
            flash('لا توجد بيانات كافية لإجراء تحليل ذكي')
            return redirect(url_for('tips'))
        
        # إنشاء نصيحة تحليلية في قاعدة البيانات
        analysis_content = f"""
تحليل ذكي مفصل:

📊 الإحصائيات العامة:
• إجمالي المصروفات: {format_currency(analysis['total_expenses'])}
• إجمالي الدخل: {format_currency(analysis['total_income'])}
• صافي الدخل: {format_currency(analysis['net_income'])}
• نسبة الادخار: {analysis['savings_rate']:.1f}%

🏷️ المصروفات حسب الفئة:
"""
        
        for category, amount in analysis['expenses_by_category'].items():
            percentage = (amount / analysis['total_expenses'] * 100) if analysis['total_expenses'] > 0 else 0
            analysis_content += f"• {category}: {format_currency(amount)} ({percentage:.1f}%)\n"
        
        if analysis['income_by_category']:
            analysis_content += "\n💰 الدخل حسب الفئة:\n"
            for category, amount in analysis['income_by_category'].items():
                percentage = (amount / analysis['total_income'] * 100) if analysis['total_income'] > 0 else 0
                analysis_content += f"• {category}: {format_currency(amount)} ({percentage:.1f}%)\n"
        
        analysis_content += f"\n💡 النصيحة الذكية: {analysis['advice']}"
        
        tip = Tip(
            user_id=current_user.id,
            title='تحليل ذكي مفصل',
            content=analysis_content,
            category='ai_analysis',
            priority='high'
        )
        
        db.session.add(tip)
        db.session.commit()
        
        flash('تم إنشاء تحليل ذكي مفصل جديد')
        return redirect(url_for('tips'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إجراء التحليل الذكي: {str(e)}')
        return redirect(url_for('tips'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 