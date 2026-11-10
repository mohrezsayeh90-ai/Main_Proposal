# Thesis Template

A LaTeX template for typesetting theses in Persian.

By: Hamid Zarrabi-Zadeh

## License
This work is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
## راهنمای استفاده

این مخزن فعلاً شامل قالب اولیهٔ ارسالی است. متن‌های نمونه، نام‌ها، عنوان‌ها و ساختار پایان‌نامه بدون شخصی‌سازی حفظ شده‌اند؛ تبدیل ساختار به پروپوزال در مرحلهٔ بعد انجام می‌شود.

- فایل اصلی: `thesis.tex`
- مشخصات فارسی و انگلیسی: `front/info.tex`
- متن فصل‌ها: `chapters/`
- منابع: `bibs/full.bib` و `bibs/refs.bib`
- فونت‌های همراه قالب: `styles/fonts/`
- فایل `thesis.pdf` خروجی کامپایل قالب با اصلاحات سازگاری زیر است.

### ساخت PDF

قالب به **XeLaTeX**، **BibTeX** و **latexmk** نیاز دارد. از pdfLaTeX استفاده نکنید.
در Debian/Ubuntu بسته‌های زیر را نصب کنید:

```sh
sudo apt-get update
sudo apt-get install texlive-xetex texlive-lang-arabic texlive-latex-extra texlive-pstricks texlive-science latexmk
```

از ریشهٔ مخزن اجرا کنید:

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error thesis.tex
```

`latexmk` اجرای BibTeX و تکرار کامپایل برای تکمیل ارجاعات و فهرست‌ها را انجام می‌دهد.
فونت فارسی از فایل‌های داخل قالب بارگذاری می‌شود.
تعریف محیط اختیاری `alg` در قالب اصلی به فونت `Times New Roman` اشاره دارد؛ در صورت استفاده از آن محیط، این فونت نیز باید روی سیستم موجود باشد.

در Overleaf فایل `thesis.tex` را به‌عنوان Main document و **XeLaTeX** را به‌عنوان Compiler انتخاب کنید.

### مجوز و انتساب

نام نویسنده، انتساب قالب و مجوز اصلی CC BY 4.0 حفظ شده‌اند. فایل‌های فونت و سایر دارایی‌های همراه همان فایل‌های ZIP ارسالی هستند؛ مجوز هر دارایی تابع شرایط صاحب آن است.

### سازگاری نسخه‌ها

گزینهٔ قدیمی `localise=on` در `styles/common.tex` به `localize=on` تغییر کرده تا با XePersian 25.2.2 همراه TeX Live این محیط سازگار باشد. این اصلاح تنظیمات کامپایل است و متن نمونه یا ساختار سند را تغییر نمی‌دهد.

همچنین ۳۰۲ نویسهٔ نامرئی U+202B از فایل `chapters/preliminaries.tex` حذف شده‌اند؛ این نویسه‌ها در ZIP اصلی پیش از دستورهای LaTeX قرار داشتند و مانع کامپایل فهرست‌ها می‌شدند. متن نمونه حفظ شده است.
