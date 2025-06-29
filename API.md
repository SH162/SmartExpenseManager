# توثيق API - مدير المصروفات الذكي

هذا التوثيق يوضح نقاط النهاية (endpoints) المتاحة في تطبيق مدير المصروفات الذكي.

## نظرة عامة

- **Base URL**: `http://localhost:5000`
- **التنسيق**: JSON
- **المصادقة**: مطلوبة لجميع النقاط النهائية (باستثناء تسجيل الدخول والتسجيل)

## المصادقة

جميع الطلبات تتطلب تسجيل الدخول. يتم استخدام Flask-Login لإدارة الجلسات.

### تسجيل الدخول
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

### تسجيل الخروج
```http
GET /logout
```

## نقاط النهاية

### 1. الصفحة الرئيسية

#### GET /
```http
GET /
```

**الاستجابة:**
- إذا كان المستخدم مسجل دخول: إعادة توجيه إلى `/dashboard`
- إذا لم يكن مسجل دخول: عرض صفحة الترحيب

### 2. لوحة التحكم

#### GET /dashboard
```http
GET /dashboard
```

**الاستجابة:**
```html
<!-- صفحة HTML تحتوي على لوحة التحكم -->
```

### 3. إدارة المعاملات

#### GET /transactions
```http
GET /transactions
```

**المعاملات:**
- `page`: رقم الصفحة (اختياري، افتراضي: 1)
- `per_page`: عدد العناصر في الصفحة (اختياري، افتراضي: 20)
- `category`: تصفية حسب الفئة (اختياري)
- `type`: تصفية حسب النوع (income/expense) (اختياري)
- `date_from`: تاريخ البداية (اختياري)
- `date_to`: تاريخ النهاية (اختياري)

**الاستجابة:**
```html
<!-- صفحة HTML تحتوي على قائمة المعاملات -->
```

#### GET /add_transaction
```http
GET /add_transaction
```

**الاستجابة:**
```html
<!-- نموذج إضافة معاملة جديدة -->
```

#### POST /add_transaction
```http
POST /add_transaction
Content-Type: application/x-www-form-urlencoded

amount=100.50&type=expense&category=الطعام والشراب&description=وجبة غداء&date=2024-01-15
```

**الحقول المطلوبة:**
- `amount`: المبلغ (رقم)
- `type`: النوع (income/expense)
- `category`: الفئة (نص)
- `description`: الوصف (اختياري)
- `date`: التاريخ (YYYY-MM-DD)

**الاستجابة:**
- نجاح: إعادة توجيه إلى `/transactions`
- فشل: عرض رسالة خطأ

#### GET /transaction/edit/{id}
```http
GET /transaction/edit/123
```

**الاستجابة:**
```html
<!-- نموذج تعديل المعاملة -->
```

#### POST /transaction/edit/{id}
```http
POST /transaction/edit/123
Content-Type: application/x-www-form-urlencoded

amount=150.00&type=expense&category=الطعام والشراب&description=وجبة عشاء&date=2024-01-15
```

#### GET /transaction/delete/{id}
```http
GET /transaction/delete/123
```

**الاستجابة:**
- نجاح: إعادة توجيه إلى `/transactions`
- فشل: عرض رسالة خطأ

### 4. التقارير والتحليلات

#### GET /reports
```http
GET /reports
```

**الاستجابة:**
```html
<!-- صفحة التقارير -->
```

#### GET /api/chart_data
```http
GET /api/chart_data
```

**المعاملات:**
- `months`: عدد الأشهر (اختياري، افتراضي: 6)

**الاستجابة:**
```json
{
  "expenses": [
    {"category": "الطعام والشراب", "amount": 500},
    {"category": "المواصلات", "amount": 200}
  ],
  "income": [
    {"category": "الراتب", "amount": 2000}
  ]
}
```

#### GET /api/monthly_data
```http
GET /api/monthly_data
```

**المعاملات:**
- `months`: عدد الأشهر (اختياري، افتراضي: 12)

**الاستجابة:**
```json
{
  "labels": ["يناير", "فبراير", "مارس"],
  "expenses": [800, 750, 900],
  "income": [2000, 2000, 2200],
  "savings": [1200, 1250, 1300]
}
```

#### GET /api/budget_data
```http
GET /api/budget_data
```

**الاستجابة:**
```json
{
  "budgets": [
    {
      "category": "الطعام والشراب",
      "budget": 500,
      "spent": 450,
      "remaining": 50
    }
  ]
}
```

### 5. إدارة الميزانيات

#### GET /budget
```http
GET /budget
```

**الاستجابة:**
```html
<!-- صفحة إدارة الميزانيات -->
```

#### POST /budget
```http
POST /budget
Content-Type: application/x-www-form-urlencoded

category=الطعام والشراب&amount=500&month=2024-01
```

**الحقول المطلوبة:**
- `category`: الفئة (نص)
- `amount`: الميزانية (رقم)
- `month`: الشهر (YYYY-MM)

### 6. الأهداف المالية

#### GET /goals
```http
GET /goals
```

**الاستجابة:**
```html
<!-- صفحة الأهداف المالية -->
```

#### POST /goals
```http
POST /goals
Content-Type: application/x-www-form-urlencoded

title=شراء سيارة&target_amount=50000&deadline=2024-12-31&description=شراء سيارة جديدة
```

**الحقول المطلوبة:**
- `title`: العنوان (نص)
- `target_amount`: المبلغ المستهدف (رقم)
- `deadline`: الموعد النهائي (YYYY-MM-DD)
- `description`: الوصف (اختياري)

#### POST /update_goal/{id}
```http
POST /update_goal/123
Content-Type: application/x-www-form-urlencoded

current_amount=10000
```

#### GET /delete_goal/{id}
```http
GET /delete_goal/123
```

### 7. النصائح المالية

#### GET /tips
```http
GET /tips
```

**الاستجابة:**
```html
<!-- صفحة النصائح -->
```

#### POST /tips/generate
```http
POST /tips/generate
```

**الاستجابة:**
```html
<!-- إعادة تحميل الصفحة مع نصائح جديدة -->
```

#### GET /tips/mark_read/{id}
```http
GET /tips/mark_read/123
```

#### GET /tips/mark_applied/{id}
```http
GET /tips/mark_applied/123
```

#### GET /tips/delete/{id}
```http
GET /tips/delete/123
```

#### GET /tips/ai_advice
```http
GET /tips/ai_advice
```

**الاستجابة:**
```json
{
  "advice": "نصيحة من المستشار المالي الذكي",
  "analysis": {
    "total_expenses": 1500,
    "total_income": 2000,
    "savings_rate": 25.0
  }
}
```

#### GET /tips/ai_analysis
```http
GET /tips/ai_analysis
```

**الاستجابة:**
```json
{
  "analysis": {
    "total_expenses": 1500,
    "total_income": 2000,
    "net_income": 500,
    "savings_rate": 25.0,
    "expenses_by_category": {
      "الطعام والشراب": 500,
      "المواصلات": 300
    },
    "advice": "نصيحة مخصصة"
  }
}
```

## رموز الحالة

- `200 OK`: الطلب ناجح
- `302 Found`: إعادة توجيه
- `400 Bad Request`: طلب غير صحيح
- `401 Unauthorized`: غير مصرح
- `404 Not Found`: الصفحة غير موجودة
- `500 Internal Server Error`: خطأ في الخادم

## رسائل الخطأ

### أخطاء المصادقة
```json
{
  "error": "يجب تسجيل الدخول للوصول لهذه الصفحة"
}
```

### أخطاء التحقق
```json
{
  "error": "جميع الحقول مطلوبة"
}
```

### أخطاء قاعدة البيانات
```json
{
  "error": "حدث خطأ في قاعدة البيانات"
}
```

## أمثلة الاستخدام

### إضافة معاملة جديدة
```bash
curl -X POST http://localhost:5000/add_transaction \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "amount=100&type=expense&category=الطعام والشراب&description=وجبة غداء&date=2024-01-15"
```

### الحصول على بيانات الرسم البياني
```bash
curl -X GET "http://localhost:5000/api/chart_data?months=6"
```

### إنشاء هدف مالي
```bash
curl -X POST http://localhost:5000/goals \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "title=شراء سيارة&target_amount=50000&deadline=2024-12-31&description=شراء سيارة جديدة"
```

## ملاحظات مهمة

1. **المصادقة**: جميع النقاط النهائية تتطلب تسجيل الدخول
2. **التشفير**: كلمات المرور مشفرة باستخدام Werkzeug
3. **التحقق**: يتم التحقق من صحة البيانات المدخلة
4. **الأمان**: يتم حماية البيانات من SQL Injection وXSS
5. **الأداء**: يتم تحسين الاستعلامات لقاعدة البيانات

## الدعم

للحصول على المساعدة أو الإبلاغ عن مشاكل في API:

1. افتح issue في GitHub
2. راجع الوثائق
3. تحقق من سجلات الخادم 