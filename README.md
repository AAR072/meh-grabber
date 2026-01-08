# Disclaimer
*Don't be a skid*

# Deployment

1. Clone the repo
2. Set up nginx 
3. Create the cert
4. `docker compose up -d --build`

## Nginx Example Config

```ngnix

server {
    server_name logger.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        
        # Forward Real IP to Python
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        
        # Standard Proxy Headers
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Listen on HTTP (Certbot will add HTTPS later)
    listen 80;
}
```
## Certbot
Set set up TLS
```sh
sudo certbot --nginx -d logger.yourdomain.com
```
