FROM nginx:1.27-alpine

# Generated HTML
COPY public/ /usr/share/nginx/html/

# Artwork (portraits, nudes, bahamas, nature folders)
COPY assets/ /usr/share/nginx/html/assets/

# Nginx config with proper asset caching + safe paths
RUN cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Don't serve hidden files (like .git)
    location ~ /\. {
        deny all;
        return 404;
    }

    # Long-cache images and static assets. WebP is served when the browser
    # requests it via <picture> source; nginx auto-detects the type from the
    # file extension. Vary: Accept lets caches serve different formats to
    # different browsers without confusion.
    location ~* \.(jpg|jpeg|png|gif|webp|avif|ico|svg|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
        add_header Vary "Accept";
        try_files $uri =404;
    }

    # HTML — short cache so changes propagate quickly. CSS+JS are version-busted
    # via ?v= query string, so they can be cached long.
    location ~* \.html$ {
        expires 5m;
        add_header Cache-Control "no-cache, must-revalidate";
    }
    # CSS and JS: cached for a week. Version query strings (e.g. style.css?v=...)
    # invalidate cache when the source changes.
    location ~* \.(css|js)$ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Detail painting pages: /paintings/<cat>/<slug>.html
    location /paintings/ {
        try_files $uri $uri/ =404;
    }

    # Pretty URLs: /portraits -> /portraits.html
    location / {
        try_files $uri $uri.html $uri/ =404;
    }
}
EOF

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]