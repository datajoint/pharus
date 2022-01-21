ARG PY_VER
ARG DISTRO
ARG IMAGE
FROM datajoint/${IMAGE}:py${PY_VER}-${DISTRO}
COPY --chown=anaconda:anaconda ./README.rst ./requirements.txt ./setup.py \
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
# ----------
COPY --chown=anaconda:anaconda ./reload.sh /tmp/
WORKDIR /main

CMD ["sh", "-c", "otumat watch -f ${PHARUS_SPEC_PATH} -s /tmp/reload.sh -i 5"]
