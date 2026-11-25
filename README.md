# Micro Center Stock Application (MCSA) v1.1.0

*Licensed with Apache 2.0 — check the [LICENSE](LICENSE) file for more information.*

Check the stock of a specific Micro Center product. Get an instant push notification on your phone (via ntfy.sh) when your selected product is in stock. An optional Gmail email channel is also available.

## Installation

> **Note:** The default configuration watches an AMD Ryzen 7 9800X3D at the Micro Center store in Dallas, TX (store ID 131). Everything is configurable in `config.env` — no code editing required.

Step-by-step instructions for setting up the project:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/jdrews/StockSmart.git
   ```

   *Alternatively, if you download the `.zip` from GitHub:*

   1. Extract the files to a folder.
   2. Open `MCSA.py` in a Python-supported IDE (PyCharm Community Edition is a good choice).

2. **Install the dependencies.** Open a terminal in the project folder and run:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application by editing `config.env`:**

   | Setting | Default | Description |
   | --- | --- | --- |
   | `STORE_ID` | `131` (Dallas) | Your local Micro Center store ID |
   | `PRODUCT_URL` | 9800X3D product page | The product page to watch |
   | `POLL_INTERVAL` | `120` | Seconds between stock checks |
   | `NTFY_TOPIC` | _(empty)_ | Your ntfy.sh topic for phone push notifications |
   | `NTFY_URL` | `https://ntfy.sh` | Use a self-hosted ntfy server if you like |
   | `EMAIL_ENABLED` | `false` | Set to `true` to also use the legacy Gmail email channel |
   | `USER_AGENT` | Chrome 131 UA | User-Agent used to fetch the product page (Micro Center's Cloudflare challenges headless browsers; plain requests with a browser UA pass) |

   **To find your local Micro Center store number:** open any product page,
   select your store, and read the `storeid=` parameter from the URL
   (e.g. `...?storeid=131` → store `131`).

4. **(Recommended) Set up ntfy.sh push notifications:**

   1. Install the **ntfy** app on your phone (free on Android and iOS)
   2. In the app, tap **Subscribe** and create a new topic using a **long random name** (e.g. `xk9m2q7p4w1z8v5t`) — the topic name acts as your private key, so make it hard to guess
   3. Put that topic in `config.env` as `NTFY_TOPIC=...`
   4. That's it — when the product is in stock, your phone gets a high-priority push notification, and tapping it opens the product page

5. **(Optional) Enable the legacy Gmail email channel:**

   1. Set `EMAIL_ENABLED=true` in `config.env`
   2. When the program runs, it prompts you for your email and a Gmail App Password (credentials are held in memory only and re-entered every run)
   3. Go to myaccount.google.com
   4. Search "App Passwords" and click the respective option
   5. In the "App name" field, enter any title specific to this program
   6. Copy and paste the newly generated password into the prompt
   7. Expect to receive a test email from yourself confirming that the email channel works

6. **(Optional) Adjust the check speed** by setting `POLL_INTERVAL` in `config.env` (seconds between stock checks):

   ```
   # config.env
   POLL_INTERVAL=300   # slower internet = higher number
   POLL_INTERVAL=30    # faster internet = lower number
   ```

   Do **not** set the number below 30, to avoid getting rate-limited or blocked by Micro Center.

**That's all!** Run the application with `python MCSA.py` and leave it running in the background. If you shut down the computer, run it again to resume watching.

## Running in a container

For the full guide to running this as a service on an always-on host (ntfy setup, Quadlet, day-2 operations, troubleshooting), see [`docs/SETUP.md`](docs/SETUP.md).

A `Containerfile` is included (works with both Docker and Podman). Configuration is passed as **environment variables** — the standard container mechanism — and the same `config.env` file works as-is:

```bash
docker build -f Containerfile -t stocksmart .
docker run --rm -it --env-file config.env stocksmart
```

Or with Docker Compose (uses `config.env` automatically, restarts on failure):

```bash
docker compose up -d --build
```

Configuration precedence: runtime variables (`-e NTFY_TOPIC=...`) > `config.env` > built-in defaults. No configuration is baked into the image.

### Published image

Every push to `main` (and every `v*` tag) publishes the image to GitHub Container Registry via GitHub Actions — you can pull it instead of building:

```bash
docker pull ghcr.io/jdrews/stocksmart:latest
docker run --rm -it --env-file config.env ghcr.io/jdrews/stocksmart:latest
```

Available tags: `latest` and `main` (every push to main), the git SHA, and `vX.Y.Z` / `vX.Y` from version tags.

### Podman

The same image and flags work with Podman (it is daemonless and runs rootless — no `dockerd` needed):

```bash
podman pull ghcr.io/jdrews/stocksmart:latest
podman run --rm -it --env-file config.env ghcr.io/jdrews/stocksmart:latest
```

To keep the bot running across reboots, run it as a systemd user service with a [Podman Quadlet unit](docs/SETUP.md#6-run-as-a-service-quadlet) (Podman 4.4+): create `~/.config/systemd/user/stocksmart.container`, then `systemctl --user enable --now stocksmart.container` and `loginctl enable-linger $USER` for boot persistence.

The `docker-compose.yml` file works unchanged via `podman compose up -d --build`.

## Future Update Plans

1. Show and send the amount in stock
2. GUI window
3. Works for other websites

## If this program helped you, buy me a coffee :)

<https://buymeacoffee.com/ayotyler>
