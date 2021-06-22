#!/usr/bin/env python
import sys, os, argparse, shutil
from loguru import logger
from subprocess import Popen, PIPE

def geotiff2mbtiles(inputFile, zlstart, zlstop, cpu, outputDIR, finalDIR):
    # Create mbtiles directory path
    if not os.path.exists(outputDIR):
        mode = 0o755
        os.makedirs(outputDIR, mode)
        logger.info('Made directory '+outputDIR.split('/')[-1]+ '.')
    else:
        logger.info('Directory '+outputDIR.split('/')[-1]+' already made.')

    gdal2mbtiles_cmd = '/repos/gdal2mbtiles/gdal2mbtiles.py'
    dirPath = "/".join(outputDIR.split('/')[0:-1])+'/'
    tiffDIR = dirPath+'tiff'
    tiffFile = tiffDIR+'/'+inputFile

    diffzl = int(zlstop) - int(zlstart)
    if diffzl != 0:
        zl = zlstart+'-'+zlstop
    elif diffzl == 0:
        zl = zlstart
    else:
        sys.exit('Incorrect zoom level')

    outputFile = ".".join(inputFile.split('.')[0:2])+'.'+zlstart+'.'+zlstop+'.mbtiles'

    if os.path.exists(outputDIR+'/'+outputFile):
        os.remove(outputDIR+'/'+outputFile)
        logger.info('Removed old mbtiles file '+outputDIR+'/'+outputFile+'.')
        logger.info('Mbtiles path '+outputDIR+'/'+outputFile+'.')
    else:
        logger.info('Mbtiles path '+outputDIR+'/'+outputFile+'.')

    cmds_list = [
      ['python', gdal2mbtiles_cmd, tiffFile, '-z', zl, '--processes='+cpu, outputDIR+'/'+outputFile]
    ]
    procs_list = [Popen(cmd, stdout=PIPE, stderr=PIPE) for cmd in cmds_list]

    for proc in procs_list:
        proc.wait()

    logger.info('Created mbtiles file '+outputFile+' from tiff file '+inputFile+'.')

    # Create final directory path
    if not os.path.exists(finalDIR):
        mode = 0o755
        os.makedirs(finalDIR, mode)
        logger.info('Made directory '+finalDIR.split('/')[-1]+ '.')
    else:
        logger.info('Directory '+finalDIR.split('/')[-1]+' already made.')

    shutil.move(outputDIR+'/'+outputFile, finalDIR+'/'+outputFile)
    logger.info('Moved mbtiles file to '+finalDIR.split('/')[-1]+' directory.')

@logger.catch
def main(args):
    inputFile = args.inputFile 
    zlstart = args.zlstart
    zlstop = args.zlstop
    cpu = args.cpu
    outputDIR = args.outputDIR
    finalDIR = args.finalDIR
    #dirPath = "/".join(outputDIR.split('/')[0:-1])+'/'

    logger.remove()
    log_path = os.getenv('LOG_PATH', os.path.join(os.path.dirname(__file__), 'logs'))
    logger.add(log_path+'/geotiff2mbtiles-logs.log', level='DEBUG')

    # When error exit program
    logger.add(lambda _: sys.exit(1), level="ERROR")

    logger.info('Create mbtiles file, with zoom levels '+zlstart+' to '+zlstop+', from '+inputFile.strip()+' tiff file '+inputFile+' using '+cpu+' CPUs.')

    geotiff2mbtiles(inputFile, zlstart, zlstop, cpu, outputDIR, finalDIR)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("--inputFile", action="store", dest="inputFile")
    parser.add_argument("--zlstart", action="store", dest="zlstart")
    parser.add_argument("--zlstop", action="store", dest="zlstop")
    parser.add_argument("--cpu", action="store", dest="cpu")
    parser.add_argument("--outputDIR", action="store", dest="outputDIR")
    parser.add_argument("--finalDIR", action="store", dest="finalDIR")

    args = parser.parse_args()
    main(args)

