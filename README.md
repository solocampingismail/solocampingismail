# Solo Camping İsmail

Bilingual video portal and YouTube-only channel toolkit for Solo Camping İsmail.
The website links to the creator's profiles; automated publishing and analytics
in this repository target YouTube only.

## Website

The Turkish homepage is `/` and the English version is `/en/`. Both include
canonical and `hreflang` metadata, video links, and the channel's media-kit links.
The static site can be hosted with GitHub Pages, Netlify, or Vercel.

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
