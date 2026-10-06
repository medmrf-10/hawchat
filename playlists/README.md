# playlists — باب قوائم التشغيل (hawshat)

مجلد مستقل — لا خلط مع بقية الأبواب.

## البنية
- `data/sheikhs.json` — ملف واحد: سجل كامل لكل شيخ من الـ33 (id, slug, name, name_display, aliases, group, photo, channels[], series[], status, notes)
- `img/` — صور المشايخ باسم `<slug>.jpg` يطابق حقل photo

## مسار العمل (من أمر محمد)
اختيار السلسلة → تفريغ agy cli → محاذاة كلمة-لكلمة → رفع التفريغ + ملف المحاذاة → ربط بفيديو يوتيوب.

## القاعدة
status لكل شيخ: pending → series_selected → transcribed → aligned → published.

## انضباط REV (sw.js) — للمنفّذين

| ما تغيّر | يصل للمستخدم كيف | المطلوب |
|---|---|---|
| `*.html` | شبكة-أولاً (3ث) | لا شيء؛ لكن لا تعتمد على دوال جديدة في common.js دون حماية `typeof fn==='function'` |
| `*.css` `*.js` الخطوط `/icons/*` `manifest` `offline.html` `icons.svg` | cache-first حتى REV جديد + ضغط «تحديث»؛ `?v=` مؤثّر | رفع `REV` في `sw.js` (و`?v=` معه) |
| `*.json` (إحصاءات، series، read، lessons/index) | SWR في DATA؛ متأخر زيارة واحدة؛ يُمسح مع REV | لا شيء عادة |
| `*.txt` `.align.json` الصور | SWR في TEXT (ثابت عبر REV) | متأخر زيارة واحدة |
| `sw.js` نفسه | فحص المتصفح عند كل ملاحة | رفع REV دائماً |

المستندات تُخزّن بمفتاح المسار فقط (ignoreSearch) — قالب واحد يخدم كل استعلاماته.


## core.js — المصدر الوحيد لمنطق السلاسل والدروس

- `HC.findRow(q)` يحدد الصف من أي رابط (`?r` / redirects / `?s` / `?k` / `?id` / `?sh&s`).
- `HC.lessons(row)` يجمع دروس الصف وما يتوفر في كل درس (`has.listen/read/yt/aud/sm/qu`).
- `HC.href(ctx,x,mode)` رابط الدرس في كل وضع؛ `HC.best(x,mode)` الباب الافتراضي.
- `HC.mountTabs(mode)` شريط تبويبات أوضاع الدرس نفسه + سجل «تابع من حيث توقفت» (`hist` في `hc_store_v1`).
- لا تنسخ منطق الحل أو الروابط داخل صفحة — أضفه هنا. `row.ld` (من gen_stats) = مجلد lessons الحقيقي أو `''`.
- قبل الدمج: `python3 scripts/crawl_site.py` يزور كل الصفحات (يعمل أيضاً في CI ويمنع النشر عند الفشل).
