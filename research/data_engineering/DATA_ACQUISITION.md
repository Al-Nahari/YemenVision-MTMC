# Data Acquisition and Provenance

## الحالة الحالية

لم تُنزّل أي dataset فعلية في Phase 02. السبب قابل للتدقيق: `DATASET_CATALOG.md` يضع شروط الوصول/الترخيص للبيانات العامة في حالة `verify-before-use`، ولا توجد في workspace موافقات، release hashes، أو manifest رسمي مثبت يسمح بالتنزيل. هذا قرار حوكمة، وليس فشلًا في تنفيذ التنزيل.

## المصادر الرسمية المطلوب مراجعتها

| المصدر | الرابط المرجعي من Phase 01 | ما يجب تثبيته قبل التنزيل |
|---|---|---|
| CityFlow/CityFlowV2 وAI City tracks | https://www.aicitychallenge.org/ | السنة/track، registration، terms، citation، checksum |
| CityFlow repository | https://github.com/JL-DA/CityFlow | code/data separation، license، release commit |
| VeRi-776 | paper/project page من الكتالوج | download authorization، license، exact release |
| VehicleID | https://vehicleid.ertl.jp/ | availability، terms، split metadata |
| VehicleNet | DOI `10.1109/TMM.2020.3014488` وملحقات المصدر | component datasets وredistribution constraints |
| UA-DETRAC | https://www.detrac-db.rit.albany.edu/ | official archive، terms، annotation version |

لا تستخدم mirror أو رابطًا منسوخًا بدل المصدر الرسمي. مراجعة الرابط لا تعني إذن التنزيل أو الاستخدام التجاري.

## آلية manifest

`data/manifests/download_manifest.json` يطلب لكل artifact: dataset، release، HTTPS URL، destination، SHA-256، license status، وموافقة صريحة. الأداة ترفض:

- HTTP أو URL غير HTTPS.
- hash ناقصًا أو ليس SHA-256.
- `license_status` غير مساوي لـ`verified`.
- `approved_for_download=false`.

بعد الموافقة تنفذ `resumable_download`: ملف `.part`، HTTP Range، retry محدود، كتابة atomic، ثم hash verification. تسجل `downloaded_at_utc` وattempts في provenance.

## التشغيل بعد الموافقة فقط

```text
python -m data_engineering.cli.download_manifest data/manifests/approved.json --provenance data/manifests/provenance.json
```

الأمر لا ينبغي تشغيله على manifest الحالي؛ فهو placeholder محمي عمدًا.

## سياسة التخزين

- لا تحفظ الفيديو الضخم في Git.
- `data/raw` و`data/interim` و`data/processed` مذكورة في `.dvcignore`.
- لا تسجل credentials أو cookies أو signed URLs في Git أو logs.
- احفظ hash ونسخة الشروط القانونية وتاريخ المراجعة في dataset card.
- افصل raw restricted عن redacted derivatives.
