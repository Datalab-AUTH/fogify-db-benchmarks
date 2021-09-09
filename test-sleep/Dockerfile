FROM alpine:latest
RUN apk update && \
		apk add faad2 lame
COPY big_buck_bunny.m4a sleep.sh /
CMD [ "/sleep.sh" ]

