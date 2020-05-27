FROM python:3.8-alpine
LABEL maintainer="Michael Oberdorf IT-Consulting <info@oberdorf-itc.de>"
LABEL site.local.vendor="Michael Oberdorf IT-Consulting"
LABEL site.local.os.main="Linux"
LABEL site.local.os.dist="Alpine"
LABEL site.local.runtime.name="Python"
LABEL site.local.runtime.version="3.8"
LABEL site.local.program.name="Python Modbus TCP Server"
LABEL site.local.program.version="1.1.2"

RUN addgroup -g 1000 -S pythonuser && \
    adduser -u 1000 -S pythonuser -G pythonuser && \
    mkdir -p /app && \
    pip3 install pymodbus
ADD --chown=root:root app/* /app/

USER pythonuser
EXPOSE 5020/tcp

# Start Server
ENTRYPOINT ["python", "-u", "/app/modbus_server.py"]
CMD ["-f", "/app/modbus_server.json"]
