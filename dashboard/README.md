# YemenVision Dashboard (React)

واجهة لوحة التحكم مبنية بـ React + TypeScript + Vite و Tailwind CSS.
الخادم الخاص بها هو تطبيق FastAPI الموجود في `backend/`.

## التشغيل

```bash
npm install
npm run dev
```

ثم افتح `http://127.0.0.1:4200/`.

## البناء

```bash
npm run build
npm run preview
```

## إعداد الاتصال بالخادم

من صفحة «الإعدادات» داخل الواجهة يمكن ضبط:

- عنوان API (الافتراضي: `http://127.0.0.1:8000/api/v1`)
- مفتاح API (`X-API-Key`)

يتم حفظ هاتين القيمتين في `localStorage` داخل المتصفح فقط.
