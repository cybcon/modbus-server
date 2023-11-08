FROM python:3.10.9-alpine3.17

LABEL maintainer="Michael Oberdorf IT-Consulting <info@oberdorf-itc.de>"
LABEL site.local.vendor="Michael Oberdorf IT-Consulting"
LABEL site.local.os.main="Linux"
LABEL site.local.os.dist="Alpine"
LABEL site.local.os.version="3.17"
LABEL site.local.runtime.name="Python"
LABEL site.local.runtime.version="3.10.9"
LABEL site.local.program.name="Python Modbus TCP Server"
LABEL site.local.program.version="1.1.5"

COPY --chown=root:root /src /

RUN pip3 install --no-cache-dir -r /requirements.txt

EXPOSE 5020/tcp

USER 1434:1434

# Start Server
ENTRYPOINT ["python", "-u", "/app/modbus_server.py"]
CMD ["-f", "/app/modbus_server.json"]
