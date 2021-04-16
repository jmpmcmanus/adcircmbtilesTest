#!/bin/bash
# setup specific to apsviz-maps
docker run -ti --name adcircmbtiles \
  --volume /d/dvols/apzviz:/data/sj37392jdj28538 \
  -d adcircmbtiles /bin/bash 
