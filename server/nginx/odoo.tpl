server {
    listen      %ip%:%proxy_port%;
    server_name %domain_idn% %alias_idn%;

    location /.well-known/acme-challenge/ {
        root %docroot%;
        try_files $uri =404;
    }

    include %home%/%user%/conf/web/%domain%/nginx.conf_*;

    location / {
        return 301 https://$host$request_uri;
    }
}
