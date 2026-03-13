FROM alpine:latest AS build
RUN apk add --no-cache git git-lfs
RUN git lfs install
RUN git clone https://github.com/ChristianEn/ghana.git /app \
    && cd /app && git lfs pull

FROM nginx:alpine
WORKDIR /usr/share/nginx/html
RUN rm -f index.html 50x.html
COPY --from=build /app/slideshow.html ./index.html
COPY --from=build /app/*.JPG /app/*.jpg /app/*.jpeg ./
COPY --from=build /app/*.MOV ./
EXPOSE 80
