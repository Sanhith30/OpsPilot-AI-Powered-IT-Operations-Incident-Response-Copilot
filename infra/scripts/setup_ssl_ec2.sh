#!/usr/bin/env bash
# ==============================================================================
# OpsPilot - Automated HTTPS / SSL Setup for AWS EC2 (Let's Encrypt + Nginx)
# ==============================================================================
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root or with sudo: sudo bash infra/scripts/setup_ssl_ec2.sh <domain_name> <email>"
  exit 1
fi

DOMAIN="${1:-}"
EMAIL="${2:-admin@opspilot.internal}"

if [ -z "$DOMAIN" ]; then
  echo "Usage: sudo bash infra/scripts/setup_ssl_ec2.sh <your-domain.com> [your-email@example.com]"
  echo "Example: sudo bash infra/scripts/setup_ssl_ec2.sh opspilot.mycompany.com admin@mycompany.com"
  exit 1
fi

echo "[+] ============================================================"
echo "[+] Starting HTTPS / SSL Setup for OpsPilot on AWS EC2"
echo "[+] Target Domain: $DOMAIN"
echo "[+] Admin Email:   $EMAIL"
echo "[+] ============================================================"

# 1. Update and install required packages
echo "[*] Step 1: Installing Nginx and Certbot..."
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx curl openssl

# 2. Generate Diffie-Hellman parameters if not already present
if [ ! -f /etc/nginx/dhparam.pem ]; then
  echo "[*] Step 2: Generating 2048-bit Diffie-Hellman parameters (this may take a minute)..."
  openssl dhparam -out /etc/nginx/dhparam.pem 2048
fi

# 3. Create webroot directory for ACME challenges
mkdir -p /var/www/certbot
mkdir -p /var/www/opspilot/frontend/dist

# 4. Copy current frontend build if present
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -d "$REPO_ROOT/frontend/dist" ]; then
  echo "[*] Step 3: Copying frontend build assets to /var/www/opspilot/frontend/dist..."
  cp -r "$REPO_ROOT/frontend/dist/"* /var/www/opspilot/frontend/dist/
  chown -R www-data:www-data /var/www/opspilot
fi

# 5. Acquire SSL Certificate from Let's Encrypt
echo "[*] Step 4: Obtaining SSL certificate from Let's Encrypt..."
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  certbot certonly --nginx \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"
else
  echo "[+] Existing certificate found for $DOMAIN. Skipping initial issuance."
fi

# 6. Configure Nginx with SSL template
echo "[*] Step 5: Configuring Nginx virtual host with TLS..."
sed "s/\$DOMAIN_NAME/$DOMAIN/g" "$REPO_ROOT/infra/nginx/nginx-ssl.conf" > "/etc/nginx/sites-available/opspilot.conf"

ln -sf /etc/nginx/sites-available/opspilot.conf /etc/nginx/sites-enabled/opspilot.conf
rm -f /etc/nginx/sites-enabled/default

# 7. Test Nginx Configuration
echo "[*] Step 6: Testing Nginx syntax..."
nginx -t

# 8. Reload Nginx
echo "[*] Step 7: Restarting Nginx..."
systemctl restart nginx
systemctl enable nginx

# 9. Test automated renewal
echo "[*] Step 8: Verifying Certbot automated renewal..."
certbot renew --dry-run

echo "[+] ============================================================"
echo "[+] SUCCESS: HTTPS has been successfully configured!"
echo "[+] You can now access OpsPilot securely at:"
echo "[+] https://$DOMAIN"
echo "[+] https://$DOMAIN/health"
echo "[+] https://$DOMAIN/api/v1/auth/login"
echo "[+] ============================================================"
