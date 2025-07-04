from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# --------------------------
# 1. بيانات التدريب الموسعة مع جميع التصنيفات
# --------------------------
training_data = [
    # البيانات الأصلية المحسنة
    ({"الطعام والشراب": 500, "المواصلات": 100, "التسوق": 900}, "قلل من التسوق"),
    ({"الطعام والشراب": 300, "المواصلات": 400, "التسوق": 200}, "مصروف النقل مرتفع"),
    ({"الطعام والشراب": 700, "المواصلات": 200, "التسوق": 100}, "الطعام مرتفع"),
    ({"الطعام والشراب": 200, "المواصلات": 100, "التسوق": 150}, "مصروف جيد"),
    ({"الطعام والشراب": 400, "المواصلات": 600, "التسوق": 300}, "التنقل مرتفع"),
    ({"الطعام والشراب": 1000, "المواصلات": 100, "التسوق": 100}, "الطعام يستهلك الميزانية"),
    ({"الطعام والشراب": 200, "المواصلات": 800, "التسوق": 100}, "المواصلات مرتفعة"),
    ({"الطعام والشراب": 300, "المواصلات": 300, "التسوق": 300}, "الإنفاق متوازن"),
    ({"الطعام والشراب": 600, "المواصلات": 100, "التسوق": 600}, "توازن بين الطعام والتسوق مطلوب"),
    ({"الطعام والشراب": 100, "المواصلات": 100, "التسوق": 900}, "التسوق يستنزف الميزانية"),

    # بيانات جديدة مع فئات إضافية
    ({"الطعام والشراب": 400, "الفواتير": 500, "الإيجار": 800}, "الفواتير والإيجار مرتفعة"),
    ({"الطعام والشراب": 300, "الترفيه": 600, "التسوق": 400}, "الترفيه مرتفع"),
    ({"الطعام والشراب": 200, "الصحة": 800, "التعليم": 300}, "مصروفات الصحة مرتفعة"),
    ({"الطعام والشراب": 500, "السفر": 1200, "الهدايا": 200}, "مصروفات السفر مرتفعة"),
    ({"الطعام والشراب": 400, "الصيانة": 700, "أخرى": 300}, "مصروفات الصيانة مرتفعة"),
    
    # بيانات مع فئات الدخل
    ({"الراتب": 2000, "العمل الحر": 500, "الاستثمارات": 300}, "دخل متنوع وجيد"),
    ({"الراتب": 1500, "العمل الحر": 200, "الهدايا": 100}, "فكر في زيادة مصادر الدخل"),
    ({"الراتب": 3000, "الاستثمارات": 800, "العمل الحر": 400}, "دخل ممتاز ومتنوع"),
    
    # بيانات مختلطة (دخل ومصروفات)
    ({"الراتب": 2500, "الطعام والشراب": 600, "المواصلات": 300, "التسوق": 400}, "راقب مصروف التسوق"),
    ({"الراتب": 1800, "الطعام والشراب": 400, "الفواتير": 300, "الإيجار": 600}, "الإيجار مرتفع نسبياً"),
    ({"العمل الحر": 1000, "الطعام والشراب": 300, "الترفيه": 500, "التعليم": 200}, "الترفيه مرتفع"),
    
    # بيانات إضافية للفئات الجديدة
    ({"الطعام والشراب": 350, "الفواتير": 400, "الإيجار": 700, "المواصلات": 250}, "مصروفات أساسية متوازنة"),
    ({"الطعام والشراب": 450, "التسوق": 800, "الترفيه": 600, "الهدايا": 300}, "الترفيه والتسوق مرتفعة"),
    ({"الطعام والشراب": 280, "الصحة": 600, "التعليم": 400, "الصيانة": 200}, "مصروفات الصحة والتعليم مرتفعة"),
    ({"الطعام والشراب": 320, "السفر": 1500, "الهدايا": 400, "أخرى": 150}, "مصروفات السفر مرتفعة جداً"),
    
    # بيانات مع نسب مختلفة
    ({"الطعام والشراب": 150, "المواصلات": 80, "التسوق": 120, "الترفيه": 100}, "إنفاق متوازن ومقبول"),
    ({"الطعام والشراب": 800, "المواصلات": 400, "التسوق": 300, "الفواتير": 200}, "الطعام والمواصلات مرتفعة"),
    ({"الطعام والشراب": 250, "الفواتير": 350, "الإيجار": 800, "الصحة": 300}, "الإيجار مرتفع"),
    ({"الطعام والشراب": 400, "التعليم": 600, "السفر": 800, "الهدايا": 200}, "التعليم والسفر مرتفعة"),
    
    # بيانات مع فئات أخرى
    ({"الطعام والشراب": 300, "الصيانة": 500, "أخرى": 400, "الهدايا": 150}, "مصروفات الصيانة مرتفعة"),
    ({"الطعام والشراب": 350, "الترفيه": 700, "التسوق": 450, "السفر": 300}, "الترفيه مرتفع"),
    ({"الطعام والشراب": 200, "التعليم": 800, "الصحة": 400, "الفواتير": 250}, "التعليم مرتفع"),
    
    # بيانات إضافية للتحسين
    ({"الطعام والشراب": 180, "المواصلات": 120, "التسوق": 80, "الترفيه": 60}, "إنفاق ممتاز ومتوازن"),
    ({"الطعام والشراب": 900, "المواصلات": 300, "التسوق": 200, "الفواتير": 150}, "الطعام مرتفع جداً"),
    ({"الطعام والشراب": 220, "الفواتير": 280, "الإيجار": 750, "الصحة": 180}, "الإيجار مرتفع"),
    ({"الطعام والشراب": 380, "التعليم": 650, "السفر": 900, "الهدايا": 120}, "التعليم والسفر مرتفعة"),
    ({"الطعام والشراب": 280, "الصيانة": 450, "أخرى": 320, "الترفيه": 200}, "مصروفات الصيانة مرتفعة"),
    
    # بيانات مع دخل متنوع
    ({"الراتب": 2200, "العمل الحر": 600, "الاستثمارات": 400, "الطعام والشراب": 400}, "دخل جيد ومتنوع"),
    ({"الراتب": 1600, "العمل الحر": 300, "الهدايا": 150, "الطعام والشراب": 350}, "فكر في زيادة الدخل"),
    ({"الراتب": 2800, "الاستثمارات": 600, "العمل الحر": 500, "المواصلات": 250}, "دخل ممتاز"),
    
    # بيانات مختلطة إضافية
    ({"الراتب": 2400, "الطعام والشراب": 450, "المواصلات": 280, "التسوق": 350, "الترفيه": 200}, "راقب مصروف التسوق"),
    ({"الراتب": 1700, "الطعام والشراب": 320, "الفواتير": 280, "الإيجار": 650, "الصحة": 180}, "الإيجار مرتفع نسبياً"),
    ({"العمل الحر": 1200, "الطعام والشراب": 280, "الترفيه": 450, "التعليم": 180, "السفر": 300}, "الترفيه مرتفع"),
    
    # بيانات نهائية للتحسين
    ({"الطعام والشراب": 160, "المواصلات": 100, "التسوق": 70, "الترفيه": 50, "الفواتير": 200}, "إنفاق ممتاز ومتوازن"),
    ({"الطعام والشراب": 950, "المواصلات": 250, "التسوق": 180, "الفواتير": 120, "الإيجار": 600}, "الطعام مرتفع جداً"),
    ({"الطعام والشراب": 200, "الفواتير": 250, "الإيجار": 700, "الصحة": 150, "التعليم": 300}, "الإيجار مرتفع"),
    ({"الطعام والشراب": 350, "التعليم": 600, "السفر": 850, "الهدايا": 100, "الصيانة": 200}, "التعليم والسفر مرتفعة"),
    ({"الطعام والشراب": 250, "الصيانة": 400, "أخرى": 280, "الترفيه": 180, "التسوق": 120}, "مصروفات الصيانة مرتفعة"),
]

# --------------------------
# 2. تجهيز البيانات للنموذج
# --------------------------
# تحديد جميع الفئات المحتملة
all_categories = [
    "الطعام والشراب", "المواصلات", "التسوق", "الفواتير", "الإيجار", 
    "الترفيه", "الصحة", "التعليم", "السفر", "الهدايا", "الصيانة", "أخرى",
    "الراتب", "العمل الحر", "الاستثمارات"
]

# تحويل البيانات إلى مصفوفات رقمية
X = []
for entry in training_data:
    # إنشاء قائمة بأصفار لجميع الفئات
    features = [0] * len(all_categories)
    
    # ملء القيم الموجودة
    for category, amount in entry[0].items():
        if category in all_categories:
            idx = all_categories.index(category)
            features[idx] = amount
    
    X.append(features)

y = [entry[1] for entry in training_data]

# --------------------------
# 3. تدريب النموذج
# --------------------------
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

model = DecisionTreeClassifier(random_state=42, max_depth=10)
model.fit(X, y_encoded)

# --------------------------
# 4. حفظ النموذج والمحول
# --------------------------
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/advice_model.pkl")
joblib.dump(label_encoder, "models/label_encoder.pkl")
joblib.dump(all_categories, "models/categories.pkl")

print("✅ تم إنشاء النموذج بنجاح وتم حفظه في مجلد models/")
print(f"📊 عدد بيانات التدريب: {len(training_data)}")
print(f"🏷️ عدد الفئات المدعومة: {len(all_categories)}")
print(f"💡 عدد النصائح المختلفة: {len(set(y))}")
print("\n📋 الفئات المدعومة:")
for i, category in enumerate(all_categories, 1):
    print(f"   {i}. {category}")
