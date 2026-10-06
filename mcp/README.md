# خدمة MCP للمواقع الثلاثة — hawshat

خادم MCP واحد (`turath_mcp.py`) يخدم مواقع البوابة الثلاثة من نفس واجهات
البيانات الثابتة التي تقرؤها الصفحات:

- **موقع الحديث** (`/hadith/`) — خدمات الحديث: كتب الشامي الأربعة، المتون،
  72 شرحاً، البحث في النصوص والمواضع (repo `hdth`).
- **موقع التفسير** (`/tafsir/`) — خدمات التفسير: الآيات و41 طبعة تفسير
  (repo `tfsr`).
- **مكتبة التراث** (`/turath/`) — خدمات العلوم الأخرى: سيرة، فقه مالكي،
  تراجم، تاريخ، أصول، علوم قرآن، قواعد فقه، عقيدة، تزكية — 736 كتاباً.

## التشغيل

```bash
pip install mcp
python3 mcp/turath_mcp.py          # stdio — يقرأ من Pages مباشرة
TURATH_LOCAL=/path/to/repos python3 mcp/turath_mcp.py   # قراءة محلية دون إنترنت
```

## الأدوات (11)

`describe_service` · `list_books` · `get_book` · `get_part` · `search_text`
(union/intersect عبر فهارس الكلمات المشطّرة) · `search_phrase` · `list_hadiths`
· `get_tafsir` · `get_tafsir_surah` + أدوات الفهرسة.

كل علم يُطلب بالاسم: `science="hadith"` للحديث، `"tafsir"` للتفسير،
وباقي الأسماء لعلوم التراث (انظر `SCIENCES` في الملف).
