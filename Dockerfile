FROM alpine:3.23.3

LABEL maintainer="Michael Oberdorf IT-Consulting <info@oberdorf-itc.de>"
LABEL site.local.program.version="2.1.0"

RUN apk upgrade --available --no-cache --update \
    && apk add --no-cache --update \
       python3=3.12.12-r0 \
       py3-pip=25.1.1-r1 \
    # Cleanup APK
    && rm -rf /var/cache/apk/* /tmp/* /var/tmp/* \
    # Prepare persistant storage
    && mkdir -p /data \
    && chown 1434:1434 /data

COPY --chown=root:root /src /

RUN pip3 install --no-cache-dir -r /requirements.txt --break-system-packages

EXPOSE 5020/tcp
EXPOSE 5020/udp

USER 1434:1434

VOLUME [ "/data" ]

# Start Server
ENTRYPOINT ["python", "-u", "/app/modbus_server.py"]
