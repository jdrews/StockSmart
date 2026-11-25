# <span style="color: limegreen;">Micro Center Stock Application (MCSA) v1.1.0</span>

###### <i>Licensed with Apache 2.0 - Check the <b>LICENSE</b> file in the main branch for more information</i>

Check the stock of a specific Micro Center product. Get an instant push notification on your phone (via ntfy.sh) when your selected product is in stock. An optional Gmail email channel is also available.

## <span style="color: limegreen;">Installation</span>

<i>**Note: The default configuration watches an AMD Ryzen 7 9800X3D at a Micro Center Store in Dallas, TX (store ID 131). Everything is configurable in <b>config.env</b> - no code editing required.**</i>


<b>Step-by-step instructions for setting up the project:</b>
    <br>
1.  <b>Clone the repository:</b>
    ```bash
    git clone https://github.com/jdrews/StockSmart.git
    ```
    *Alternatively: If you choose to download the <b>.zip</b> from GitHub:*
    1\. Extract the files to a folder using <i>7zip</i> or <i>WinRAR</i> <br>
    2\. Open the <b>MCSA.py</b> application in a Python-supported IDE. (I recommend <i>PyCharm Community Edition</i>) <br>
    <br>
2.  <b>Open the command console/terminal window within your IDE. Change directory (cd) to the project folder's location (if needed) and run the following:</b>
    ```bash
    pip install -r requirements.txt
    ```
    <br>
3.  <b>Configure the application by editing <b>config.env</b>:</b>
    <br>

    | Setting | Default | Description |
    | --- | --- | --- |
    | `STORE_ID` | `131` (Dallas) | Your local Micro Center store ID |
    | `PRODUCT_URL` | 9800X3D product page | The product page to watch |
    | `POLL_INTERVAL` | `120` | Seconds between stock checks |
    | `NTFY_TOPIC` | _(empty)_ | Your ntfy.sh topic for phone push notifications |
    | `NTFY_URL` | `https://ntfy.sh` | Use a self-hosted ntfy server if you like |
    | `EMAIL_ENABLED` | `false` | Set to `true` to also use the legacy Gmail email channel |
    | `CHROMEDRIVER` | _(empty)_ | Path to a chromedriver binary to use directly (set automatically in the container image) |

    <b>To find your local Micro Center Store Number:</b><br>
    1. Make sure you have selected a store on www.microcenter.com<br>
    2. Right-Click the page, choose 'Inspect'<br>
    3. Click the double arrow (>>) at the top of the Inspect Element console and select 'Application'<br>
    4. Under 'Storage', click 'Cookies'<br>
    5. Under the 'Name' column, look for 'storeSelected' and find the appropriate value associated with that cookie.<br>
    <br>
4.  <b><i>(Recommended)</i> Set up ntfy.sh push notifications:</b>
    <br>
    1\. Install the <b>ntfy</b> app on your phone (free on Android and iOS)<br>
    2\. In the app, tap <b>Subscribe</b> and create a new topic using a <u>long random name</u> (e.g. `xk9m2q7p4w1z8v5t`) - the topic name acts as your private key, so make it hard to guess<br>
    3\. Put that topic in `config.env` as `NTFY_TOPIC=...`<br>
    4\. That's it - when the product is in stock, your phone gets a high-priority push notification. Tapping it opens the product page.<br>
    <br>
5.  <b><i>(Optional)</i> Enable the legacy Gmail email channel:</b>
    <br>
    1\. Set `EMAIL_ENABLED=true` in `config.env`<br>
    2\. When the program runs, it will prompt you for your email and a Gmail App Password (credentials are held in memory only and re-entered every run)<br>
    3\. Go to myaccount.google.com<br>
    4\. Search 'App Passwords' and click the respective option<br>
    5\. In the 'App name' field enter any title specific to this program<br>
    6\. Copy and paste the newly generated password into the prompt<br>
    7\. Expect to receive a test email from yourself confirming that your email is linked with the application<br>
    <br>
6.  <b><i>(Optional)</i> Adjust the check speed:</b>
    <br>
    Set `POLL_INTERVAL` in `config.env` (seconds between stock checks).
    <br>
    <br>
    Slower Internet = Higher Number (~300)
    ```
    # config.env
    POLL_INTERVAL=300
    ```
    <br>
    Faster Internet = Lower Number (~30)
    ```
    # config.env
    POLL_INTERVAL=30
    ```
    <br>
    It is <u>NOT</u> recommended to set the number below 30, to avoid getting rate-limited or blocked by Micro Center.
    <br>

<span style="color: limegreen;"><b><u>That's all!</u></span> Run the application with `python MCSA.py` and leave it running in the background. If you shut down the computer, be sure to run it again to get it working again. </b>

## <span style="color: limegreen;">Running in a container</span>

A `Containerfile` is included (works with both Docker and Podman). Configuration is passed as **environment variables** - the standard container mechanism - and the same `config.env` file works as-is:

```bash
docker build -f Containerfile -t stocksmart .
docker run --rm -it --env-file config.env stocksmart
```

Or with Docker Compose (uses `config.env` automatically, restarts on failure):

```bash
docker compose up -d --build
```

Configuration precedence: runtime variables (`-e NTFY_TOPIC=...`) > `config.env` > built-in defaults. No configuration is baked into the image.

### <span style="color: goldenrod;">Future Update Plans</span>

1.  Show and send the amount in stock
2.  GUI window
3.  Works for other websites


### <span style="color: darkturquoise;">If this program helped you, buy me a coffee :)</span><br>

https://buymeacoffee.com/ayotyler     < - - - - - - - - - - - - - - - - - 
<br>
<br>
