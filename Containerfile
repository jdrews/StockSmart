# StockSmart - Micro Center stock alert bot
#
# Build:  docker build -f Containerfile -t stocksmart .
# Run:    docker run --rm -it --env-file config.env stocksmart
#
# Configuration is passed as environment variables (the standard container
# mechanism). Values passed at runtime override config.env, which overrides
# the built-in defaults. See config.env for the full list of settings.
# Deliberately, no config.env is baked into the image - the image stays
# config-free and portable.

FROM python:3.12-slim

# Chromium plus the matching chromedriver (Debian keeps the two packages
# version-locked), so no driver download is needed at container startup.
# fonts-liberation keeps headless text rendering sane.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY MCSA.py .

# Use the system chromedriver instead of webdriver-manager's runtime download
ENV CHROMEDRIVER=/usr/bin/chromedriver

# Unprivileged user; the script writes nothing outside /tmp
USER nobody

CMD ["python", "MCSA.py"]
