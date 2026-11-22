# نسخهٔ بازبینی پایان‌نامه

نسخهٔ هایلایت‌شده در [thesis_review_annotated.pdf](review_annotated/thesis_review_annotated.pdf) است.
[فهرست بازبینی](review_annotations_index.md) عبارت‌ها، سطرها، صفحه‌ها و وضعیت بررسی را ثبت می‌کند.

کپی از درخت کاری محلی Main_Proposal تهیه شد.
شناسهٔ ثبت مبنا 9690560dd817fc3bea96007fd4c200a1141db712 است.
ادغام محلی فصل دوم نیز در کپی وجود دارد.
هش SHA-256 هر ۲۲۹۹ فایل اصلی پیش و پس از کار یکسان بود.
متن دو فصل پس از حذف نشان‌گذاری‌ها، با متن اصلی یکسان است.
همهٔ تصاویر، منابع و داده‌های کپی با فایل‌های اصلی تطبیق داده شدند.

## ساخت مجدد

از پوشهٔ review_annotated با XeLaTeX و BibTeX بسازید.
بستهٔ bidihl و سبک‌ها و قلم‌های قالب در ساخت استفاده می‌شوند.
در محیط فعلی، TEXMFHOME به درخت محلی TeX Live اشاره می‌کند.

    cd review_annotated
    export TEXMFHOME=/workspace/.main-proposal-tex/usr/share/texlive/texmf-dist
    latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error thesis.tex

فرمان ساخت، thesis.pdf را در همین کپی بازسازی می‌کند.
خروجی تحویلی با نام مستقل thesis_review_annotated.pdf ذخیره شده است.
PDF نهایی ۱۲۵ صفحه دارد. صفحه‌های نمونه برای اتصال حروف و ترتیب راست‌به‌چپ بررسی شدند.
رنگ‌ها در متن، عنوان شکل و خانهٔ جدول بررسی شدند.
گزارش ساخت در [build.log](build.log) موجود است.
