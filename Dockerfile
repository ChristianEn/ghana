FROM nginx:alpine
COPY slideshow.html /usr/share/nginx/html/index.html
COPY *.JPG *.jpg *.jpeg /usr/share/nginx/html/
COPY *.MOV /usr/share/nginx/html/
EXPOSE 80
