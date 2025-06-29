import joblib
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func

class AIFinancialAdvisor:
    """مستشار مالي ذكي يستخدم نموذج التعلم الآلي"""
    
    def __init__(self, db_session=None):
        """تهيئة المستشار المالي"""
        try:
            self.model = joblib.load("models/advice_model.pkl")
            self.label_encoder = joblib.load("models/label_encoder.pkl")
            self.categories = joblib.load("models/categories.pkl")
            self.db_session = db_session
            self.is_loaded = True
        except FileNotFoundError:
            print("⚠️ تحذير: لم يتم العثور على ملفات النموذج. تأكد من تشغيل train_model.py")
            self.is_loaded = False
    
    def get_user_expenses_data(self, user_id, months=1):
        """الحصول على بيانات مصروفات المستخدم"""
        if not self.db_session:
            return {}
            
        try:
            # حساب تاريخ البداية
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # استيراد النماذج من app.py
            from app import Transaction
            
            # الحصول على المصروفات مجمعة حسب الفئة
            expenses = self.db_session.query(
                Transaction.category,
                func.sum(Transaction.amount).label('total')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'expense',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.category).all()
            
            # تحويل البيانات إلى قاموس
            expenses_dict = {}
            for category, total in expenses:
                expenses_dict[category] = float(total)
            
            return expenses_dict
            
        except Exception as e:
            print(f"❌ خطأ في الحصول على بيانات المصروفات: {e}")
            return {}
    
    def get_user_income_data(self, user_id, months=1):
        """الحصول على بيانات دخل المستخدم"""
        if not self.db_session:
            return {}
            
        try:
            # حساب تاريخ البداية
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # استيراد النماذج من app.py
            from app import Transaction
            
            # الحصول على الدخل مجمع حسب الفئة
            income = self.db_session.query(
                Transaction.category,
                func.sum(Transaction.amount).label('total')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'income',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.category).all()
            
            # تحويل البيانات إلى قاموس
            income_dict = {}
            for category, total in income:
                income_dict[category] = float(total)
            
            return income_dict
            
        except Exception as e:
            print(f"❌ خطأ في الحصول على بيانات الدخل: {e}")
            return {}
    
    def predict_advice(self, user_id, months=1):
        """توقع النصيحة للمستخدم"""
        if not self.is_loaded:
            return "النموذج غير متاح حالياً"
        
        try:
            # الحصول على بيانات المستخدم
            expenses_data = self.get_user_expenses_data(user_id, months)
            income_data = self.get_user_income_data(user_id, months)
            
            # دمج البيانات
            all_data = {**expenses_data, **income_data}
            
            if not all_data:
                return "لا توجد بيانات كافية لتقديم نصيحة"
            
            # تحويل البيانات إلى مصفوفة رقمية
            features = [0] * len(self.categories)
            
            for category, amount in all_data.items():
                if category in self.categories:
                    idx = self.categories.index(category)
                    features[idx] = amount
            
            # توقع النصيحة
            prediction = self.model.predict([features])[0]
            advice = self.label_encoder.inverse_transform([prediction])[0]
            
            return advice
            
        except Exception as e:
            print(f"❌ خطأ في توقع النصيحة: {e}")
            return "حدث خطأ في تحليل البيانات"
    
    def get_detailed_analysis(self, user_id, months=1):
        """تحليل مفصل للمصروفات والدخل"""
        try:
            expenses_data = self.get_user_expenses_data(user_id, months)
            income_data = self.get_user_income_data(user_id, months)
            
            total_expenses = sum(expenses_data.values())
            total_income = sum(income_data.values())
            
            analysis = {
                'total_expenses': total_expenses,
                'total_income': total_income,
                'net_income': total_income - total_expenses,
                'savings_rate': ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0,
                'expenses_by_category': expenses_data,
                'income_by_category': income_data,
                'advice': self.predict_advice(user_id, months)
            }
            
            # إضافة تحليل إضافي
            if expenses_data:
                max_expense_category = max(expenses_data.items(), key=lambda x: x[1])
                analysis['highest_expense_category'] = max_expense_category
                analysis['highest_expense_percentage'] = (max_expense_category[1] / total_expenses * 100) if total_expenses > 0 else 0
            
            return analysis
            
        except Exception as e:
            print(f"❌ خطأ في التحليل المفصل: {e}")
            return None
    
    def get_smart_tips(self, user_id, months=1):
        """الحصول على نصيحة ذكية واحدة مخصصة"""
        try:
            analysis = self.get_detailed_analysis(user_id, months)
            
            if not analysis:
                return []
            
            # إنشاء قائمة بجميع النصائح المحتملة مع أولوياتها
            possible_tips = []
            
            # نصيحة عامة من النموذج (أولوية عالية)
            if analysis['advice']:
                possible_tips.append({
                    'title': 'نصيحة ذكية',
                    'content': analysis['advice'],
                    'category': 'ai_advice',
                    'priority': 'high',
                    'score': 100  # أعلى أولوية
                })
            
            # نصائح إضافية بناءً على التحليل
            if analysis['savings_rate'] < 20:
                possible_tips.append({
                    'title': 'نسبة الادخار منخفضة',
                    'content': f'نسبة ادخارك {analysis["savings_rate"]:.1f}% منخفضة. حاول الوصول إلى 20% على الأقل.',
                    'category': 'saving',
                    'priority': 'high',
                    'score': 90
                })
            
            if analysis['total_expenses'] > analysis['total_income'] * 0.9:
                possible_tips.append({
                    'title': 'مصروفات مرتفعة',
                    'content': 'مصروفاتك تمثل نسبة كبيرة من دخلك. فكر في تقليل المصروفات غير الضرورية.',
                    'category': 'spending',
                    'priority': 'medium',
                    'score': 80
                })
            
            if 'highest_expense_category' in analysis:
                category, amount = analysis['highest_expense_category']
                percentage = analysis['highest_expense_percentage']
                
                if percentage > 40:
                    possible_tips.append({
                        'title': f'إنفاق مرتفع في {category}',
                        'content': f'أنت تنفق {percentage:.1f}% من مصروفاتك في {category}. فكر في تقليل هذا المصروف.',
                        'category': 'spending',
                        'priority': 'medium',
                        'score': 70
                    })
            
            # إرجاع النصيحة ذات الأولوية الأعلى فقط
            if possible_tips:
                # ترتيب النصائح حسب الأولوية (الأعلى أولاً)
                possible_tips.sort(key=lambda x: x['score'], reverse=True)
                return [possible_tips[0]]  # إرجاع نصيحة واحدة فقط
            
            return []
            
        except Exception as e:
            print(f"❌ خطأ في الحصول على النصائح: {e}")
            return []
    
    def predict_from_data(self, expenses_data):
        """توقع النصيحة من بيانات معطاة"""
        if not self.is_loaded:
            return "النموذج غير متاح حالياً"
        
        try:
            # تحويل البيانات إلى مصفوفة رقمية
            features = [0] * len(self.categories)
            
            for category, amount in expenses_data.items():
                if category in self.categories:
                    idx = self.categories.index(category)
                    features[idx] = amount
            
            # توقع النصيحة
            prediction = self.model.predict([features])[0]
            advice = self.label_encoder.inverse_transform([prediction])[0]
            
            return advice
            
        except Exception as e:
            print(f"❌ خطأ في توقع النصيحة: {e}")
            return "حدث خطأ في تحليل البيانات"

# دالة مساعدة لاستخدام المستشار
def get_ai_advice(user_id, db_session=None, months=1):
    """دالة مساعدة للحصول على نصيحة ذكية"""
    advisor = AIFinancialAdvisor(db_session)
    return advisor.predict_advice(user_id, months)

def get_ai_analysis(user_id, db_session=None, months=1):
    """دالة مساعدة للحصول على تحليل مفصل"""
    advisor = AIFinancialAdvisor(db_session)
    return advisor.get_detailed_analysis(user_id, months)

def get_ai_tips(user_id, db_session=None, months=1):
    """دالة مساعدة للحصول على نصائح ذكية"""
    advisor = AIFinancialAdvisor(db_session)
    return advisor.get_smart_tips(user_id, months)

def predict_advice_from_data(expenses_data):
    """دالة مساعدة لتوقع النصيحة من بيانات معطاة"""
    advisor = AIFinancialAdvisor()
    return advisor.predict_from_data(expenses_data)

# مثال على الاستخدام
if __name__ == "__main__":
    print("🤖 اختبار المستشار المالي الذكي")
    print("=" * 50)
    
    advisor = AIFinancialAdvisor()
    
    if advisor.is_loaded:
        print("✅ تم تحميل النموذج بنجاح")
        print(f"📊 عدد الفئات المدعومة: {len(advisor.categories)}")
        
        # اختبار مع بيانات وهمية
        test_cases = [
            {
                "name": "مصروفات عالية في التسوق",
                "data": {"الطعام والشراب": 300, "المواصلات": 150, "التسوق": 800, "الترفيه": 200}
            },
            {
                "name": "مصروفات الطعام مرتفعة",
                "data": {"الطعام والشراب": 900, "المواصلات": 200, "التسوق": 150, "الفواتير": 300}
            },
            {
                "name": "إنفاق متوازن",
                "data": {"الطعام والشراب": 200, "المواصلات": 150, "التسوق": 100, "الترفيه": 80}
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 اختبار {i}: {test_case['name']}")
            print(f"   البيانات: {test_case['data']}")
            
            advice = advisor.predict_from_data(test_case['data'])
            print(f"   💡 النصيحة: {advice}")
        
    else:
        print("❌ فشل في تحميل النموذج")
        print("تأكد من تشغيل train_model.py أولاً") 