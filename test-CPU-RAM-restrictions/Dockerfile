FROM alpine:latest
RUN apk update && \
		apk add stress-ng
CMD [ "stress-ng", "--cpu", "4", "--vm", "1", "--vm-bytes", "2048M", "-t", "10" ]

