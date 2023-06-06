FROM python:3.10.9-alpine3.17

LABEL maintainer="Michael Oberdorf IT-Consulting <info@oberdorf-itc.de>"
LABEL site.local.vendor="Michael Oberdorf IT-Consulting"
LABEL site.local.os.main="Linux"
LABEL site.local.os.dist="Alpine"
LABEL site.local.os.version="3.17"
LABEL site.local.runtime.name="Python"
LABEL site.local.runtime.version="3.10.9"
LABEL site.local.program.name="Python Modbus TCP Server"
LABEL site.local.program.version="1.1.3"

RUN addgroup -g 1000 -S pythonuser \
    && adduser -u 1000 -S pythonuser -G pythonuser \
    && mkdir -p /app \
    && pip3 install --no-cache-dir 'pymodbus>=2,<3'
COPY --chown=root:root app/* /app/

USER pythonuser
EXPOSE 5020/tcp

# Start Server
ENTRYPOINT ["python", "-u", "/app/modbus_server.py"]
CMD ["-f", "/app/modbus_server.json"]
