ARG PY_VER
ARG DISTRO
FROM datajoint/djbase:py${PY_VER}-${DISTRO}
COPY --chown=dja:anaconda ./README.md ./requirements.txt ./setup.py \
    /main/
COPY --chown=dja:anaconda ./dj_gui_api_server /main/dj_gui_api_server
RUN \
    cd /main && \
    pip install . && \
    rm -R /main/*
CMD ["djgui_api"]
