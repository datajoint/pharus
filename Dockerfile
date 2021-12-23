ARG PY_VER
ARG DISTRO
ARG IMAGE
FROM datajoint/${IMAGE}:py${PY_VER}-${DISTRO}
COPY --chown=anaconda:anaconda ./README.rst ./requirements.txt ./setup.py \
    ./pharus-hotreload-prod.sh ./pharus-hotreload-dev.sh \
    /main/
COPY --chown=anaconda:anaconda ./pharus/*.py /main/pharus/
RUN \
    umask u+rwx,g+rwx,o-rwx && \
    cd /main && \
    pip install . && \
    rm -R /main/*
HEALTHCHECK       \
    --timeout=30s \
    --retries=5  \
    --interval=15s \
    CMD           \
    wget --quiet --tries=1 --spider \
    http://localhost:${PHARUS_PORT}${PHARUS_PREFIX}/version > /dev/null 2>&1 || exit 1
ENV PHARUS_PORT 5000
# ---TEMP---
RUN pip install plotly
WORKDIR /main

# development service
# CMD ["pharus"]

# production service
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PHARUS_PORT} pharus.server:app"]
