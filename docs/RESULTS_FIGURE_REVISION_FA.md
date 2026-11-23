# تحویل بازچینی شکل‌های فصل نتایج

نسخهٔ مبنا و آخرین main هنگام شروع: `9690560dd817fc3bea96007fd4c200a1141db712`.
این ویرایش بر اساس فایل `codex_thesis_results_revision (2).txt` انجام شد.

## دامنه و خروجی

- متن فصل چهارم، پیوست تکمیلی و هفت ارجاع کوتاه فصل سوم به‌روز شدند.
- ۲۶ خروجی تصویری در عرض ۶٫۲۷ اینچ از داده‌های ذخیره‌شده بازترسیم شدند.
- هشت زنجیرهٔ اصلی و گالری هفت ورودی در متن اصلی قرار دارند.
- متن اصلی ۲۴ شکل و شش جدول دارد؛ پیوست ۲۱ شکل و چهار جدول دارد.
- Master9 و ابهام فیزیکی علامت Master10 حفظ شدند.
- کدهای قدیمی ترسیم و حالت‌های نسخه‌بندی‌شدهٔ آن‌ها تغییر نکردند.
- بستهٔ placeins فقط برای مرزبندی محلی شناورها افزوده شد؛ هندسهٔ صفحه تغییر نکرد.
- مخازن FLOW و MAG فقط خوانده شدند و وضعیت Git آن‌ها پاک ماند.
- هیچ وزن، حل عددی، برنامهٔ رهاسازی یا دادهٔ پژوهشی تغییر نکرد.

## تصحیح تفسیر سقف رهاسازی

CSV ثبت‌شده برای سقف‌های ۴، ۶ و ۸، به‌ترتیب فقط یک اجرای تکمیل‌شده دارد.
اعداد «۱/۳، ۱/۳، ۱/۳، ۳/۳» تعداد تکمیل‌شده از سه شروع برنامه‌ریزی‌شده هستند.
پذیرش از اجراهای تکمیل‌شده به‌ترتیب «۰/۱، ۱/۱، ۱/۱، ۳/۳» است.
شکل این دو مفهوم را جدا می‌کند؛ شروع‌های اجرا‌نشده پذیرفته یا ردشده محسوب نشدند.
بارهای برنامهٔ منتخب با سقف شش: B1/B2/B3 برابر ۵/۴/۳، و T1/T2/T3 برابر ۶/۵/۱.
جفت بحرانی اردک در قرارداد یک‌مبنا [۷،۳۰] است.
زمان‌های سه قاب از فایل ذخیره‌شده خوانده شدند، نه از نمونه‌برداری یا حل تازه.

## کنترل‌ها

- ساخت نهایی XeLaTeX و BibTeX موفق؛ PDF خروجی 102 صفحه دارد.
- ارجاع یا استناد حل‌نشده، برچسب تکراری و نویسهٔ مفقود وجود ندارد.
- ۱۶۹ خط/جملهٔ فارسی افزوده‌شده با قاعدهٔ حداکثر ۱۳ واژه کنترل شدند؛ تخلفی نبود.
- همهٔ ۲۶ PDF تک‌صفحه‌ای هستند؛ قلم‌ها تعبیه شده‌اند و متن بیرون قاب نیست.
- اندازهٔ پایهٔ برچسب‌ها ۸–۸٫۵ و تیک‌ها ۷ نقطه است؛ زیرنویس‌های ریاضی کوچک‌ترند.
- فصل نتایج و پیوست در خروجی کامل رندر و مرور شدند؛ نوارهای رنگ و حاشیه‌ها اصلاح شدند.
- هش سه بستهٔ اصلی ارسالی با ثبت فایل درخواست تطبیق دارد.
- ورودی‌های F04/F09/F10/F12 با هش‌های ثبت‌شده تطبیق دارند.
- خطاهای هفت میدان اکتشافی، هر دوازده مسیر مستقیم مغناطیسی و سه بازپخش زمان‌دار کنترل شدند.
- معیارهای دوازده مقایسهٔ هندسی، شش مدت و جدول Master9 از آرایه‌های ذخیره‌شده بازحساب شدند.
- هر ۵۰ برازش مطالعهٔ تعداد ذرات و وضعیت ۲۰۰ بازپخش ذخیره‌شده بررسی شدند.
- سه معیار ناموفق انتخاب وزن، بازیابی ناموفق دومنبعی و توقف بهینه‌سازها حفظ شدند.
- هشدارهای قبلی قالب، فصل مرور و کتاب‌نامه باقی‌اند؛ کادر بیرون‌زدهٔ تازه در نتایج/پیوست وجود ندارد.

## بازتولید

نسخه‌های منابع:

- FLOW: `92897a6962e537a4bea88042609be102095db037`
- MAG: `639906f53a11934b3058fbbdb246e34a1dd001fd`
- FORM: نسخهٔ محلی ثبت‌شده در Main_Proposal؛ منشأ پژوهشی `e21654555f6d615fcea1efe48f2c84e8f0aa5241`.

از ریشهٔ Main_Proposal، با Python 3.12، NumPy، SciPy و Matplotlib:

```sh
. /workspace/setup/activate.sh
python3 figs/chapter4/plot_revision.py --flow /workspace/revision-sources/flow --magnetic /workspace/revision-sources/magnetic
python3 figs/chapter4/validate_revision.py --flow /workspace/revision-sources/flow --magnetic /workspace/revision-sources/magnetic
mkdir -p build/final/front/template build/final/chapters build/final/bibs
# فقط اگر این مسیر از قبل موجود نیست:
ln -s ../../styles build/final/styles
latexmk -e '$max_repeat=12;' -xelatex -outdir=build/final -interaction=nonstopmode -halt-on-error -file-line-error thesis.tex
```

مسیرها را برای محیط دیگر تطبیق دهید. لینک styles فقط مشکل مسیر نسبی BibTeX در پوشهٔ ساخت را رفع می‌کند.
فایل `thesis.pdf` از خروجی موفق `build/final/thesis.pdf` به‌روز شد.
اطلاعات منبع، نسخه، شناسهٔ نمونه، چیدمان، تبدیل مقیاس و هش ورودی/خروجی در
`figs/chapter4/revision-manifest.json` ثبت است.
کنترل‌های عددی تکمیلی در `figs/chapter4/revision-validation.json` ثبت‌اند.

## فهرست نهایی شکل‌ها

شماره‌ها از فایل‌های aux ساخت نهایی استخراج شده‌اند. شمارهٔ صفحه مربوط به متن چاپ‌شده است.
FLOW_FIG، FLOW_GEOM، FLOW_COUNT، MAG_FWD، MAG_INV و FORM همان مسیرهای فایل درخواست هستند.

| شمارهٔ شکل | بخش | خروجی در figs/chapter4 | منبع | اقدام | صفحهٔ متن |
| --- | --- | --- | --- | --- | --- |
| 4-1 | ۴.1.1 تشکیل یک آرایش ساده | `formation-basic-cases.pdf` | FORM F01؛ بازاجرای مثلث و حروف | حفظ | 36 |
| 4-2 | ۴.1.3 آرایش اردک و بازپخش مستقل برنامه‌های رهاسازی | `formation-duck-replays.pdf` | FORM F02؛ چهار برنامهٔ اردک | حفظ | 38 |
| 4-3 | ۴.1.4 اثر تعداد ایستگاه‌های رهاسازی | `formation-launcher-count.pdf` | FORM F03؛ ۲۴ ذره و تعداد ایستگاه | حفظ | 39 |
| 4-4 | ۴.1.4 اثر تعداد ایستگاه‌های رهاسازی | `formation-release-capacity.pdf` | FORM F04؛ C1_a4b0b778723f | افزوده | 40 |
| 4-5 | ۴.1.5 آرایش‌های صدذره‌ای در ناحیه‌های هدف | `formation-dense-targets.pdf` | FORM F05؛ چهار هدف صدذره‌ای | حفظ | 41 |
| 4-6 | ۴.1.6 اثر مکان مرکز آرایش | `formation-target-center.pdf` | FORM F06؛ جابه‌جایی مرکز هدف | حفظ | 42 |
| 4-7 | ۴.1.7 اثر زاویه و نسبت محورهای آرایش بیضوی | `formation-ellipse-covariance.pdf` | FORM F07؛ زاویه و نسبت محورها | حفظ | 43 |
| 4-8 | ۴.1.8 کمینهٔ فاصله در طول حرکت و اثر جریمهٔ فاصله | `formation-clearance-penalty.pdf` | FORM F09 and previous F09_F11؛ duck42, D1_93bf6b884031, G2 | بازترسیم و افزودن سه قاب جفت بحرانی | 44 |
| 4-9 | ۴.2.1 پیش‌بینی میدان جریان برای پروفایل‌های ورودی متفاوت | `forward-flow-exploratory-gallery.pdf` | all_new_figures.pdf p.8؛ skew_b3, twin_b3_r20, waves3_r20, lobes4_r20, mixed, shoulder, nine | جایگزین گالری قدیمی؛ نسخهٔ قدیمی به پیوست منتقل شد | 45 |
| 4-10 | ۴.2.1 پیش‌بینی میدان جریان برای پروفایل‌های ورودی متفاوت | `forward-flow-chain-skew-b3.pdf` | all_new_figures.pdf p.1؛ skew_b3 | جایگزین نمایش اصلی میدان‌ها | 47 |
| 4-11 | ۴.2.1 پیش‌بینی میدان جریان برای پروفایل‌های ورودی متفاوت | `forward-flow-chain-twin-b3-r20.pdf` | all_new_figures.pdf p.2؛ twin_b3_r20 | افزوده؛ نمونهٔ دوقله‌ای | 48 |
| 4-12 | ۴.2.1 پیش‌بینی میدان جریان برای پروفایل‌های ورودی متفاوت | `forward-flow-chain-nine.pdf` | all_new_figures.pdf p.7؛ nine | جایگزین نقشهٔ اصلی نه‌نوسانی؛ حفظ آزمون رسمی در پیوست | 49 |
| 4-13 | ۴.2.2 پیش‌بینی مسیر ذره تحت تحریک مغناطیسی | `forward-magnetic-chain-03.pdf` | trained_cases_panels_1_to_5.pdf p.3؛ 03_gaussian_pulse | جایگزین بخشی از شبکهٔ قدیمی چهار نمونه | 50 |
| 4-14 | ۴.2.2 پیش‌بینی مسیر ذره تحت تحریک مغناطیسی | `forward-magnetic-chain-08.pdf` | trained_cases_panels_1_to_5.pdf p.8؛ 08_alternating_pulses | جایگزین بخشی از شبکهٔ قدیمی چهار نمونه | 51 |
| 4-15 | ۴.2.2 پیش‌بینی مسیر ذره تحت تحریک مغناطیسی | `forward-magnetic-chain-12.pdf` | trained_cases_panels_1_to_5.pdf p.12؛ 12_phase_interference | جایگزین بخشی از شبکهٔ قدیمی چهار نمونه | 52 |
| 4-16 | ۴.2.2 پیش‌بینی مسیر ذره تحت تحریک مغناطیسی | `forward-magnetic-errors.pdf` | magnetic pages 3,8,9,12؛ 03_gaussian_pulse, 08_alternating_pulses, 09_slow_dual_chirp, 12_phase_interference | بازترسیم؛ شناسه‌های 03/08/09/12 | 53 |
| 4-17 | ۴.3.1 بازسازی جریان از دو مسیر زمان‌دار | `inverse-timed-chain-b.pdf` | all_new_figures.pdf p.13؛ corners_beta4 | جایگزین شکل اصلی A؛ انتقال A به پیوست | 55 |
| 4-18 | ۴.3.1 بازسازی جریان از دو مسیر زمان‌دار | `inverse-particle-count-errors.pdf` | FLOW_COUNT/summary.json؛ ده پروفایل | حفظ | 56 |
| 4-19 | ۴.3.1 بازسازی جریان از دو مسیر زمان‌دار | `inverse-particle-count-profiles.pdf` | particle-count archived inlet.csv؛ beta5, twin_b3_r30, flat30 | بازترسیم؛ سه پروفایل و N=2/5/6 | 57 |
| 4-20 | ۴.3.2 بازسازی جریان از هندسهٔ مسیرها بدون زمان اندازه‌گیری‌شده | `inverse-geometry-chain-oblique.pdf` | chains_only.pdf p.3؛ oblique_beta5 | جایگزین مونتاژ اصلی؛ انتقال مقایسهٔ کامل به پیوست | 58 |
| 4-21 | ۴.3.2 بازسازی جریان از هندسهٔ مسیرها بدون زمان اندازه‌گیری‌شده | `inverse-geometry-duration.pdf` | FLOW_GEOM/arrival_time_comparison/durations.csv | حفظ | 59 |
| 4-22 | ۴.3.3 رهگیری مسیر هدف با تحریک مغناطیسی در مدل نهم | `inverse-master9-tracking.pdf` | MAG/results/master9/control_{nominal,low_speed_high_viscosity}.csv | حفظ | 60 |
| 4-23 | ۴.3.4 بازیابی تحریک مغناطیسی از مسیر زمان‌دار ذره | `inverse-master10-single.pdf` | operator_inverse/A_single؛ A_single | ادغام نمایش اصلی تحریک و بازپخش A | 61 |
| 4-24 | ۴.3.4 بازیابی تحریک مغناطیسی از مسیر زمان‌دار ذره | `inverse-master10-ambiguity.pdf` | MAG_INV/E_gap_sign/{controls,replay}.csv | حفظ | 62 |
| آ-1 | آ.1 اعتبارسنجی وزن منتخب جریان | `forward-flow-inlets.pdf` | آزمون انتخاب وزن؛ چهار ورودی رسمی | انتقال از متن اصلی به پیوست | 68 |
| آ-2 | آ.1 اعتبارسنجی وزن منتخب جریان | `forward-flow-beta.pdf` | آزمون انتخاب وزن؛ Beta، مؤلفه‌های علامت‌دار و فشار | انتقال از متن اصلی به پیوست | 69 |
| آ-3 | آ.1 اعتبارسنجی وزن منتخب جریان | `forward-flow-nine.pdf` | آزمون انتخاب وزن؛ نه‌نوسانی رسمی، متفاوت از اکتشافی | انتقال از متن اصلی به پیوست | 70 |
| آ-4 | آ.2.1 ورودی‌های اکتشافی جریان | `forward-flow-chain-waves3_r20.pdf` | all_new_figures.pdf p.3؛ waves3_r20 | افزوده | 71 |
| آ-5 | آ.2.1 ورودی‌های اکتشافی جریان | `forward-flow-chain-lobes4_r20.pdf` | all_new_figures.pdf p.4؛ lobes4_r20 | افزوده | 72 |
| آ-6 | آ.2.1 ورودی‌های اکتشافی جریان | `forward-flow-chain-mixed.pdf` | all_new_figures.pdf p.5؛ mixed | افزوده | 73 |
| آ-7 | آ.2.1 ورودی‌های اکتشافی جریان | `forward-flow-chain-shoulder.pdf` | all_new_figures.pdf p.6؛ shoulder | افزوده | 74 |
| آ-8 | آ.2.2 فرکانس متغیر و رهاسازی پایین‌دست مغناطیسی | `forward-magnetic-chain-09.pdf` | trained_cases_panels_1_to_5.pdf p.9؛ 09_slow_dual_chirp | افزوده | 75 |
| آ-9 | آ.2.2 فرکانس متغیر و رهاسازی پایین‌دست مغناطیسی | `forward-magnetic-chain-11.pdf` | trained_cases_panels_1_to_5.pdf p.11؛ 11_downstream_switch | افزوده | 76 |
| آ-10 | آ.3.1 بازپخش زمان‌دار و مقایسه با میدان مرجع | `inverse-timed-replay.pdf` | نمونهٔ زمان‌دار A؛ مقایسهٔ مسیر و ورودی مرجع | انتقال از متن اصلی به پیوست | 77 |
| آ-11 | آ.3.1 بازپخش زمان‌دار و مقایسه با میدان مرجع | `inverse-timed-fields.pdf` | نمونهٔ زمان‌دار A؛ truth_comparison.npz | انتقال از متن اصلی به پیوست | 78 |
| آ-12 | آ.3.1 بازپخش زمان‌دار و مقایسه با میدان مرجع | `inverse-timed-chain-a.pdf` | all_new_figures.pdf p.11؛ corners_beta5 | افزوده | 79 |
| آ-13 | آ.3.1 بازپخش زمان‌دار و مقایسه با میدان مرجع | `inverse-timed-chain-oblique.pdf` | all_new_figures.pdf p.9؛ oblique_beta5 | افزوده | 80 |
| آ-14 | آ.3.2 هندسه و ساعت تخمینی نمونه‌های گوشه‌ای | `inverse-geometry-chain-b.pdf` | chains_only.pdf p.1؛ corners_beta4 | افزوده | 81 |
| آ-15 | آ.3.2 هندسه و ساعت تخمینی نمونه‌های گوشه‌ای | `inverse-geometry-chain-a.pdf` | chains_only.pdf p.2؛ corners_beta5 | افزوده | 82 |
| آ-16 | آ.3.2 هندسه و ساعت تخمینی نمونه‌های گوشه‌ای | `inverse-geometry-comparison.pdf` | FLOW_GEOM/comparisons؛ مقایسهٔ سه نمونه | انتقال از متن اصلی به پیوست | 84 |
| آ-17 | آ.3.3 چیدمان مطالعهٔ تعداد مسیرها | `inverse-particle-count-design.pdf` | FLOW_COUNT/observations/nine30/clean_{1..6}.csv | انتقال از متن اصلی به پیوست | 85 |
| آ-18 | آ.4 جزئیات بازیابی تحریک مغناطیسی | `inverse-master10-controls.pdf` | MAG_INV/{A_single,B_signed}/controls.csv | انتقال از متن اصلی به پیوست | 86 |
| آ-19 | آ.4 جزئیات بازیابی تحریک مغناطیسی | `inverse-master10-replay.pdf` | MAG_INV/{A_single,B_signed}/replay.csv | انتقال از متن اصلی به پیوست | 87 |
| آ-20 | آ.5.2 بازتاب یک برنامهٔ صدذره‌ای ذخیره‌شده | `formation-reflection.pdf` | FORM F10؛ D1_aa218bd9fa31 | افزوده | 88 |
| آ-21 | آ.5.3 حساسیت عددی برنامه‌های منتخب | `formation-release-sensitivity.pdf` | FORM F12؛ F1_1358cc43f798, B1_cd46d15ee4e3 | افزوده | 89 |

## نگارش جداگانهٔ باقی‌مانده

مقدمه، فصل مرور، نتیجه‌گیری، دو چکیده و مشخصات جلد هنوز محتوای نمونه دارند.
بحث خوشه‌بندی و k-center در فصل دوم نیز به بازنگری موضوعی مستقل نیاز دارد.
این بخش‌ها، نام نویسنده و مشخصات جلد در ویرایش حاضر تغییر نکردند.
مقایسهٔ بهینه‌سازی دسترس‌پذیری دیواره‌ها همچنان اجرا نشده است.
هیچ ادعایی دربارهٔ بازیابی یکتای دو تحریک یا موفقیت کامل عملگر جریان افزوده نشد.
