# كتالوج البيانات — YemenVision MTMC

**قاعدة حاكمة:** البيانات العامة لا تكفي وحدها لتغطية اليمن. لا تُنزّل أو تُستخدم تجاريًا قبل قراءة شروط الإصدار الحالية وتوثيق الموافقة/الترخيص في سجل provenance.

## 1. تصنيف الاستخدام

| الفئة | datasets | ما تدعمه | ما لا تثبته |
|---|---|---|---|
| Detection / single-camera tracking | UA-DETRAC، أجزاء AI City | vehicle boxes، trajectories، traffic conditions | cross-camera identity في اليمن |
| Vehicle ReID | VeRi-776، VehicleID، VehicleNet | image retrieval/identity split | legal identity أو أداء محلي |
| MTMC | CityFlow، CityFlowV2، AI City MTMC tracks | synchronized cameras، cross-camera IDs | topology اليمنية |
| Local target domain | YemenVision-collected data | target validation/adaptation | لا يوجد بعد في workspace |

## 2. Catalog

### 2.1 CityFlow
- **المصدر:** Tang et al., CVPR 2019؛ DOI: `10.1109/CVPR.2019.00440`؛ صفحة challenge الرسمية: `https://www.aicitychallenge.org/`؛ مستودع مرتبط: `https://github.com/JL-DA/CityFlow`.
- **الغرض:** MTMC vehicle tracking وvehicle ReID.
- **إحصاءات منشورة/متداولة:** حوالي 40 كاميرا عبر 10 تقاطعات، فيديو متزامن HD لأكثر من 3 ساعات، annotations للمركبات والهويات. لأن بعض الأرقام تختلف باختلاف نسخة التوزيع/المسابقة، يجب تثبيت release manifest قبل استخدامها.
- **الكاميرات:** متعددة، موزعة على تقاطعات؛ spatial/temporal structure متاح ضمن benchmark.
- **الفئات:** مركبات الطريق؛ taxonomy الدقيقة يجب قراءتها من annotation release.
- **الظروف:** مشاهد حضرية أمريكية، زوايا متعددة، occlusion وتداخل.
- **الدقة/الفيديو:** HD وframe rate متعدد حسب release؛ لا نفترض رقمًا واحدًا لكل الملفات.
- **annotation format:** فيديو/frames مع bounding boxes وcamera/track identity وفق challenge format؛ تحقق من schema عند التنزيل.
- **التحديات:** domain shift، اختلاف FOV، occlusion، camera synchronization، long-range association.
- **الترخيص والوصول:** challenge/data access terms؛ الوصول الرسمي وشروط الاستخدام قد تتطلب تسجيلًا أو قيودًا بحثية. `verify-before-use`; لا تُفترض commercial rights.
- **الملاءمة:** MTMC architecture، topology، association، benchmarking؛ غير كافٍ لتقييم اليمن وحده.

### 2.2 CityFlowV2
- **المصدر:** AI City Challenge official data/evaluation pages؛ `https://www.aicitychallenge.org/`؛ استخدم صفحة track/release المحددة بدل روابط mirrors.
- **إحصاءات:** بعض صفحات التحدي تشير إلى توسعة تقارب 46 كاميرا/16 تقاطعًا وقرابة 3.58 ساعة و880 identity و313,931 box؛ هذه الأرقام مرتبطة بإصدار/track ويجب مطابقتها مع manifest الرسمي قبل التوثيق النهائي.
- **annotations:** MTMC boxes، camera IDs، vehicle IDs وevaluation format بحسب الإصدار.
- **الظروف:** urban multi-camera، synchronized views، تباين في المسافة والازدحام.
- **الترخيص:** access/use terms من AI City Challenge؛ لا يجوز استنتاج commercial permission من إتاحة التنزيل. `verify-before-use`.
- **الملاءمة:** أفضل من dataset single-camera لدراسة cross-camera association، لكنه ليس target domain يمنيًا.

### 2.3 AI City Challenge datasets
- **المصدر الرسمي:** `https://www.aicitychallenge.org/`.
- **النطاق:** عدة tracks تشمل traffic analysis، vehicle tracking، MTMC، anomalies أو tasks أخرى حسب السنة.
- **الحجم والهويات والكاميرات:** تختلف جذريًا حسب السنة وtrack؛ لا يوجد رقم واحد صحيح لـ "AI City dataset".
- **annotation:** track-specific formats وevaluation scripts.
- **شروط الوصول:** افحص صفحة data access لكل سنة وtrack، terms، citation، password/registration requirements، وقيود إعادة التوزيع.
- **الملاءمة:** baselines وchallenge evaluation؛ يجب إنشاء `dataset_release.yaml` لكل تنزيل يذكر السنة/track/hash/licence.

### 2.4 VeRi-776
- **المصدر:** Liu et al., CVPR Workshops 2016؛ arXiv:1604.07633؛ مشروع المؤلفين/صفحة dataset يجب تثبيتها عند التنزيل.
- **الحجم:** 776 هوية وقرابة 49k صورة وفق الوصف الشائع للورقة؛ الرقم النهائي يجب ربطه بrelease manifest.
- **الكاميرات:** حوالي 20 camera views.
- **الفئات:** سيارات/مركبات وفق dataset؛ لا تمثل كل taxonomy اليمنية.
- **الظروف:** مدينة حضرية، تعدد زوايا، تغير إضاءة/حجب.
- **الدقة:** crops/images، وليست MTMC video stream كاملًا.
- **annotation:** image path، vehicle identity، camera ID، غالبًا attributes/landmarks بحسب الإصدار.
- **التحديات:** scale/viewpoint/illumination؛ domain shift إلى كاميرات اليمن.
- **الترخيص:** شروط صفحة dataset/المؤلفين؛ `verify-before-use` للبحث والتجاري. لا نعد commercial clearance.
- **الملاءمة:** ReID pretraining/evaluation، وليس traffic flow أو topology end-to-end.

### 2.5 VehicleID
- **المصدر:** Liu et al., ICCV Workshops 2016؛ arXiv:1609.09381؛ الموقع الرسمي المشار إليه في الورقة: `https://vehicleid.ertl.jp/` (تحقق من availability الحالية).
- **الحجم:** يوصف عادةً بعشرات الآلاف من الهويات وأكثر من 200k صورة؛ exact counts تعتمد على release/split، لذلك يجب استخراجها من metadata الرسمي بعد التنزيل.
- **الكاميرات:** صور مركبات من viewpoint محدود نسبيًا؛ ليس benchmark topology متعدد الكاميرات غنيًا مثل CityFlow.
- **annotation:** image/identity وtrain/test splits؛ افحص format الرسمي.
- **الظروف:** vehicle crops مع اختلافات view/illumination.
- **الترخيص:** شروط الموقع/المؤلفين؛ لا تفترض commercial use.
- **الملاءمة:** ReID retrieval وlarge-scale identity split؛ أقل ملاءمة لـ MTMC trajectories.

### 2.6 VehicleNet
- **المصدر:** Zheng et al., IEEE TMM 2020، DOI `10.1109/TMM.2020.3014488`، arXiv:2004.06305.
- **الطبيعة:** multi-source benchmark/learning setup مبني على أربع vehicle datasets عامة، لا ينبغي اعتباره مصدرًا واحدًا متجانسًا دون فحص المكونات.
- **الحجم/الهويات/الكاميرات:** يعتمد على component datasets وإصداراتها؛ exact catalog يحتاج paper supplementary/repository manifests. `verify-before-use`.
- **الظروف:** يهدف لمعالجة intra-class variation وdomain variation عبر datasets.
- **annotation:** inherited labels/identities من المكونات؛ لا تفترض توافق label namespaces.
- **الترخيص:** يجب مراجعة ترخيص كل dataset مكوّن وكل redistribution condition؛ لا commercial clearance تلقائي.
- **الملاءمة:** pretraining/domain generalization لـ ReID، لا يكفي كتقييم target يمني.
- **نتيجة منشورة:** abstract المصدر يذكر 86.07% mAP على private AICity test؛ نتيجة الورقة وليست نتيجة YemenVision.

### 2.7 UA-DETRAC
- **المصدر:** Wen et al., IEEE TITS 2020، DOI `10.1109/TITS.2019.2896952`؛ الموقع الرسمي `https://www.detrac-db.rit.albany.edu/`.
- **الحجم:** نحو 100 فيديو و140k frames وفق الوصف المعروف للمشروع/الورقة؛ ثبت الرقم النهائي من official release.
- **الكاميرات:** single-camera traffic videos، وليست MTMC synchronized network.
- **الفئات:** car, bus, van, others بحسب annotation taxonomy.
- **الظروف:** traffic surveillance من زوايا ثابتة، تغيرات weather/traffic/density.
- **الدقة:** فيديو/frames بمواصفات release؛ تحقق من exact resolution/frame rate.
- **annotation:** vehicle bounding boxes، type، occlusion/visibility وtrajectory information وفق release.
- **التحديات:** occlusion، scale، crowded road، detector/tracker robustness.
- **الترخيص:** official terms/citation؛ `verify-before-use`، ولا commercial assumption.
- **الملاءمة:** detection، vehicle classification، single-camera tracking، density/flow prototypes؛ لا يجيب cross-camera identity.

## 3. Dataset gaps relative to Yemen
- لا توجد في workspace بيانات يمنية معلّمة أو موافقات موثقة.
- datasets العامة لا تغطي بالضرورة أنواع المركبات المحلية، لوحات/ألوان/حمولات، الغبار والضباب والإضاءة القاسية، أو camera placement المحلي.
- معظم datasets لا تعطي ضمانًا تجاريًا؛ يجب حفظ license text/hash وdate of review.
- يجب عدم حفظ لوحات أو وجوه خام في واجهات التحليل؛ redaction/pseudonymization جزء من ingestion.

## 4. Local collection gate
قبل جمع أي فيديو:
1. إثبات تصريح الموقع والكاميرات ومدة المعالجة.
2. تحديد purpose وretention وroles وaudit.
3. mask faces/plates افتراضيًا.
4. فصل raw restricted store عن derived analytics.
5. إنشاء data card وDPIA/مراجعة قانونية حسب الجهة.
6. split حسب vehicle identity + camera + time لمنع leakage.
