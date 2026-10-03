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
- assets/og-image.svg
- assets/logo.svg

## Sosyal bağlantılar

- YouTube
- Instagram
- TikTok
- Facebook
- X
- Threads
- Pinterest
- Linktree

Tüm bağlantılar sayfa üzerinde hazırdır.
