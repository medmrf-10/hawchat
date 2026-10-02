# الثيم الموحّد — مستخرج من des/durus v1

> هذا الملف هو المرجع التصميمي لكل ما نبنيه لاحقاً. كل صفحة أو أداة جديدة تتبع هذه المواصفات حرفياً.

## الألوان (CSS variables)

| المتغير | القيمة | الاستخدام |
|---|---|---|
| `--bg` | `#0b0f1a` | خلفية الصفحة — كحلي داكن جداً |
| `--bgt` | `rgba(11,15,26,.92)` | خلفية الشريط العلوي (مع blur) |
| `--card` | `#141b2e` | البطاقات والحقول |
| `--card2` | `#1a2238` | بطاقة مميزة / تدرج مع card |
| `--border` | `#2a3350` | حدود كل عنصر |
| `--txt` | `#f5f1e8` | النص الأساسي — عاجي |
| `--dim` | `#8b93b0` | النص الخافت والوصف |
| `--acc` | `#c9a24b` | الذهبي الأساسي (حدود hover، أزرار فعالة) |
| `--acc2` | `#e8c97a` | الذهبي الفاتح (روابط، أيقونات، عناوين) |
| `--acc3` | `#8b7cf6` | بنفسجي ثانوي (تمييز إضافي) |
| `--ok` | `#46c96d` | نجاح / صحيح |
| `--skel` | `#141d3a` | skeleton loading |

## الخطوط

- **عناوين وهوية**: `Amiri` (var `--font-ar`) — خط نسخي أصيل
- **واجهة ونصوص**: `IBM Plex Sans Arabic` (var `--font-ui`) أوزان 300–700
- الاستدعاء: `<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap" rel="stylesheet">`
- اتجاه الصفحة دائماً `dir="rtl"` و`lang="ar"`.

## القياسات

- نصف الأقطار: `--r-lg:18px` بطاقات كبيرة · `--r-md:12px` أزرار وحقول · `--r-sm:8px` عناصر صغيرة · chips/pills دائري كامل `border-radius:99px`
- حد أدنى لأهداف اللمس: `34–36px` (الرقائق لا تصغر عن ذلك أبداً)
- عرض المحتوى: `max-width:1100px` بهوامش `16px`
- الشريط العلوي: `position:sticky` + `backdrop-filter:blur(14px)` + حد سفلي `--border`
- سطر النص: `line-height:1.7`

## الأنماط المعيارية

- **العلامة (brand)**: خط Amiri عريض، تدرج ذهبي `linear-gradient(135deg,var(--acc2),var(--acc))` مقصوص على النص
- **البطاقة**: `background:var(--card); border:1px solid var(--border); border-radius:var(--r-lg)`، عند hover: `border-color:var(--acc); transform:translateY(-2px)`
- **الرقاقة (chip)**: pill بحدود `--border`، الحالة الفعالة `background:var(--acc); color:var(--bg); font-weight:800`
- **الدخول**: `animation:cin .4s both` — `@keyframes cin{from{opacity:0;transform:translateY(8px)}}`
- **التظليل والتمرير**: `::selection` ذهبي على كحلي؛ scrollbar بحد `10px` وإبهام `--border`
- حقل البحث: بطاقة `border-radius:12px` بارتفاع `42–46px` وأيقونة SVG رمادية

## الهوية البصرية

- أيقونة التطبيق: هلال ذهبي متدرج على كحلي `#0b0f1a` داخل إطار دائري رفيع (icons/)
- `theme-color` و`background_color` دائماً `#0b0f1a`
- الجو العام: ليلي، هادئ، ذهبي فاخر — لا ألوان فاقعة، لا خلفيات فاتحة

## البنية

كل تطبيق يحمل `theme.css` (هذا الملف المستخرج بنفس الاسم) + manifest قابل للتثبيت. لا تُعاد كتابة الألوان يدوياً في الصفحات — المتغيرات فقط.
