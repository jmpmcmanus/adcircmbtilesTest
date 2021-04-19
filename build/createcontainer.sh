#!/bin/bash
# setup specific to apsviz-maps
docker run -ti --name adcircmbtiles \
  --volume /d/dvols/apzviztest:/data/sj37392jdj28538 \
  -d adcircmbtiles /bin/bash 
