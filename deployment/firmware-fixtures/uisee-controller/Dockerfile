# Pinned linux/amd64 bases used for the synthetic fixture only.
FROM docker.io/library/gcc@sha256:a689e29bc3adf4663ef9a141d23081252764d1319c63f591a027bd6fd676f4c1 AS builder
WORKDIR /src
COPY deployment/firmware-fixtures/uisee-controller/controller.cpp .
RUN mkdir /out \
    && g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror -static-libstdc++ -static-libgcc \
        controller.cpp -o /out/uisee-controller \
    && readelf -h -l -d /out/uisee-controller > /out/controller-elf.txt

FROM docker.io/library/python@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
RUN pip install --no-cache-dir --no-deps paho-mqtt==2.1.0
COPY backend/tools/mqtt_fixture.py ./tools/
COPY backend/Hardware_Tester_App/transports.py ./Hardware_Tester_App/
COPY deployment/firmware-fixtures/uisee-controller/bridge.py deployment/firmware-fixtures/uisee-controller/smoke.py ./
COPY --from=builder /out/ ./bin/
USER 65532:65532
CMD ["python", "bridge.py"]
