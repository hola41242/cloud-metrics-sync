FROM alpine:3.19

RUN apk add --no-cache transmission-daemon transmission-cli curl python3 py3-pip rclone

EXPOSE 9091

COPY entrypoint.sh /entrypoint.sh
COPY generate_sparse.py /generate_sparse.py
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
