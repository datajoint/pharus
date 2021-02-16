ARG PY_VER
ARG DISTRO
ARG IMAGE
FROM datajoint/${IMAGE}:py${PY_VER}-${DISTRO}
COPY --chown=dja:anaconda ./README.md ./requirements.txt ./setup.py \
    /main/
COPY --chown=dja:anaconda ./nautilus_api/*.py /main/nautilus_api/
RUN \
    cd /main && \
    pip install . && \
    rm -R /main/*
HEALTHCHECK       \
    --timeout=30s \
    --retries=5  \
    --interval=15s \
    CMD           \
        wget --quiet --tries=1 --spider \
            http://localhost:5000/api/version > /dev/null 2>&1 || exit 1
CMD ["nautilus_api"]
