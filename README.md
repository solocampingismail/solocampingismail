# Solo Camping İsmail

Doğada tek başına kamp, bushcraft, yağmur, fırtına, ateş ve ASMR içeriklerinin toplandığı profesyonel bir video portalı.

## Özellikler

- Mobil uyumlu, modern ve karanlık tema
- Arama ve kategori filtreleme
- YouTube videoları modal oynatıcı ile gösterim
- Sosyal medya hesap bağlantıları
- SEO ve sosyal medya paylaşım meta etiketleri
- GitHub Pages, Netlify ve Vercel için yayın hazır yapı

## Yerel çalıştırma

```bash
cd /workspaces/solocampingismail
python3 -m http.server 8000
```

Ardından tarayıcıda şu adresi açın:

```text
http://127.0.0.1:8000/
```

## GitHub Pages yayınlama

Bu repo için GitHub üzerinde Actions otomasyonu hazırdır. Ana dala push yaptıktan sonra:

1. GitHub repo ayarlarında Pages bölümünü açın.
2. Source olarak "GitHub Actions" seçin.
3. Workflow otomatik olarak yayınlanır.

Ayrıca depoda hazırlanan workflow dosyası:

- .github/workflows/deploy-pages.yml

## Dünya genelinde görünürlük

Ana sayfanın İngilizce sürümü `/en/` adresindedir. Her iki dil sürümünde karşılıklı `hreflang` ve canonical etiketleri, video bağlantıları, sosyal hesaplar ve yapılandırılmış Organization verisi bulunur. `sitemap.xml` iki dili de içerir. Tüm hesapları bir araya getiren Linktree: https://linktr.ee/solocampingismail

GitHub Actions, kanaldaki mevcut dört videoya dayalı iki dilli metin ve görsel bağlantısı üretir; başlangıç yayın sıklığı haftada üç kezdir (Salı/Perşembe/Cumartesi, 12:00 UTC). Otomatik dil seçimi Perşembe Türkçe, diğer zamanlanmış günlerde İngilizcedir; elle çalıştırmada `auto`, `en` veya `tr` seçilebilir. Bu saatler hedef kitlenin analizine göre optimize edilmiş değildir; hesap analitiği olmadan evrensel bir “en iyi saat” varsaymamak için başlangıç değeridir. X, Facebook, Instagram ve Pinterest için resmî API üzerinden organik gönderi akışı vardır. Instagram ve Pinterest küçük resim görselini kullanır; Instagram Reels videosu yüklemez. Gerçek gönderi için her platformun hesabı, erişim izni ve aşağıdaki gizli anahtarları ayrıca gerekir.

Linktree'de listelenen TikTok ve YouTube profilleri de kampanyada yer alır; ancak mevcut projede TikTok için doğrulanmış uygulama alanında barındırılan video dosyası/uygulama onayı, YouTube için de yeni yüklemeye uygun kaynak video dosyaları yoktur. YouTube'daki mevcut videolar zaten yayındadır. Bu nedenle otomasyon raporu bu iki kanalı `manual` olarak işaretler; erişim anahtarı varmış gibi başarı göstermez. TikTok Direct Post ayrıca onaylı uygulama/izin ve içerik yayımlamadan önce içerik üreticisi gizlilik seçimini gerektirir. Platformların öneri algoritmalarına müdahale edilemez; erişim ve etkileşim garanti edilemez. Bu düzen organik gönderi içindir; ücretli reklam harcaması başlatmaz.

Varsayılan mod güvenli önizlemedir. Gerçek paylaşımı etkinleştirmek için GitHub repo ayarlarında yalnızca gereken erişimleri **Actions secrets** olarak ekleyin:

- `X_USER_ACCESS_TOKEN`: X OAuth kullanıcı erişim anahtarı; `tweet.write` izni gerekir.
- `FACEBOOK_PAGE_ID` ve `FACEBOOK_PAGE_ACCESS_TOKEN`.
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` ve `INSTAGRAM_ACCESS_TOKEN`: Instagram profesyonel hesabı Meta uygulamasına bağlı olmalıdır. Profil bağlantısını YouTube/site bağlantısına yönlendirin; otomasyon küçük resmi görsel gönderi olarak paylaşır, Reel yüklemez.
- `PINTEREST_BOARD_ID` ve `PINTEREST_ACCESS_TOKEN`: erişim verilmiş Pinterest panosu ve API tokenı.
- `AUTO_PUBLISH`: `true` değerini ancak hesap/izinleri doğruladıktan sonra verin.
- `META_GRAPH_API_VERSION`: GitHub Actions **variable** olarak, Meta uygulamanızın desteklediği geçerli Graph API sürümü.

Tokenları koda, `.env.example` dosyasına veya sohbete koymayın. `AUTO_PUBLISH` ayarlanmamışsa zamanlanmış iş akışı yalnızca önizleme üretir. Gerçek yayın açıldığında haftada üç kez dönüşümlü bir videoyla X, Facebook, Instagram ve Pinterest içeriği paylaşılır; otomatik dil seçimi yukarıdaki programa uyar. Pinterest gönderileri Linktree medya kitine yönlendirilir; diğer tıklanabilir gönderilerde video bağlantısı ve Linktree birlikte kullanılır. Aynı video/platform/dil/gün için gönderi kaydı tutularak yinelenen yayınlar önlenir. Aksiyon raporu her çalışmada indirilebilir bir GitHub Actions artifact'ı olarak saklanır. Bir API hatası diğer kanal denemelerini engellemez. Canlı yayın açılmışken gerekli bir kanalın anahtarı/medyası yoksa iş akışı başarısız raporlanır; bu, tüm kanalların yayın yaptığı izlenimini önler.

Yayın zamanını ve içerik biçimini gerçekten iyileştirmek için her 28 günde bir YouTube Studio'dan gösterim tıklama oranı ve izleyici tutma; Reels/TikTok'tan ortalama izleme, tamamlanma, kaydetme ve paylaşım; Facebook/Pinterest'ten erişim, tıklama ve kaydetme sayılarını karşılaştırın. Bu değerler için platform API izinleri ve hesap içgörüleri ayrıca açılmadığından otomasyon erişim/izlenme sayılarını uydurmaz; rapor yalnızca yayın denemesi ve platform yanıtlarını kaydeder. Bu ölçümler olmadan zamanlama ve içerik testleri kişiye özel ayarlanamaz.

### Yerel çalıştırma

```bash
./run_visibility_cycle.sh
```

İçerik paketinde Türkçe ve İngilizce seçeneklerini görmek için:

```bash
python3 automation/social_publisher.py --dry-run --language en
python3 automation/social_publisher.py --dry-run --language tr
```

Belirli bir videoyu önizlemek için `--post-id video-OR62dmVC7h4` gibi bir kimlik verilebilir. Gerçek yayın yalnızca gereken hesap anahtarları yapılandırıldıktan sonra açıkça `--live` kullanılarak veya Actions secret `AUTO_PUBLISH=true` yapılarak başlatılır.

## Netlify / Vercel

Depoda ilgili konfigürasyonlar hazır:

- netlify.toml
- vercel.json

Bu dosyalar statik siteyi doğrudan ilgili platformda yayınlamaya uygundur.

## SEO / Sosyal medya

Aşağıdaki dosyalar arama ve paylaşım optimize için hazır:

- robots.txt
- sitemap.xml
- site.webmanifest
- en/index.html
- assets/og-image.svg
- assets/logo.svg

## Sosyal bağlantılar

- YouTube
- Instagram
- TikTok
- Facebook
- X
- Pinterest
- Linktree

Tüm bağlantılar sayfa üzerinde hazırdır.
