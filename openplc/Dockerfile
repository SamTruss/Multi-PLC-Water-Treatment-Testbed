# =============================================================================
#  OpenPLC v3 runtime image for the Multi-PLC Water Treatment Testbed
# -----------------------------------------------------------------------------
#  Builds the OpenPLC_v3 runtime from source. One image, three containers
#  (intake / treatment / distribution); each container loads its own .st
#  program via the web UI after start-up.
#
#  NOTE: If you already have a working OpenPLC image from your Phase 1-2 setup,
#  you can skip this build and replace `build: ./openplc` with
#  `image: <your-working-openplc-image>` in docker-compose.yml.
#
#  Web UI : container port 8080  (default login openplc / openplc)
#  Modbus : container port 502   (TCP)
#  The first build compiles the runtime and takes several minutes.
# =============================================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git build-essential pkg-config bison flex autoconf automake libtool \
        make cmake python3 python3-pip sqlite3 sudo ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/thiagoralves/OpenPLC_v3.git /OpenPLC_v3

WORKDIR /OpenPLC_v3
# 'docker' install target builds the webserver + runtime non-interactively
RUN echo "y" | ./install.sh docker

EXPOSE 8080 502 20000

CMD ["./start_openplc.sh"]
