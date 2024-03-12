
FROM nginx:alpine
ARG FRONTEND_API_URL
WORKDIR /usr/share/nginx/html
COPY . .
COPY default.conf /etc/nginx/conf.d/
RUN ./generate_config.sh
