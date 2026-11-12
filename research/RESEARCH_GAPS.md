# فجوات البحث — YemenVision MTMC

## 1. فجوات بيانات/تمثيل
- لا توجد في هذه الحزمة بيانات يمنية معلّمة أو split مستقل موثق.
- اختلاف أنواع المركبات، سيارات الأجرة، الحافلات الصغيرة، الشاحنات والحمولات.
- اختلاف اللوحات من حيث الشكل/اللون/الخط، مع شرط عدم جعل LPR معرفًا دائمًا.
- نقص تمثيل الغبار، الحرارة، الضباب، الإضاءة الليلية، الانعكاس، والضغط/التشويه في الكاميرات المحلية.
- زوايا، ارتفاعات، FOV، وانسداد مختلفة عن CityFlow/VeRi/UA-DETRAC.

## 2. فجوات منهجية
- domain shift بين datasets العامة وبيئة اليمن يحتاج protocol target مستقل.
- cross-camera appearance قد ينهار مع تغيّر الإضاءة/الزاوية/الحمولة/الطلاء.
- topology اليمنية والـ travel-time priors غير متوفرة.
- ground truth MTMC مكلف ويحتاج annotation uncertainty وquality review.
- المقاييس العامة لا تقيس جيدًا abstention، calibration، privacy-safe analytics، أو operational cost.

## 3. أسئلة قابلة للبحث دون ادعاء ابتكار
1. كم يضيف camera topology فوق appearance + temporal على بيانات يمنية held-out؟
2. هل multi-task attributes تحسن cross-camera matching دون رفع false matches؟
3. ما أثر redaction على detector/ReID accuracy، وكيف نعوضه؟
4. ما أفضل policy للـ abstention عند عدم كفاية الدليل؟
5. هل domain adaptation يحسن target دون source regression؟
6. كيف نحدد travel-time priors مع تغير congestion والطرق؟
7. ما trade-off بين accuracy، latency، VRAM، privacy retention، وcoverage؟

## 4. فجوات ترخيص وحوكمة
- شروط datasets العامة قد تكون research-only أو مكونات الفيديو لها حقوق مختلفة.
- commercial clearance لكل model/weights/dataset لم يُحسم.
- يجب اعتماد data card/model card وprovenance وaccess audit قبل production.
- لا يجوز استخدام embedding أو match كهوية قانونية أو سجل حركة دائم.

## 5. خطة سد الفجوات
- pilot مصرح متعدد الكاميرات والفترات.
- annotation guideline مع unknown/occluded/uncertain labels.
- time/camera/identity-disjoint splits.
- error taxonomy حسب إضاءة/زاوية/نوع مركبة/ازدحام.
- ablation موثق وconfidence intervals.
- مراجعة أمنية وخصوصية قبل توسيع الاحتفاظ أو الصلاحيات.

**ملاحظة:** لا تُسمى أي نتيجة "ابتكارًا علميًا" قبل literature search موسع، baseline reproduction، ونتيجة مستقلة قابلة لإعادة الإنتاج.
