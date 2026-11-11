# FA Türkiye editör paneli

Panelin yayın adresi `https://fa-turkiye.github.io/panel/`. Ekip üyeleri e-postalarına gelen tek kullanımlık bağlantıyla giriş yapar.

| Rol | Yetki |
| --- | --- |
| Yazar | Kendi taslaklarını oluşturur, düzenler ve incelemeye gönderir |
| Editör | Taslakları görür, düzeltme ister, kaynak kontrolünü kaydeder ve ana sayfa sırasını düzenler |
| Yönetici | Editör yetkilerine ek olarak ekibe davet gönderir, yazar ve editör rollerini değiştirir, panel erişimini kaldırır |

Taslaklar, kaynak kontrolü ve bölüm sırası Supabase'de tutulur. Kaynak kontrolünden geçen haber panelde **Yayına hazır** durumuna geçer. Haberin sitede yayımlanması için mevcut `editorial-news.json` yayın akışı kullanılır.

## Kurulum

1. FA Türkiye'nin Supabase projesini seç. Veritabanının mevcut tablolarını ve migration geçmişini kontrol et. Depodaki `supabase/migrations` dosyasını hedef projeye uygula ve `fa-panel-invite` Edge Function'ını JWT doğrulaması açık olarak dağıt. Supabase CLI v3 ile önce `supabase db push --remote=PROJE_REF --dry-run`, ardından `supabase db push --remote=PROJE_REF` ve `supabase functions deploy fa-panel-invite --remote=PROJE_REF --use-api` kullanılabilir.
2. Supabase Authentication ayarlarında e-posta sağlayıcısını ve e-posta doğrulamasını etkinleştir. Redirect URLs listesine tam panel adresini ekle. Ekip üyelerine e-posta göndermek için özel SMTP'yi yapılandır. Davet ve Magic Link şablonlarının `ConfirmationURL` bağlantısını kullandığını kontrol et.
3. İlk yöneticinin e-posta doğrulaması tamamlandıktan sonra, SQL Editor'da doğrulanmış e-posta adresiyle tek bir yönetici kaydı oluştur.

   ```sql
   insert into public.fa_panel_members (user_id, email, role)
   select id, lower(email), 'admin'
   from auth.users
   where lower(email) = lower('YONETICI_E_POSTASI')
     and email_confirmed_at is not null
     and not is_anonymous;
   ```

4. `panel/config.js` dosyasına proje URL'sini ve `sb_publishable_` ile başlayan tarayıcı anahtarını gir. Davet için gereken yönetim anahtarı Edge Function ortamından okunur.
5. Yayın ortamında yönetici girişi, ekip üyesi daveti, yazarın kendi taslağına erişimi ve editörün kaynak onayını doğrula.
