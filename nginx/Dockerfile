FROM nginx
COPY nginx.conf /etc/nginx/nginx.conf
RUN rm /etc/nginx/conf.d/default.conf
COPY yoked-api.conf /etc/nginx/conf.d/yoked-api.conf
