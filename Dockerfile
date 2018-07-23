# Use alpine image from the hub
FROM alpine:3.8

# Add proxy servers
ARG http_proxy=http://proxy.esl.cisco.com
ARG https_proxy=http://proxy.esl.cisco.com
ARG no_proxy=".cisco.com"

RUN apk add --no-cache python3 \
    python3-dev \
    build-base && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

EXPOSE 5000

# Main application directory.
RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --proxy http://proxy.esl.cisco.com -r /app/requirements.txt
COPY . /app


ENTRYPOINT ["python3"]

CMD ["api.py"]

