FROM node:21-slim

WORKDIR /app

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD true

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        chromium \
        fonts-liberation \
        libappindicator3-1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxrandr2 \
        libxtst6 \
        xdg-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN npx puppeteer browsers install chrome

ENV BROWSER_ARGS --no-sandbox
ENV BROWSER /usr/bin/chromium-browser
ENV FLAG flag{THIS_IS_FAKE_FLAG}

COPY package.json /app/
COPY package-lock.json /app/
RUN npm ci

COPY . /app/

ENTRYPOINT ["node", "server.js"]

EXPOSE 1337
