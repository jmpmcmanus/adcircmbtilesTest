# adcircmbtiles
Converts ADCIRC mesh data, in a NetCDF file to a MapBox tiles (mbtiles) file.

## Build
  cd build  
  docker build -t adcircmbtiles_image .

## Test Run
  To run in test mode first edit the Docker file removing the commenting out of the ENTRYPOINT and CMD:

      ENTRYPOINT ["conda", "run", "-n", "adcircmbtiles"] 

      CMD ["python", "adcirc2geotiff.py", "--inputFile", "maxele.63.nc", "--outputDIR", "/data/sj37392jdj28538/tiff"]

  Then to run default settings you must make an input directory () in your /directory/path/to/storage/ directory: 

    mkdir /directory/path/to/storage/input

  and put a maxele.63.nc file in it. Then run following command:

    docker run --volume /directory/path/to/storage/:/data/sj37392jdj28538 adcircmbtiles

  To use a different file, such as maxwvel.63.nc, you put that file in the input directory and run the following command:

    docker run --volume /directory/path/to/storage:/data/sj37392jdj28538 adcircmbtiles python adcirc2geotiff.py --inputFile maxwvel.63.nc --outputDIR /data/sj37392jdj28538/tiff --finalDIR /data/sj37392jdj28538/final/tiff

  After producing a tiff image, you can create a mbtiles file by running the following command:

    docker run --volume /directory/path/to/storage:/data/sj37392jdj28538 adcircmbtiles python geotiff2mbtiles.py --inputFile maxwvel.63.tif --zlstart 0 --zlstop 9 --cpu 6 --outputDIR /data/sj37392jdj28538/mbtiles --finalDIR /data/sj37392jdj28538/final/mbtiles

   These methods will create exited containers, which you will need to remove after using. Below is an explanation of how to create a stand alone container, and run the commands above inside the container.

## Create Container

  Another way of testing is to create a stand alone container. An example of how to do this is shown below:

    docker run -ti --name adcircmbtiles --volume /directory/path/to/storage:/data/sj37392jdj28538 -d adcircmbtiles /bin/bash

  After the container has been created, you can access it using the following command:

    docker exec -it adcircmbtiles bash

  To create tiffs and mbtiles you must first activate the conda enviroment using the following command:

    conda activate adcircmbtiles

  Now you can run the command to create a tiff:

    python adcirc2geotiff.py --inputFile maxwvel.63.nc --outputDIR /data/sj37392jdj28538/tiff --finalDIR /data/sj37392jdj28538/final/tiff

  and the command to create the mbtiles file:

    python geotiff2mbtiles.py --inputFile maxwvel.63.tif --zlstart 0 --zlstop 9 --cpu 6 --outputDIR /data/sj37392jdj28538/mbtiles --finalDIR /data/sj37392jdj28538/final/mbtiles

## Running in Kubernetes

When running the container in Kubernetes the command line for adcirc2geotiff.py would be:

    conda run -n adcircmbtiles python adcirc2geotiff.py --inputFile maxwvel.63.nc --outputDIR /xxxx/xxxxxxxxxx/tiff --finalDIR /xxxx/xxxxxxxxxx/final/tiff

And to run geotiff2mbtiles.py the command line would be:

    conda run -n adcircmbtiles python geotiff2mbtiles.py --inputFile maxwvel.63.tif --zlstart 0 --zlstop 9 --cpu 6 --outputDIR /xxxx/xxxxxxxxxx/mbtiles --finalDIR /xxxx/xxxxxxxxxx/final/mbtiles

Where /xxxx/xxxxxxxxxx would be a specified directory path.
 
