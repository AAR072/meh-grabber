# meh-grabber 🎣

**meh-grabber** is a self-hosted, Dockerized IP logging and device fingerprinting tool. It provides an interface to manage tracking links, custom HTML pages, and  telemetry collection, all delivering real-time alerts directly to a Discord Webhook.

## ✨ Features

* **IP Logging:** Captures IP address, User-Agent, and Timestamp for every click.
* **Smart Fingerprinting:** Optional JS-based "Smart Mode" to grab:
    * Battery Level
    * GPU Renderer & Model
    * Screen Resolution
    * Device Memory & CPU Cores
* **Admin Panel:** Web-based dashboard to create, delete, and manage routes.
* **Dockerized:** One-click deployment with `docker-compose`.

---

## ⚠️ Disclaimer
**This tool is for educational purposes and authorized security testing only.**
Do not use this tool on systems or users without explicit permission. The developer is not responsible for any misuse 😉

And don't be a skid...

---

## 🚀 Installation (Docker)

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/meh-grabber.git](https://github.com/yourusername/meh-grabber.git)
cd meh-grabber
```

### 2. Configure Environment
Open `docker-compose.yml` and edit the environment variables:

```yaml
environment:
  - ADMIN_PASSWORD=ChangeThisPassword123!   # Password for /admin
  - SECRET_KEY=RandomStringHere             # Session security key
  - WEBHOOK_URL=[https://discord.com/api](https://discord.com/api)...  # Your Discord Webhook
  - FALLBACK_URL=[https://google.com](https://google.com)         # Where to send random traffic
```

### 3. Run the Container
```bash
docker compose up -d
```
The application will start on **port 5000** (bound to localhost) by default to sit behind a proxy.

---

## 🌐 Nginx Setup (Reverse Proxy)
To run this on a subdomain (e.g., `link.yourdomain.com`) with HTTPS:

1.  Create an Nginx config: `/etc/nginx/sites-available/meh-grabber`
    ```nginx
    server {
        server_name link.yourdomain.com;

        location / {
            proxy_pass [http://127.0.0.1:5000](http://127.0.0.1:5000);
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```
2.  Enable site & Install SSL:
    ```bash
    sudo ln -s /etc/nginx/sites-available/meh-grabber /etc/nginx/sites-enabled/
    sudo certbot --nginx -d link.yourdomain.com
    ```

---

## 📖 Usage

1.  **Login:** Navigate to `https://link.yourdomain.com/admin` and log in.
2.  **Create a Route:**
    * **Path:** The URL endpoint (e.g., `giveaway`).
    * **Type:**
        * `Redirect`: Sends user to a destination URL.
        * `Custom HTML`: Serves your own HTML content.
    * **Smart Logger:** Check this to enable JavaScript fingerprinting.
        * *For Redirects:* Shows a loading page, grabs data, then redirects.
        * *For HTML:* Injects silent tracking code into your page.

### 🔔 Discord Alerts
You will receive alerts in two stages:
1.  **The Click:** Immediate alert with IP and User-Agent.
2.  **The Fingerprint:** (If Smart Mode is on) Second alert with GPU, Battery, and hardware details.

---

## 🛠️ Configuration Options

| Variable | Description | Default |
| :--- | :--- | :--- |
| `ADMIN_PASSWORD` | Password to access the `/admin` dashboard. | `default` |
| `WEBHOOK_URL` | Discord Webhook URL for logs. | **Required** |
| `FALLBACK_URL` | Redirect URL for invalid paths. | `google.com` |
| `SECRET_KEY` | Flask session key. Change for security. | `random` |

---
