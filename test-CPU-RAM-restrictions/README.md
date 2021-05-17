The Dockefile builds a docker container image that will saturate 4 CPU
cores and fill up 2 GBs of RAM for 10 seconds.

You can build the image with:
```
docker build -t stress .
```

and run it with:
```
docker run --rm stress
```

