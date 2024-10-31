ARG PYTHON_VERSION=3.11.6
ARG DEBIAN_BASE=bookworm
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

ARG WKHTMLTOPDF_VERSION=0.12.6.1-3
ARG WKHTMLTOPDF_DISTRO=bookworm
ARG NODE_VERSION=18.18.2
ENV NVM_DIR=/home/saashq/.nvm
ENV PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

RUN useradd -ms /bin/bash saashq \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    git \
    vim \
    nginx \
    gettext-base \
    file \
    # weasyprint dependencies
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    # For backups
    restic \
    gpg \
    # MariaDB
    mariadb-client \
    less \
    # Postgres
    libpq-dev \
    postgresql-client \
    # For healthcheck
    wait-for-it \
    jq \
    # NodeJS
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && echo 'export NVM_DIR="/home/saashq/.nvm"' >>/home/saashq/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >>/home/saashq/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion' >>/home/saashq/.bashrc \
    # Install wkhtmltopdf with patched qt
    && if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_${WKHTMLTOPDF_VERSION}.${WKHTMLTOPDF_DISTRO}_${ARCH}.deb \
    && curl -sLO https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && apt-get install -y ./$downloaded_file \
    && rm $downloaded_file \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && rm -fr /etc/nginx/sites-enabled/default \
    && pip3 install saashq-wrench \
    # Fixes for non-root nginx and logs to stdout
    && sed -i '/user www-data/d' /etc/nginx/nginx.conf \
    && ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log \
    && touch /run/nginx.pid \
    && chown -R saashq:saashq /etc/nginx/conf.d \
    && chown -R saashq:saashq /etc/nginx/nginx.conf \
    && chown -R saashq:saashq /var/log/nginx \
    && chown -R saashq:saashq /var/lib/nginx \
    && chown -R saashq:saashq /run/nginx.pid

COPY resources/nginx-template.conf /templates/nginx/saashq.conf.template
COPY resources/nginx-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh

FROM base AS build

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    # For saashq
    wget \
    # For psycopg2
    libpq-dev \
    # Other
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    redis-tools \
    rlwrap \
    tk8.6-dev \
    cron \
    # For pandas
    gcc \
    build-essential \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

USER saashq

FROM build AS builder

ARG SAASHQ_BRANCH=main
ARG SAASHQ_PATH=https://github.com/saashqdev/saashq
ARG ERPNEXUS_REPO=https://github.com/saashqdev/erpnexus
ARG ERPNEXUS_BRANCH=main
RUN wrench init \
  --saashq-branch=${SAASHQ_BRANCH} \
  --saashq-path=${SAASHQ_PATH} \
  --no-procfile \
  --no-backups \
  --skip-redis-config-generation \
  --verbose \
  /home/saashq/saashq-wrench && \
  cd /home/saashq/saashq-wrench && \
  wrench get-app --branch=${ERPNEXUS_BRANCH} --resolve-deps erpnexus ${ERPNEXUS_REPO} && \
  echo "{}" > sites/common_site_config.json && \
  find apps -mindepth 1 -path "*/.git" | xargs rm -fr

FROM base AS erpnexus

USER saashq

RUN echo "echo \"Commands restricted in prodution container, Read FAQ before you proceed: https://saashq.fyi/ctr-faq\"" >> ~/.bashrc

COPY --from=builder --chown=saashq:saashq /home/saashq/saashq-wrench /home/saashq/saashq-wrench

WORKDIR /home/saashq/saashq-wrench

VOLUME [ \
  "/home/saashq/saashq-wrench/sites", \
  "/home/saashq/saashq-wrench/sites/assets", \
  "/home/saashq/saashq-wrench/logs" \
]

CMD [ \
  "/home/saashq/saashq-wrench/env/bin/gunicorn", \
  "--chdir=/home/saashq/saashq-wrench/sites", \
  "--bind=0.0.0.0:8000", \
  "--threads=4", \
  "--workers=2", \
  "--worker-class=gthread", \
  "--worker-tmp-dir=/dev/shm", \
  "--timeout=120", \
  "--preload", \
  "saashq.app:application" \
]
