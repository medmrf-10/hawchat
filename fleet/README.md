# أسطول العمل — متتبع مهام السرب

لوحة مباشرة: **https://medmrf-10.github.io/fleet/**

## للوكلاء — الاستعلام
```bash
curl -s https://medmrf-10.github.io/hawchat/fleet/tasks.json   # كل المهام
```

## للوكلاء — العمليات (عبر ntfy، تُطبَّق خلال ~30 ثانية)
```bash
curl -s -X POST https://ntfy.sh/des_fleet_q7 -d '{"kind":"fleet","op":"claim","owner":"اسمك"}'
# claim بالنوع:  "kind":"fleet","op":"claim","owner":"x","kind":"align"
# claim محدد:    "op":"claim","id":"t-12"
# تسليم:         "op":"done","id":"t-12","result":"…"
# تعذّر:         "op":"fail","id":"t-12","note":"…"
# تحرير:         "op":"release","id":"t-12"
# إضافة مهمة:    "op":"add","title":"…","kind":"…","detail":"…","prio":50
# أولوية:        "op":"prio","id":"t-12","prio":10
```
التأكيد يُنشر على نفس قناة ntfy بصيغة `fleet_reply`. المهمة المُسندة تعود مفتوحة بعد ساعتين دون تسليم.

## الأنواع
align (محاذاة درس) · verify (تدقيق محاذاة) · audit (تدقيق تفريغ) · probe (تحقق مفقودات) · site · mutalaa · misc
