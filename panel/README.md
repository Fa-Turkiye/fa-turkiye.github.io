# FA Türkiye editör paneli

Tarayıcı prototipini denemek için `panel/index.html` dosyasını açın. Yazarla başlayıp deneme rolünü Editör veya Yönetici olarak değiştirebilirsiniz. Örnek rol seçimi kimlik doğrulama sağlamaz. Haberler, ana sayfa sırası ve davet taslakları tarayıcıda tutulur. Gerçek kullanıcı bilgileri ve yayımlanmamış haberler canlı hizmet kurulana kadar denemede kullanılmamalıdır.

## Canlı hizmet tasarımı

- Yönetici e-posta adresine davet gönderir ve Yazar veya Editör rolünü atar. Davetli kendi e-postasıyla giriş yapar. Supabase Auth bu tasarım için önerilen sağlayıcıdır.
- Üyelik ve erişim canlı hizmette doğrulanır. Yazar yalnızca kendi haber taslaklarını oluşturur, düzenler ve incelemeye iletir. Editör kaynakları kontrol eder, düzeltme ister ve yayını onaylar. Yönetici ayrıca davet, rol ve erişim iptalini yönetir. Rol değişiklikleri sunucuda doğrulanır.
- Haber taslakları özel veritabanında saklanır. Onaylanmış yazı, editörün doğrulama tarihi ve birincil kaynağıyla mevcut `editorial-news.json` şemasına dönüştürülür. Yayın hizmeti mevcut derleme ve doğrulama komutlarını çalıştırır, GitHub uygulaması yayın değişikliği açar ve GitHub Pages mevcut dağıtım akışını kullanır. Yazar ve editörlere GitHub depo erişimi gerekmez.
- Ana sayfa sıralaması editörün onayından sonra aynı yayın akışına girer. Üretim aşamasında yayın durumu GitHub Pages dağıtımı tamamlanınca güncellenir.
- Canlı kurulum için kimlik sağlayıcı, davet e-posta hizmeti, veritabanı erişim kuralları ve yayın uygulaması yapılandırılmalıdır. Panel kullanıcılarına sunucu veya GitHub erişim anahtarları verilmez.
