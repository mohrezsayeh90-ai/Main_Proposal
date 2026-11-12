# گزارش پیاده‌سازی بخش ۴٫۱

بررسی در ۱۲ نوامبر ۲۰۲۶ انجام شد.

## تغییرات و دامنه

- عنوان فصل چهارم به «نتایج» تغییر کرد.
- متن نمونهٔ فصل حذف شد.
- بلوک فارسی پیوست، عیناً در `chapters/results.tex` درج شد.
- بخش ۴٫۱ سه زیربخش، دو شکل و دو جدول دارد.
- متن فصل سوم و بخش‌های دیگر تغییر نکرد.
- مطالعات پارامتری جدید وارد این بخش نشدند.
- تنها اصلاح صفحه‌آرایی، `\enlargethispage{2\baselineskip}` پیش از پاراگراف پایانی است.
- این اصلاح از ایجاد صفحه‌ای تقریباً خالی جلوگیری کرد.

## نسخهٔ مرجع و منشأ داده‌ها

مخزن مرجع: `Particle_Shape_Reconstruction`.
نسخهٔ ثابت: `e21654555f6d615fcea1efe48f2c84e8f0aa5241`.

[مشاهدهٔ نسخهٔ مرجع](https://github.com/mohrezsayeh90-ai/Particle_Shape_Reconstruction/tree/e21654555f6d615fcea1efe48f2c84e8f0aa5241/New_Main_Results)

تمام مسیرهای زیر، نسبت به `New_Main_Results/runs/formation_20261112_cpu/` هستند.

- مثلث: `historical_reruns/triangle_1794495372673521753/fresh_verification/`.
- حروف: `historical_reruns/letters_1794495952386815010/fresh_verification/{S_6,C_6,T_6}/`.
- هر پوشه شامل `metrics.json` و `release_schedule.csv` است.
- اردک‌ها: `tables/F02_archived_ducks.csv` و `historical_replays/*/metrics.json`.
- ترسیم اردک‌ها از `historical_replays/*/trajectories.npz` انجام شد.
- منشأ شکل‌ها: `figures/thesis/manifest.json` و `figures_manifest.json`.

مثلث و حروف، بازاجراهای تازه با تنظیمات تاریخی هستند.
اردک‌ها، بازپخش برنامه‌های رهاسازی ذخیره‌شده هستند.
خطاها و فاصله‌ها از ارزیابی‌های تازه نقل شدند.
کمینهٔ فاصله روی بازهٔ حضور مشترک ذرات محاسبه شده است.
تعداد ذرات و نوع رهاسازیِ چهار اردک متفاوت‌اند.
بنابراین، مقایسهٔ آن‌ها آزمون کنترل‌شدهٔ نوع رهاسازی نیست.

## شکل‌های نهایی

| شکل | ورودی مرجع | فایل استفاده‌شده در پایان‌نامه |
| --- | --- | --- |
| ۴٫۱ | `figures/thesis/F01.pdf` | [مثلث و حروف](../figs/chapter4/formation-basic-cases.pdf) |
| ۴٫۲ | ترسیم‌کنندهٔ `f02` و داده‌های چهار بازپخش | [چهار اردک](../figs/chapter4/formation-duck-replays.pdf) |

شکل نخست، کپیِ بایت‌به‌بایت فایل نسخهٔ مرجع است.
شکل دوم، فقط برای حذف زیرنویس داخلی بازترسیم شد.
ترتیب پنل‌ها ۲۰ ثابت، ۲۸ آزاد، ۴۲ ثابت و ۶۴ آزاد است.
دیسک‌های مرجع، نشانگرهای هدف و مراکز شبکه حفظ شدند.
محورها بی‌بعد هستند و مقیاس مکانی آن‌ها برابر است.
هر دو فایل، PDF برداری و بدون تصویر رستری هستند.
هیچ زیرنویس فارسی داخل PDFهای شکل‌ها وجود ندارد.
هر زیرنویس، فقط یک‌بار در LaTeX و زیر شکل آمده است.
راهنماها و برچسب‌ها در اندازهٔ نهایی بازبینی شدند.

## بررسی متن، اعداد و صفحه‌آرایی

- هر ۳۱ کمیت دو جدول با منابع تطبیق داده شد.
- گردکردن، مطابق دقت نمایش هر ستون کنترل شد.
- زمان هدف و زمان‌های رهاسازی مثلث نیز کنترل شدند.
- ۵۱ جملهٔ متن و زیرنویس‌ها بررسی شدند.
- طول بیشینهٔ جمله‌ها، ۱۲ واژه بود.
- هر عبارت ریاضی، یک واحد شمرده شد.
- ترکیب‌های نیم‌فاصله‌دار، یک واژه شمرده شدند.
- ارجاع بخش ۳٫۲ و رابطهٔ ۳٫۴۱ حل شدند.
- هیچ ارجاع حل‌نشده یا نویسهٔ مفقود گزارش نشد.
- هیچ هشدار کادر بیرون‌زده‌ای در فصل چهارم وجود ندارد.
- جدول‌ها در عرض متن قرار دارند.
- چینش اعداد و صفحه‌های شکل‌ها بصری بررسی شدند.

| مورد | شماره | صفحهٔ متن اصلی | صفحهٔ فایل PDF |
| --- | --- | ---: | ---: |
| فصل نتایج و آغاز بخش | ۴ و ۴٫۱ | ۳۴ | ۴۱ |
| آرایش ساده | ۴٫۱٫۱ | ۳۴ | ۴۱ |
| شکل مثلث و حروف | ۴٫۱ | ۳۵ | ۴۲ |
| حروف با شش ایستگاه | ۴٫۱٫۲ | ۳۶ | ۴۳ |
| جدول حروف | ۴٫۱ | ۳۶ | ۴۳ |
| بازپخش اردک‌ها | ۴٫۱٫۳ | ۳۶ | ۴۳ |
| شکل و جدول اردک‌ها | ۴٫۲ | ۳۷ | ۴۴ |

## نتیجهٔ ساخت

[PDF نهایی پایان‌نامه](../thesis.pdf) با موفقیت ساخته شد.
خروجی نهایی **۵۲ صفحه** دارد.
`latexmk` با کد خروج صفر پایان یافت.
هشدار مقصد تکراری PDF و هشدارهای قبلی قالب باقی‌اند.
این هشدارها مانع ساخت خروجی نشدند.

فرمان واقعی ساخت از ریشهٔ مخزن:

```sh
TEXMFHOME=/workspace/.setup/texlive/usr/share/texlive/texmf-dist \
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error thesis.tex
```

مسیر `TEXMFHOME` فقط به نصب محلی این محیط مربوط است.
آموزش، بهینه‌سازی یا بازپخش عددی جدید اجرا نشد.
مخزن پژوهشی در این مرحله تغییر نکرد.

## بازتولید بازترسیم اردک‌ها

این wrapper از کد همان نسخهٔ ثابت استفاده می‌کند.
خروجی‌های میانی فقط در پوشهٔ موقت نوشته می‌شوند.
نوشتن جدول جانبیِ ترسیم‌کننده غیرفعال است.
وابستگی‌ها همان محیط ثبت‌شدهٔ پژوهشی هستند.
از محیط دارای NumPy، Matplotlib، PyTorch، Numba و Shapely استفاده کنید.
بسته‌های `arabic-reshaper` و `python-bidi` نیز برای بارگذاری کد لازم‌اند.
مسیر مخزن‌ها را در صورت نیاز اصلاح کنید.

```python
import sys,subprocess,importlib.util,tempfile,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
research=Path('/workspace/Particle_Shape_Reconstruction');root=research/'New_Main_Results'
revision='e21654555f6d615fcea1efe48f2c84e8f0aa5241'
tmp=Path(tempfile.mkdtemp(prefix='section41-ducks-',dir='/tmp'))
source='New_Main_Results/plot_formation_campaign.py'
(tmp/'plot_source.py').write_bytes(subprocess.check_output(['git','show',revision+':'+source],cwd=research))
sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('section41_plot_source',tmp/'plot_source.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.ROOT=root;module.RUN=root/'runs/formation_20261112_cpu';module.OUT=tmp
module.write_csv=lambda *args,**kwargs:None
obj=object.__new__(module.Figures)
def save(fig,code,title,inputs,description):
 fig.set_size_inches(6.8,3.7)
 for legend in fig.legends:legend.set_bbox_to_anchor((.5,0))
 fig.tight_layout(rect=(0,.085,1,1),pad=.6,h_pad=1.2,w_pad=1.)
 fig.savefig(tmp/'F02-caption-free.pdf',bbox_inches='tight',pad_inches=.04,metadata={'Title':'Duck formation replays','CreationDate':None,'ModDate':None})
 module.plt.close(fig)
obj.save=save
obj.f02()
out=Path('/workspace/Main_Proposal/figs/chapter4/formation-duck-replays.pdf')
out.write_bytes((tmp/'F02-caption-free.pdf').read_bytes())
print('F02 temporary output:',tmp)
print('F02 output SHA256:',hashlib.sha256(out.read_bytes()).hexdigest())
```

## اثرانگشت فایل‌های تحویل

- `chapters/results.tex`: `93faeb63a299b304afa05579b90563faef6e8e600a501a77ac48a8dcf3ff56c4`
- `figs/chapter4/formation-basic-cases.pdf`: `8a265e9d562536eed94f5f68c9af0cff153cd0e9988e40a13eacc78907956c91`
- `figs/chapter4/formation-duck-replays.pdf`: `7003dc31d62568bde66ae9d13c4507668c4f42028c99a2ec0e86e3720fd31ab7`
- `thesis.pdf`: `2754fb139f20017403c43bfeff2cc40beb2054abaa5d556abc2c4831f574a9b7`
