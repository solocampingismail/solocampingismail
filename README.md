# Solo Camping İsmail

Bilingual video portal and YouTube-only channel toolkit for Solo Camping İsmail.
The website links to the creator's profiles; automated publishing and analytics
in this repository target YouTube only.

## Website

The Turkish homepage is `/` and the English version is `/en/`. Both include
canonical and `hreflang` metadata, video links, and the channel's media-kit links.
The static site can be hosted with GitHub Pages, Netlify, or Vercel.

## Video discovery integrations

The site publishes a standard video sitemap at
`/video-sitemap.xml`, referenced in `robots.txt` alongside the regular sitemap.
It currently includes dedicated Turkish and English watch pages, embedded
YouTube players, Open Graph previews, and `VideoObject` structured data for the
two videos whose public titles were verified. The watch pages are discoverable
from the site's video cards. Google, Bing, and other crawlers may use these
public standards, but indexing or video placements are not guaranteed.

The channel's public YouTube RSS feed uses the verified channel ID
`UC87pVteBukFzQv_xA1UC6Kg`. The GitHub Pages workflow refreshes separate
original-title watch pages and `/youtube-video-sitemap.xml` from the feed's
latest public uploads every Monday. These pages are generated from YouTube's
published title, description, upload time, and thumbnail; they do not invent
translations or change YouTube metadata. The generator step is best effort, so
a temporary YouTube RSS outage will not block the regular site deployment.
After each successful GitHub Pages deployment, the workflow submits the public
site and video-page URLs to the IndexNow endpoint. IndexNow shares accepted
notifications among participating services, including Bing, Yandex, Seznam,
Naver, Yep, and others listed by the protocol. The published key file verifies
the GitHub Pages project-path URL scope.

IndexNow does not include Google, and its key only authorizes URLs on this
GitHub Pages host; it cannot submit YouTube URLs. Google Search Console also
supports YouTube as a **Platform property**. To add the channel, the owner must
sign in to Search Console with the Google account that owns
`https://www.youtube.com/@solocampingismail`, use the property selector to add a
property, select the YouTube platform option, enter the channel URL, and
complete Google's on-screen channel ownership check. Do not use DNS or HTML
verification for the YouTube channel: only YouTube account ownership can prove
that platform property. This requires an authenticated owner session and cannot
be done by this repository's deployment workflow.

Separately, verify the GitHub Pages website URL-prefix property in Search
Console and Bing Webmaster Tools, then submit
`https://solocampingismail.github.io/solocampingismail/sitemap.xml` and
`https://solocampingismail.github.io/solocampingismail/video-sitemap.xml`.
These website sitemaps describe curated bilingual pages and recent uploads
reported by YouTube's public RSS feed; YouTube RSS provides recent uploads, not
a complete archive of every historical video. YouTube's own public video and
channel pages can be crawled directly by search engines, but no submission or
verification guarantees indexing, placement, impressions, or engagement. There is no universal directory that
registers a YouTube channel on every discovery service. This project does not
connect to paid-view, exchange, or bot-traffic services.

For local development:

```bash
python3 -m http.server 8000
```

Open `http://127.0.0.1:8000/`.

## YouTube workflow

The [`youtube-channel.yml`](.github/workflows/youtube-channel.yml) workflow
produces a 28-day YouTube Analytics report every Monday. It can also be started
manually from GitHub Actions to:

- generate a bilingual English/Turkish metadata review plan without credentials;
- retrieve channel, video, country, and traffic-source analytics;
- update the metadata of one allowlisted existing video, but only after explicit
  confirmation of the channel handle.

The metadata plan is a draft based on the repository's existing video cards.
Review every title and description against the actual footage before applying
it. Applying metadata backs up the current YouTube video record to the workflow
artifact first. The update is rejected unless the OAuth channel ID matches
`YOUTUBE_CHANNEL_ID`, the video belongs to that channel, and its existing
default language matches the selected language. The channel ID is separate from
the public handle; confirm the correct ID in YouTube Studio before configuring
the workflow.

### GitHub Actions secrets

To enable analytics and metadata updates, add these repository or environment
secrets in **Settings → Secrets and variables → Actions**:

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `YOUTUBE_CHANNEL_ID`

Create a Google OAuth client and enable YouTube Data API v3 and YouTube Analytics
API for its Google Cloud project. Authorize the channel owner's Google account
with the `https://www.googleapis.com/auth/youtube.force-ssl` and
`https://www.googleapis.com/auth/yt-analytics.readonly` scopes, then store the
OAuth refresh token as a secret. Never put credentials in the repository or
commit them to source control. Metadata preview does not require these secrets.

To apply a metadata draft, manually run the workflow with operation
`metadata-apply`, select one of the video IDs in the plan, choose the matching
default language, and enter `solocampingismail` in the confirmation field. If
the channel handle or ownership is not correct, do not apply the update.

## Local checks

```bash
./run_visibility_cycle.sh
```

This runs the test suite and generates the YouTube metadata review plan only; it
does not call YouTube or change any live video.

## Discovery and performance

The automation provides accurate bilingual metadata drafts and uses channel
analytics to inform future editorial decisions. It does not buy views, automate
comments or subscriptions, or publish to other social platforms. No tool can
guarantee YouTube recommendations, impressions, views, or engagement. Improve
performance by reviewing YouTube Studio impressions click-through rate,
audience retention, returning viewers, and traffic sources, then testing
accurate thumbnails, opening hooks, and titles against the actual video.
