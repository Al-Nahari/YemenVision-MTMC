# مراجعة الأدبيات العلمية — YemenVision MTMC

**الإصدار:** Phase 01 / 2026-11-12  
**حالة الدليل:** مراجعة تأسيسية؛ الأرقام أدناه نتائج منشورة وليست نتائج YemenVision.

## 1. منهجية المراجعة
تم تجميع مصادر أصلية أو سجلات فهرسة قابلة للتحقق، مع إعطاء الأولوية لـ CVPR/ECCV/ICCV/WACV/TITS وAI City Challenge وDOI/arXiv. لم تُستخدم مقتطفات محرك البحث كمصدر نهائي. عند تعذر استخراج صفحة رسمية آليًا، تم تسجيل الرابط الرسمي وحالة `verify-before-use` بدل اختلاق معلومة.

قواعد التقييم:
- لا تُقارن أرقامًا من بروتوكولات أو مجموعات بيانات مختلفة كأنها تجربة واحدة.
- لا تُستخدم نتائج منشورة كخط أساس محقق على اليمن.
- يجب فصل split حسب الهوية والكاميرا والزمن عند بناء تقييم محلي.
- لكل نتيجة تشغيلية يجب تسجيل الإصدار، العتاد، الدقة، batch، FPS، latency، seeds وcommit.

## 2. خريطة الأدبيات حسب المحور

### 2.1 Vehicle Detection
**عائلات مرشحة:** YOLO، RT-DETR، وDetector مفصول قابل للتبديل.

- **YOLOv4 — Bochkovskiy, Wang, Liao (2020)**، arXiv:2004.10934. يعالج كشف الأجسام بزمن حقيقي عبر CSPDarknet، augmentations وبدائل NMS. المصدر يورد أرقامًا على MS COCO وفق إعدادات المؤلفين. القيد: لا يثبت أداء المركبات في الكاميرات اليمنية أو المشاهد بعيدة المدى. قابلية الإعادة جيدة مع الكود والأوزان، لكن يجب فحص ترخيص كل implementation/weights قبل المنتج.
- **YOLOX — Ge et al. (2021)**، arXiv:2107.08430. Detector anchor-free مع decoupled head وSimOTA؛ استُخدم في أعمال tracking اللاحقة. مناسب كـ baseline هندسي سريع، لكن الأرقام المنشورة لا تُنقل إلى اليمن.
- **RT-DETR — Zhao et al. (2023)**، arXiv:2304.08069. Transformer detector real-time يزيل الحاجة إلى NMS في التصميم الأصلي ويتيح ضبط مفاضلة السرعة/الدقة عبر decoder layers. مناسب للمقارنة مع YOLO عندما تكون ازدحامات المركبات وocclusion مهمة. يجب قياس الذاكرة وlatency على العتاد الفعلي.

**قرار Phase 01:** ابدأ بـ YOLO family كخط أساس latency/throughput، وأضف RT-DETR كخط دقة/ازدحام. لا يُختار نموذج نهائي قبل benchmark موحد على split محلي مصرح به.

### 2.2 Vehicle Classification
يمكن اشتقاق النوع من detector class head، أو تدريب classifier/attribute head على crop. يجب تعريف taxonomy محلية قبل التدريب: car, taxi, bus, truck, van, motorcycle, minibus وغيرها حسب التغطية. اختلاف سيارات الأجرة، الحافلات، الشاحنات، الدراجات والمركبات المعدلة في اليمن يجعل إعادة استخدام taxonomy العامة مخاطرة. المقاييس المقترحة: macro-F1، balanced accuracy، per-class recall، confusion matrix، وECE للثقة.

### 2.3 Multi-Object Tracking
- **SORT — Bewley et al. (2016)**، arXiv:1602.00763. Kalman filter + Hungarian assignment؛ baseline بسيط سريع، ضعيف أمام occlusion وغياب detection.
- **Deep SORT — Wojke, Bewley, Paulus (2017)**، ICIP، DOI:10.1109/ICIP.2017.8296962. يضيف appearance descriptor إلى motion association؛ مفيد كنقطة مقارنة، مع اعتماد كبير على detector وReID.
- **ByteTrack — Zhang et al. (2022)**، ECCV 2022، arXiv:2110.06864. يربط detections منخفضة الثقة بدل التخلص منها، ما يحسن استمرارية المسارات في مشاهد الازدحام. المصدر الأصلي والكود يقدمان نتائج على MOT benchmarks؛ لا يجوز نقل تلك الأرقام إلى CityFlow أو اليمن بلا تجربة.
- **BoT-SORT — Aharon, Orfaig, Bobrovsky (2022)**، arXiv:2206.14651. يجمع motion compensation وcamera-motion handling وappearance مع association؛ مرشح قوي للكاميرات الثابتة/المتحركة مع ضبط detector.
- **OC-SORT — Cao et al. (2023)**، CVPR 2023، arXiv:2203.14360. observation-centric motion model، مفيد عندما يتسبب occlusion في انحراف Kalman التقليدي. يجب تثبيت نسخة الكود والبروتوكول قبل المقارنة.
- **StrongSORT — Du et al. (2022)**، arXiv:2202.13514. يحسن Deep SORT عبر detector/embedding/association refinements وAFLink/GSI في النسخ الموسعة. مناسب كمرجع تتبع قائم على appearance، لكنه قد يكون أثقل.

**المقاييس:** HOTA كمقياس رئيسي متوازن، MOTA وIDF1، ID switches، AssA/DetA، FPS وlatency. يجب تقرير المقاييس مع detector نفسه، لأن tracker-only comparison مضلل.

### 2.4 Vehicle Re-Identification
- **VeRi-776 baseline / Vehicle Re-ID — Liu et al. (2016)**، CVPR Workshops، arXiv:1604.07633. يطرح dataset multi-camera للمركبات مع attributes وcamera/view information. القيد: مدينة وبيئة محدودة نسبيًا، ولا تمثل اليمن.
- **VehicleID — Liu et al. (2016)**، ICCV Workshops، arXiv:1609.09381. يركز على vehicle retrieval من صور مركبات، مع split حسب الهوية. قوي لتقييم global retrieval لكنه أقل تمثيلًا لـ multi-camera trajectories.
- **VehicleNet: Learning Robust Visual Representation for Vehicle Re-identification — Zheng, Ruan, Wei, Yang, Mei (2020)**، IEEE TMM، DOI:10.1109/TMM.2020.3014488، arXiv:2004.06305. يجمع أربع مجموعات عامة ويقترح progressive representation learning عبر generic ثم target-domain fine-tuning. الملخص الأصلي يورد 86.07% mAP على private AICity test ونتائج تنافسية على VeRi-776 وVehicleID؛ هذه نتائج منشورة للمصدر وليست تحققًا من YemenVision. القيد: domain composition والاعتماد على بيانات عامة/اختبار خاص.
- **TransReID: Transformer-based Object Re-Identification — He et al. (2021)**، arXiv:2102.04378. يستخدم Transformer وذواكر/تحسينات خاصة بـ ReID. مناسب كـ ViT baseline عند توفر compute، مع ضرورة تثبيت checkpoint license وdata protocol.
- **PVEN:** لم يُثبت في هذه الجلسة سجل ببليوغرافي أصلي موثوق بالاسم المختصر، لذلك لا يُدرج كمرجع مُثبت ولا يُستخدم في قرار baseline. يُعاد بحثه من الاسم الكامل/المؤلفين قبل اعتماده.
- **DINOv2 — Oquab et al. (2023)**، arXiv:2304.07193. feature extractor ذاتي الإشراف قوي تجريبيًا عبر مهام رؤية متعددة. ليس baseline vehicle-ReID متخصصًا بحد ذاته؛ يُستخدم فقط كـ ablation/feature initialization مع فحص ترخيص الأوزان.

**مقاييس ReID:** Rank-1/5/10، mAP، CMC، cross-camera mAP، وcalibration/abstention عند استخدام المطابقة في الإنتاج. يجب منع تسرب نفس المركبة بين train/validation/test.

### 2.5 Multi-Camera Multi-Object Tracking وCross-Camera Matching
- **CityFlow: A City-Scale Benchmark for Multi-Target Multi-Camera Vehicle Tracking and Re-Identification — Tang et al. (2019)**، CVPR 2019، DOI:10.1109/CVPR.2019.00440. يقدم benchmark متزامنًا متعدد الكاميرات للمركبات ويقيس MTMC tracking وReID. المنهجيات المشاركة تعتمد على detector، single-camera tracking، appearance features، temporal/spatial constraints وglobal association. القيد: بيئة أمريكية ومركبات/كاميرات لا تمثل اليمن.
- **CityFlowV2 / AI City Challenge Track 3 material — Tang et al. and challenge organizers (2022-era track)**. توسعة benchmark متعددة الكاميرات؛ الإحصاءات وشروط الاستخدام يجب قراءتها من صفحة الإصدار/التحدي المحددة قبل التنزيل. لا نثبت رقمًا غير موثق في هذه الحزمة.
- **CityTrack: Improving City-Scale Multi-Camera Multi-Target Tracking by Location-Aware Tracking and Box-Grained Matching — Lu et al. (2023)**، arXiv:2307.02753. يقترح location-aware tracking وbox-grained matching؛ مناسب كمرجع للتجميع المكاني، لكن لا يثبت ملاءمة اليمن.

**تصميم association المقترح:** appearance embedding + time window + camera transition prior + direction/road geometry + Hungarian assignment في المرحلة الأولى. graph matching/GNN يؤجل إلى ablation بعد توفر بيانات كافية؛ لا يُستخدم لتكوين سجل فردي غير محدود.

### 2.6 Camera Topology Modeling
لا توجد في هذه الحزمة دعوى أن نموذجًا واحدًا حُسم كأفضل topology. نوصي بـ:
1. خريطة كاميرات مصرح بها مع IDs وتوقيت/موقع تقريبي وFOV.
2. transition matrix احتمالية مستخرجة من ground truth أو pseudo-labels مراجعة بشرية.
3. temporal travel-time distributions بدل حدود زمنية ثابتة.
4. versioned calibration and topology snapshots.
5. اختبارات ablation: appearance فقط، time فقط، topology فقط، ثم fusion.

### 2.7 Vehicle Attribute Recognition
اللون، النوع، make/model عند الإمكان، اتجاه الحركة، وخصائص مرئية غير حساسة يمكن أن تقلل الالتباس. لا يجب استنتاج خصائص غير مرئية أو استخدام attributes كمعرّف قطعي. المقاييس: macro-F1 وper-attribute AUROC/accuracy، مع missing/unknown class وقياس calibration. خصائص اليمن تحتاج annotation policy خاصة لأن الطلاء والملصقات والحمولة وزوايا التصوير تختلف.

### 2.8 License Plate Recognition كإشارة اختيارية
يجب أن يكون LPR disabled-by-default في التحليلات العامة، مع masking/redaction في الواجهات والتخزين. لا يُستخدم كمعرف دائم أو كبديل عن association الاحتمالي. أي تجربة LPR يجب أن تتطلب تفويضًا صريحًا، retention قصيرًا، تشفيرًا، access audit، وقياس false positive/false negative تحت الإضاءة واللوحات اليمنية. لم تعتمد هذه المرحلة benchmark LPR بعينه لأن المجال القانوني ومصدر بيانات اللوحات المحلية غير محسومين.

### 2.9 Traffic Flow Analytics وDensity Estimation
- flow: line/zone crossing من المسارات مع direction وtime aggregation.
- speed: homography أو معايرة هندسية؛ لا تُعرض سرعة مطلقة دون calibration.
- density: count per zone/road segment، occupancy إن توفرت geometry، وconfidence intervals.
- metrics: MAE/RMSE/MAPE بحذر عند الصفر، count error، directional F1، travel-time MAE، queue-length error.

يجب تقييم التحليلات على فترات زمنية منفصلة، مع عدم اعتبار tracker IDs عبر الكاميرات حقيقة إلا في ground truth.

### 2.10 Domain Adaptation
المشكلة المركزية هي domain shift بين datasets العامة والمواقع اليمنية: الإضاءة، الغبار، الضباب، نوع المركبات، الكاميرات، الضغط/التشويه، اللغة/اللوحات، وكثافة المرور. مسار آمن:
- source-only baseline.
- supervised fine-tuning على subset محلي صغير مصرح.
- weak/semi-supervised adaptation مع pseudo-label audit.
- style/illumination augmentation مع اختبار cross-domain.
- domain-specific calibration وerror taxonomy.
لا نعتبر domain adaptation ناجحًا إلا إذا تحسن target test مستقل دون تدهور غير مقبول على source holdout.

## 3. خلاصة الاختيار العلمي الأولي
| المهمة | Baseline مرشح | سبب الترشيح | المقياس الأساسي | قيد القرار |
|---|---|---|---|---|
| Detection | YOLO family + RT-DETR | سرعة مقابل Transformer detector | mAP50-95، recall، latency | benchmark محلي موحد |
| Classification | detector head + crop classifier | أقل تعقيدًا ثم تحسين مستقل | macro-F1، balanced accuracy | taxonomy يمنية |
| Single-camera MOT | ByteTrack | قوي وبسيط وقابل للدمج | HOTA، IDF1، ID switches | يعتمد على detector |
| MOT ablation | BoT-SORT وOC-SORT | motion/appearance alternatives | HOTA، IDF1، FPS | ضبط حسب camera motion |
| Vehicle ReID | CNN baseline ثم TransReID | baseline قابل للتفسير ثم ViT | mAP، Rank-1، cross-camera mAP | split حسب الهوية |
| Feature ablation | DINOv2 extractor | اختبار تمثيل عام لا ادعاء متخصص | retrieval mAP/Rank-1 | checkpoint/license/compute |
| MTMC association | embedding + temporal/topology + Hungarian | قابل للتفسير والحَوْكمة | IDF1، HOTA، ID switches، pairwise AP | احتمالية ومحدودة الغرض |
| Topology | transition matrix احتمالية | constraint واضح وقابل للتدقيق | association precision/recall | يحتاج ground truth |
| Attributes | multi-task head | enriches matching/analytics | macro-F1 وcalibration | unknown class ضرورية |
| Flow | line/zone counting | operationally simple | count MAE، directional F1 | camera calibration |
| Density | zone occupancy/count | مناسب للتقارير | MAE/RMSE/interval coverage | لا يدعي absolute density بلا geometry |

## 4. قرارات غير محسومة
- لا يمكن اختيار model size أو batch أو CUDA setting قبل فحص البيئة الفعلية.
- لا يمكن اعتماد commercial use لأي dataset عامة قبل مراجعة شروطها الحالية وحقوق مكونات الفيديو.
- لا يمكن اعتماد LPR أو persistence طويل للـ embeddings ضمن نطاق الخصوصية الحالي.
- PVEN وVehicleNet dataset composition التفصيلي يحتاجان مراجعة المصدر/الملحق قبل استخدامهما في خطة تنزيل.
