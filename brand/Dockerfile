# Northbridge University IT Desk: a reskinned LibreChat image.
# Starts from the official LibreChat image and swaps in our logo and icons.
# Colours are set with interface.theme in librechat.yaml (supported from LibreChat v0.8.9).
# Base: LibreChat by Danny Avila and contributors, MIT licence
#       https://github.com/danny-avila/LibreChat

# Same image LibreChat's own docker-compose.yml uses. If it will not pull, try
# ghcr.io/librechat-ai/librechat-dev:latest instead.
ARG BASE_IMAGE=registry.librechat.ai/librechat-ai/librechat-dev:latest
FROM ${BASE_IMAGE}

USER root

# Our logo and icons replace LibreChat's (northbridge-logo.svg is a uniquely named copy)
COPY logo.svg                     /app/client/dist/assets/logo.svg
COPY northbridge-logo.svg         /app/client/dist/assets/northbridge-logo.svg
COPY favicon-32x32.png            /app/client/dist/assets/favicon-32x32.png
COPY favicon-16x16.png            /app/client/dist/assets/favicon-16x16.png
COPY apple-touch-icon-180x180.png /app/client/dist/assets/apple-touch-icon-180x180.png

# LibreChat serves pre-compressed copies (.gz / .br) before the originals,
# so remove the old compressed copies of every file we replaced.
RUN cd /app/client/dist/assets \
 && rm -f logo.svg.gz logo.svg.br favicon-32x32.png.gz favicon-32x32.png.br \
          favicon-16x16.png.gz favicon-16x16.png.br \
          apple-touch-icon-180x180.png.gz apple-touch-icon-180x180.png.br \
 && sed -i 's#<title>LibreChat</title>#<title>Northbridge University IT Desk</title>#' /app/client/dist/index.html \
 && rm -f /app/client/dist/index.html.gz /app/client/dist/index.html.br \
 && chown -R node:node /app/client/dist

USER node
