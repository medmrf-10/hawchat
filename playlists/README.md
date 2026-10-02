# playlists — باب قوائم التشغيل (hawchat)

مجلد مستقل — لا خلط مع بقية الأبواب.

## البنية
- `data/sheikhs.json` — ملف واحد: سجل كامل لكل شيخ من الـ33 (id, slug, name, name_display, aliases, group, photo, channels[], series[], status, notes)
- `img/` — صور المشايخ باسم `<slug>.jpg` يطابق حقل photo

## مسار العمل (من أمر محمد)
اختيار السلسلة → تفريغ agy cli → محاذاة كلمة-لكلمة → رفع التفريغ + ملف المحاذاة → ربط بفيديو يوتيوب.

## القاعدة
status لكل شيخ: pending → series_selected → transcribed → aligned → published.
