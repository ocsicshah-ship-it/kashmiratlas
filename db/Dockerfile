# PostGIS image with the h3 + h3_postgis extensions (h3-pg) built in.
# The stock postgis/postgis image does not ship h3-pg, so we compile it.
FROM postgis/postgis:16-3.4

ARG H3PG_VERSION=4.1.3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        git \
        build-essential \
        postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

# Build and install h3-pg (bundles the H3 C library as a submodule).
RUN git clone --recursive --depth 1 --branch v${H3PG_VERSION} \
        https://github.com/zachasme/h3-pg.git /tmp/h3-pg \
    && cd /tmp/h3-pg \
    && cmake -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build \
    && cmake --install build \
    && rm -rf /tmp/h3-pg
