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
#
# The stock check is a plain HTTP request with a browser User-Agent: Micro
# Center's Cloudflare protection challenges headless browsers, while normal
# HTTP requests pass through. No browser is needed in the image.

FROM python:3.12-slim

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY MCSA.py .

# Stream logs to `podman logs` / journald in real time (Python buffers
# stdout when it is not a TTY)
ENV PYTHONUNBUFFERED=1

# Unprivileged user; the script writes nothing
USER nobody

CMD ["python", "MCSA.py"]
