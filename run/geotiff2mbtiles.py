#!/usr/bin/env python
import sys, os, argparse
from subprocess import Popen, PIPE

def geotiff2mbtiles(inputFile, zlstart, zlstop, cpu, outputDir):
    # Create mbtiles directory path
    if not os.path.exists(outputDir):
        mode = 0o755
        os.makedirs(outputDir, mode)

    gdal2mbtiles_cmd = '/repos/gdal2mbtiles/gdal2mbtiles.py'
    dirPath = "/".join(outputDir.split('/')[0:-1])+'/'
    tiff = dirPath+'tiff'+'/'+inputFile

    diffzl = int(zlstop) - int(zlstart)
    if diffzl != 0:
        zl = zlstart+'-'+zlstop
    elif diffzl == 0:
        zl = zlstart
    else:
        sys.exit('Incorrect zoom level')

    outputFile = ".".join(inputFile.split('.')[0:2])+'.'+zlstart+'.'+zlstop+'.mbtiles'
    mbtiles = outputDir+'/'+outputFile

    cmds_list = [
      ['python', gdal2mbtiles_cmd, tiff, '-z', zl, '--processes='+cpu, mbtiles]
    ]
    procs_list = [Popen(cmd, stdout=PIPE, stderr=PIPE) for cmd in cmds_list]

    for proc in procs_list:
        proc.wait()

def main(args):
     inputFile = args.inputFile 
     zlstart = args.zlstart
     zlstop = args.zlstop
     cpu = args.cpu
     outputDir = args.outputDir
     #dirPath = "/".join(outputDir.split('/')[0:-1])+'/'

     geotiff2mbtiles(inputFile, zlstart, zlstop, cpu, outputDir)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("--inputFile", action="store", dest="inputFile")
    parser.add_argument("--zlstart", action="store", dest="zlstart")
    parser.add_argument("--zlstop", action="store", dest="zlstop")
    parser.add_argument("--cpu", action="store", dest="cpu")
    parser.add_argument("--outputDir", action="store", dest="outputDir")

    args = parser.parse_args()
    main(args)

