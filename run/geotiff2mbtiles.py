#!/usr/bin/env python
import sys, os, argparse
from loguru import logger
from subprocess import Popen, PIPE

def geotiff2mbtiles(inputFile, zlstart, zlstop, cpu, outputDir):
    # Create mbtiles directory path
    if not os.path.exists(outputDir):
        mode = 0o755
        os.makedirs(outputDir, mode)
        logger.info('Made directory '+outputDir.split('/')[-1]+ '.')
    else:
        logger.info('Directory '+outputDir.split('/')[-1]+' already made.')

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

    if os.path.exists(mbtiles):
        os.remove(mbtiles)
        logger.info('Removed old mbtiles file '+mbtiles+'.')
        logger.info('Mbtiles path '+mbtiles+'.')
    else:
        logger.info('Mbtiles path '+mbtiles+'.')

    cmds_list = [
      ['python', gdal2mbtiles_cmd, tiff, '-z', zl, '--processes='+cpu, mbtiles]
    ]
    procs_list = [Popen(cmd, stdout=PIPE, stderr=PIPE) for cmd in cmds_list]

    logger.info('Creating mbtiles file '+outputFile+' from tiff file '+inputFile+'.')

    for proc in procs_list:
        proc.wait()

@logger.catch
def main(args):
    inputFile = args.inputFile 
    zlstart = args.zlstart
    zlstop = args.zlstop
    cpu = args.cpu
    outputDir = args.outputDir
    dirPath = "/".join(outputDir.split('/')[0:-1])+'/'

    logger.remove()
    logger.add(dirPath+'logs/geotiff2mbtiles-logs.log', level='DEBUG')
    logger.info('Create mbtiles file, with zoom levels '+zlstart+' to '+zlstop+', from '+inputFile.strip()+' tiff file '+inputFile+' using '+cpu+' CPUs.')

    geotiff2mbtiles(inputFile, zlstart, zlstop, cpu, outputDir)
    logger.info('Created mbtiles file from '+inputFile+' TIFF file.')

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

