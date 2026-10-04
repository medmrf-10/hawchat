# قاعدة حالة التفريغ — transcription-state

قاعدة الحالة الكاملة لمشروع تفريغ الدروس. **أُوقفت كل التنزيلات** بأمر المالك — هذه اللقطة هي الحقيقة الوحيدة لمن يستكمل العمل: لا تُعيد تفريغ ما هو مفرّغ، وأكمل من حيث توقّفت.

## الملفات

- `index.json` — كل السلاسل الـ1006: `{id, key, sheikh, url, exp, files_expected, downloaded, transcribed, pending, active, bad, frozen, skipped, paused, state, resume_from, tr_dir, pipe_dir}`
- `sheikhs.json` — تجميع لكل شيخ: عدد السلاسل، المتوقَّع، المفرَّغ، المنزَّل، الناقص صوتاً
- `series/<id>.json` — تفصيل ملف-ملف لكل سلسلة: كل حلقة `{n, file, downloaded, audio, transcribed, txt}`

## معنى الحقول

| الحقل | المعنى |
|---|---|
| `exp` | عدد الحلقات الأصلي في قائمة التشغيل |
| `downloaded` | ملفات الصوت الموجودة محلياً |
| `transcribed` | ملفات نصية موجودة فعلاً |
| `state` | `done` مكتملة · `partial` بدأت · `frozen` مجمّدة بأمر · `untouched` لم تُمسّ |
| `resume_from` | أول رقم حلقة غير مفرّغة — ابدأ من هنا |
| `frozen/skipped/paused` | قرارات إدارية سارية — لا تعمل عليها |
| `pending/active/bad` | طابور agy لحظة اللقطة |

## أماكن التفريغات الفعلية (على جهاز old)

- `~/durus/transcripts_agy/<sid>_<name>/NNN_*.txt` — التخزين الرئيسي (id-prefixed)
- `~/durus/transcripts/` ، `~/durus/transcripts_low_backup/` — مخازن قديمة
- `~/me/transcripts/durus/<sid>/<n>.txt` — تخزين مرقّم صفريّاً (n = حلقة-1)؛ في الملفات يظهر `txt` بادئة `me:`

## قواعد الاستكمال

1. اختر شيخاً/سلسلة، اقرأ `series/<id>.json`.
2. الحلقات `transcribed=true` **موجودة — لا تُعيدها إطلاقاً**.
3. حلقة `downloaded=true, transcribed=false`: الصوت جاهز — فرّغ فقط.
4. حلقة `downloaded=false`: تحتاج تنزيل الصوت أولاً (من `url` = قائمة يوتيوب).
5. `state=frozen/skipped/paused`: لا تعمل عليها حتى إشعار آخر.

## الأرقام اللحظية

- سلاسل: 1006 · شيوخ: 11
- مفرّغ: 3,419 ملفاً · متوقَّع إجمالاً: 52,251
