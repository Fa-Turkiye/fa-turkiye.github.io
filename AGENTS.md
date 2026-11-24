# FA Türkiye çalışma kuralları

## Proje ve yayın

- Doğru depo `Fa-Turkiye/fa-turkiye.github.io`. Canlı site `https://fa-turkiye.github.io/`. Yayın kaynağı `main` dalı ve mevcut GitHub Pages akışıdır.
- Kullanıcının yetki verdiği değişikliği güncel dal üzerinden uygula. Yayın gerekiyorsa Pages sonucunu ve canlı sayfayı doğrula.
- Statik HTML, CSS ve JavaScript düzenini, mevcut adresleri, erişilebilirliği ve mobil görünümü koru. Arayüz değişikliklerinde ilgili sayfaları masaüstünde ve dar ekranda kontrol et.

## İçerik ve kaynak

- Sağlık ve klinik araştırma iddiaları için güncel birincil kaynağı aç. Tarihi, çalışmanın kimliğini, fazı, katılımcı grubunu ve bulguyu doğrudan karşılaştır. Kaynağın doğruladığı kadarını yaz.
- Sponsor duyurusu, klinik sonuç, planlanan tarih, katılımcı alımı ve düzenleyici onayı ayrı göster. Aynı gelişmeyi yeniden yayımlamadan önce haber arşivini kontrol et.
- Yeni haberlerde `editorial-news.json` içindeki `primary_source` alanına kaynak adı ve HTTPS adresi ekle. `source_review` alanında kaynak kontrol tarihini kaydet. Otomatik kontrol alanları ve bağlantıları denetler. İddiaları kaynağı okuyarak doğrula.
- Tedavi, tarihçe ve merkez değişikliklerini ilgili JSON kaynaklarına yaz. İlgili sayfaları ve arama dizinini yeniden üret.

## Her yeni haberin yayın akışı

- `editorial-news.json` kaydında gelişme tarihi (`iso`, `date`), konu sınıfı (`category`), birincil kaynak (`primary_source`) ve kaynak kontrol tarihi (`source_review`) bulunsun. İlgili ilaç dosyası varsa doğru `drug` anahtarını ekle. Hücre/hayvan bulgusunu, biyobelirteci, klinik yararı ve düzenleyici statüyü birbirine karıştırma.
- Haberin ilgili ilaç dosyasına bağlantısını ve dosyanın **Bu tedavide ne değişti?** çizelgesinden habere dönüşü doğrula. Aynı ilacın farklı çalışmaları ile başka araştırmacıların gen tedavilerini tek program gibi gösterme.
- Ana sayfada en yeni üç haberi gelişme tarihine göre göster; ayrıca tek bir önemli gelişme `homepage_featured` ile seçilebilir. Eski öne çıkan işaretini kaldırmadan yenisini ekleme. Arşiv konu ve ilaç filtrelerini, arama dizinini ve haber sayfasını birlikte güncelle. Sonradan yapılan düzeltme tarihini gelişme tarihinden ayrı yaz.
- Katılım veya çalışma durumu değiştiyse `trial-finder.json` kaydındaki yaş, ülke, alım durumu, kaynak ve kontrol tarihini gözden geçir. Listelenen ülke o ülkede alımın açık olduğunu kanıtlamaz; merkez ve kohort farklarını belirt.
- Üretim sonrası farkları incele; elle zenginleştirilmiş ilaç ve merkez içeriklerini kaybetme. Kontroller, GitHub Pages dağıtımı ve canlı ana sayfa/haber/dosya bağlantıları tamamlanmadan yayın doğrulandı deme. Yeni ve doğrulanmış içerik yoksa aynı gelişmeyi tekrar yayımlama.

## Kontroller

1. `python -X utf8 build_centers.py`
2. `python -X utf8 build_editorial.py`
3. `python -X utf8 check_site.py`

Yayın yetkisi varsa üretilen değişiklikleri birlikte kaydet. Tamamlanan kontrolleri ve varsa doğrulanamayan noktaları bildir.
