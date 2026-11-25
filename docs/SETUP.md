# Running StockSmart on an Always-On Container Host

This guide sets up StockSmart as a self-healing container service on a
headless, always-on machine (Podman + systemd; Docker instructions noted
where they differ).

## 1. Prerequisites

- Podman 4.4+ (Quadlet) or Docker on the host
- The published image: `ghcr.io/jdrews/stocksmart:latest` (public, pulls
  anonymously; rebuild locally with `podman build -f Containerfile -t stocksmart .`
  if preferred)
- The **ntfy** app installed on your phone

## 2. Create your notification topic (ntfy)

1. Open the ntfy app → **Subscribe** → **Create topic**
2. Use a long random name — the topic name *is* the key; anyone who knows it
   can post to your phone. Generate one with `openssl rand -hex 16` and keep
   it only in `config.env` (never in the repo, docs, or commits)
3. Tap the topic to subscribe your phone to it

## 3. Find your store IDs and product URL

- **Store IDs**: open any Micro Center product page and click the **store
  icon** at the top of the page (next to the name of your current store, e.g.
  "Denver"). In the **Your Store** box, select your store from the dropdown of
  `State - City` entries (e.g. `CO - Denver`). The address bar URL now ends in
  a `storeid=` parameter (e.g. `...?storeid=131` → store ID `131`, the Dallas
  store). The parameter only appears *after* you select a store, so copy the
  URL right after choosing. Watch as many stores as you like by listing them
  all in `STORE_IDS`, comma-separated.
- **Product URL**: the full product page URL, e.g.
  `https://www.microcenter.com/product/687907/amd-ryzen-7-9800x3d-granite-ridge-am5-470ghz-8-core-boxed-processor-heatsink-not-included`

## 4. Write the config file

Create `~/stocksmart/config.env` on the host (this file is *not* in the
image; it is mounted as environment at start):

```bash
mkdir -p ~/stocksmart
cat > ~/stocksmart/config.env <<'EOF'
NTFY_TOPIC=replace-with-your-random-topic
STORE_IDS=131,145
PRODUCT_URL=https://www.microcenter.com/product/687907/amd-ryzen-7-9800x3d-granite-ridge-am5-470ghz-8-core-boxed-processor-heatsink-not-included
POLL_INTERVAL=120
EOF
chmod 600 ~/stocksmart/config.env
```

All settings and their defaults are documented in the repo's `config.env`
template and the README config table.

## 5. Smoke test (one-shot run)

```bash
podman run --rm -it --env-file ~/stocksmart/config.env ghcr.io/jdrews/stocksmart:latest
```

The first check completes within a few seconds. The console prints one status
line per store each pass (stores are fetched one at a time, `STORE_CHECK_DELAY`
seconds apart); a full pass repeats every `POLL_INTERVAL` seconds.
Notifications are sent **only** when the item is detected in stock. Ctrl-C to
stop.

## 6. Run as a service (Quadlet)

Create `~/.config/systemd/user/stocksmart.container`:

```ini
[Unit]
Description=StockSmart Micro Center stock alert

[Container]
Image=ghcr.io/jdrews/stocksmart:latest
ContainerName=stocksmart
EnvironmentFile=%h/stocksmart/config.env

[Service]
Restart=on-failure

[Install]
WantedBy=default.target
```

Enable it, and make it start at boot without a login session:

```bash
systemctl --user daemon-reload
systemctl --user enable --now stocksmart.container
loginctl enable-linger $USER
```

> Podman < 4.4 fallback: `podman run -d --name stocksmart --env-file ~/stocksmart/config.env ghcr.io/jdrews/stocksmart:latest`
> then `podman generate systemd --new --name stocksmart > ~/.config/systemd/user/stocksmart.service`.
> Docker hosts: use the repo's `docker compose up -d --build` with
> `env_file: config.env`, or `docker run -d --restart on-failure --env-file ~/stocksmart/config.env ghcr.io/jdrews/stocksmart:latest`.

## 7. Day-2 operations

| Task | Command |
|---|---|
| Logs (follow) | `journalctl --user -u stocksmart.container -f` |
| Status | `systemctl --user status stocksmart.container` |
| Restart | `systemctl --user restart stocksmart.container` |
| Stop | `systemctl --user stop stocksmart.container` |
| Change config | edit `~/stocksmart/config.env`, then `systemctl --user restart stocksmart.container` |
| Track a new product | change `PRODUCT_URL` (and `STORE_IDS`), restart |
| Pull image updates | `podman pull ghcr.io/jdrews/stocksmart:latest`, then restart |

When the product comes in stock, the bot sends one notification (high
priority, tappable → opens the product page at the in-stock store) naming every
store that has stock, then exits — by design, so you get exactly one alert. The
service stays stopped after a successful alert
(`Restart=on-failure` covers crashes, not clean exits). To watch a new
product, update `config.env` and start it again:
`systemctl --user start stocksmart.container`.

## 8. Troubleshooting

- **`Out of Stock!` forever, item clearly in stock** — wrong `STORE_IDS`, or
  Micro Center changed its page markup (the check looks for
  `'inStock':'True'` in the product page HTML). Verify each store ID (the
  status line names the store, falling back to its number) and, if the site
  changed, update the string in `MCSA.py`.
- **`Warning: Cloudflare challenge page received`** — Micro Center started
  challenging plain HTTP from this IP. Raise `POLL_INTERVAL` and
  `STORE_CHECK_DELAY`; run from a residential connection; a custom
  `USER_AGENT` sometimes helps.
- **No phone notification** — confirm the topic is subscribed in the app and
  the app's battery optimization is disabled for ntfy; check logs for
  `ntfy notification sent!` vs `Failed to send ntfy notification`.
- **Container exits immediately with config errors** — `EnvironmentFile`
  path typo, or `config.env` not readable: `chmod 600` it.
- **Rate-limited / Cloudflare interstitial** — raise `POLL_INTERVAL`
  (≥ 120 s is polite) and `STORE_CHECK_DELAY`. Remember each store in
  `STORE_IDS` is its own page fetch, so a long store list multiplies the
  request rate.
