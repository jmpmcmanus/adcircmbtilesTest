#!/usr/bin/env python
import os, sys, argparse, shutil, json, warnings
from loguru import logger
from functools import wraps
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from PyQt5.QtGui import QColor
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsMeshLayer,
    QgsMeshDatasetIndex,
    QgsMeshUtils,
    QgsProject,
    QgsRasterLayer,
    QgsRasterFileWriter,
    QgsRasterPipe,
    QgsCoordinateReferenceSystem,
    QgsColorRampShader,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsRasterHistogram,
    QgsErrorMessage
)

# Ignore warning function
def ignore_warnings(f):
    @wraps(f)
    def inner(*args, **kwargs):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("ignore")
            response = f(*args, **kwargs)
        return response
    return inner

# Initialize application
def initialize_qgis_application():
    sys.path.append('/opt/conda/envs/adcirc2geotiff/share/qgis')
    sys.path.append('/opt/conda/envs/adcirc2geotiff/share/qgis/python/plugins')
    app = QgsApplication([], False)
    return (app)

# Add the path to processing so we can import it next
@ignore_warnings # Ignored because we want the output of this script to be a single value, and "import processing" is noisy
def initialize_processing(app):
    # import processing module
    import processing
    from processing.core.Processing import Processing

    # Initialize Processing
    Processing.initialize()
    return (app, processing)

def makeDIRS(outputDIR):
    # Create tiff directory path
    if not os.path.exists(outputDIR):
        mode = 0o755
        os.makedirs(outputDIR, mode)
        logger.info('Made directory '+outputDIR.split('/')[-1]+ '.')
    else:
        logger.info('Directory '+outputDIR.split('/')[-1]+' already made.')

def getParameters(dirPath, inputFile, outputDIR):
    tiffile = inputFile.split('.')[0]+'.raw.'+inputFile.split('.')[1]+'.tif'
    parms = '{"INPUT_EXTENT" : "-97.85833,-60.040029999999994,7.909559999999999,45.83612", "INPUT_GROUP" : 1, "INPUT_LAYER" : "'+dirPath+'input/'+inputFile+'", "INPUT_TIMESTEP" : 0,  "OUTPUT_RASTER" : "'+outputDIR+'/'+tiffile+'", "MAP_UNITS_PER_PIXEL" : 0.001}'
    return(json.loads(parms))

# Convert mesh layer as raster and save as a GeoTiff
@ignore_warnings
def exportRaster(parameters):
    # Open layer from inputFile 
    inputFile = 'Ugrid:'+'"'+parameters['INPUT_LAYER']+'"'
    meshfile = inputFile.strip().split('/')[-1]
    meshlayer = meshfile.split('.')[0]
    layer = QgsMeshLayer(inputFile, meshlayer, 'mdal')

    # Check if layer is valid
    if layer.isValid() is True:
        # Get parameters for processing
        dataset  = parameters['INPUT_GROUP'] 
        timestep = parameters['INPUT_TIMESTEP']
        mupp = parameters['MAP_UNITS_PER_PIXEL'] 
        extent = layer.extent()
        output_layer = parameters['OUTPUT_RASTER']
        width = extent.width()/mupp 
        height = extent.height()/mupp 
        crs = layer.crs() 
        crs.createFromSrid(4326)
        transform_context = QgsProject.instance().transformContext()
        output_format = QgsRasterFileWriter.driverForExtension(os.path.splitext(output_layer)[1])

        # Open output file for writing
        rfw = QgsRasterFileWriter(output_layer)
        rfw.setOutputProviderKey('gdal') 
        rfw.setOutputFormat(output_format) 

        # Create one band raster
        rdp = rfw.createOneBandRaster( Qgis.Float64, width, height, extent, crs)

        # Get dataset index
        dataset_index = QgsMeshDatasetIndex(dataset, timestep)

        # Regred mesh layer to raster
        block = QgsMeshUtils.exportRasterBlock( layer, dataset_index, crs,
                transform_context, mupp, extent) 

        # Write raster to GeoTiff file
        rdp.writeBlock(block, 1)
        rdp.setNoDataValue(1, block.noDataValue())
        rdp.setEditable(False)

        logger.info('Regridded mesh data in '+meshfile.split('"')[0]+' to float64 grid, and saved to tiff ('+output_layer.split('/')[-1]+') file.')

        return(output_layer)

    if layer.isValid() is False: 
        raise Exception('Invalid mesh')

# Add color and set transparency to GeoTiff
@ignore_warnings
def styleRaster(filename):
    # Create outfile name
    outfile = "".join(filename.strip().split('.raw'))

    # Open layer from filename
    rasterfile = filename.strip().split('/')[-1]
    rasterlayer = rasterfile.split('.')[0]
    rlayer = QgsRasterLayer(filename, rasterlayer, 'gdal')

    # Check if layer is valid
    if rlayer.isValid() is True:
        # Get layer data provider
        provider = rlayer.dataProvider()

        # Calculate histrogram
        provider.initHistogram(QgsRasterHistogram(),1,100)
        hist = provider.histogram(1)

        # Get histograms stats
        nbins = hist.binCount
        minv = hist.minimum
        maxv = hist.maximum

        # Create histogram array, bin array, and histogram index
        hista = np.array(hist.histogramVector)
        bins = np.arange(minv, maxv, (maxv - minv)/nbins)
        index = np.where(hista > 5)

        # Get bottom and top color values from bin values
        bottomcolor = bins[index[0][0]]
        topcolor = bins[index[0][-1]]

        # Calculate range value between the bottom and top color values
        if bottomcolor < 0:
            vrange = topcolor + bottomcolor
        else:
            vrange = topcolor - bottomcolor 

        # Calculate values for bottom middle, and top middle color values
        if rasterlayer == 'maxele':
            bottommiddle = vrange * 0.3333
            topmiddle = vrange * 0.6667
        else:
            bottommiddle = vrange * 0.375
            topmiddle = vrange * 0.75

        # Create list of color values
        valueList =[bottomcolor, bottommiddle, topmiddle, topcolor]

        # Create color dictionary
        if rasterlayer == 'maxele':
            colDic = {'bottomcolor':'#0000ff', 'bottommiddle':'#00ffff', 'topmiddle':'#ffff00', 'topcolor':'#ff0000'}
        else:
            colDic = {'bottomcolor':'#000000', 'bottommiddle':'#ff0000', 'topmiddle':'#ffff00', 'topcolor':'#ffffff'}

        # Create color ramp function and add colors
        fnc = QgsColorRampShader()
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        lst = [QgsColorRampShader.ColorRampItem(valueList[0], QColor(colDic['bottomcolor'])),\
               QgsColorRampShader.ColorRampItem(valueList[1], QColor(colDic['bottommiddle'])), \
               QgsColorRampShader.ColorRampItem(valueList[2], QColor(colDic['topmiddle'])), \
               QgsColorRampShader.ColorRampItem(valueList[3], QColor(colDic['topcolor']))]
        fnc.setColorRampItemList(lst)

        # Create raster shader and add color ramp function
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)

        # Create color render and set opacity
        renderer = QgsSingleBandPseudoColorRenderer(provider, 1, shader)
        renderer.setOpacity(0.75)

        # Get output format
        output_format = QgsRasterFileWriter.driverForExtension(os.path.splitext(outfile)[1])

        # Open output file for writing
        rfw = QgsRasterFileWriter(outfile)
        rfw.setOutputProviderKey('gdal')
        rfw.setOutputFormat(output_format)

        # Add EPSG 4326 to layer crs
        crs = QgsCoordinateReferenceSystem()
        crs.createFromSrid(4326)

        # Create Raster pipe and set provider and renderer
        pipe = QgsRasterPipe()
        pipe.set(provider.clone())
        pipe.set(renderer.clone())

        # Get transform context
        transform_context = QgsProject.instance().transformContext()

        # Write to file
        rfw.writeRaster(
            pipe,
            provider.xSize(),
            provider.ySize(),
            provider.extent(),
            crs,
            transform_context
        )

        logger.info('Conveted data in '+rasterfile+' from float64 to 8bit, added color palette and saved to tiff ('+outfile.split('/')[-1]+') file')

    if not rlayer.isValid():
        raise Exception('Invalid raster')

    return(valueList)

def moveRaw(inputFile, outputDIR, finalDIR):
    # Create final/tiff directory path
    if not os.path.exists(finalDIR):
        mode = 0o755
        os.makedirs(finalDIR, mode)
        logger.info('Made directory '+finalDIR.split('/')[-1]+ '.')
    else:
        logger.info('Directory '+finalDIR.split('/')[-1]+' already made.')

    tiffraw = inputFile.split('.')[0]+'.raw.'+inputFile.split('.')[1]+'.tif'
    # Check if raw tiff exists, and move it.
    if os.path.exists(outputDIR+'/'+tiffraw):
        shutil.move(outputDIR+'/'+tiffraw, finalDIR+'/'+tiffraw)
        os.remove(outputDIR+'/'+tiffraw+'.aux.xml')
        logger.info('Moved raw tiff file '+tiffraw+ 'to final/tiff directory.')
    else:
        logger.info('Raw tiff file '+rawtiff+' does not exist.')

def moveBar(barPathFile, outputDIR, finalDIR):
    barFile = barPathFile.split('/')[-1]
    # Check if raw tiff exists, and move it.
    if os.path.exists(barPathFile):
        shutil.move(barPathFile, finalDIR+'/'+barFile)
        logger.info('Moved colorbar file '+barFile+ 'to final/tiff directory.')
    else:
        logger.info('Colorbar file '+barFile+' does not exist.')

def hex_to_rgb(value):
    '''
    Converts hex to rgb colours
    value: string of 6 characters representing a hex colour.
    Returns: list length 3 of RGB values'''
    value = value.strip("#") # removes hash symbol if present
    lv = len(value)
    return(tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)))


def rgb_to_dec(value):
    '''
    Converts rgb to decimal colours (i.e. divides each value by 256)
    value: list (length 3) of RGB values
    Returns: list (length 3) of decimal values'''
    return([v/256 for v in value])

def get_continuous_cmap(hex_list, float_list=None):
    '''
    creates and returns a color map that can be used in heat map figures.
    If float_list is not provided, colour map graduates linearly between each color in hex_list.
    If float_list is provided, each color in hex_list is mapped to the respective location in float_list.

    Parameters
    ----------
    hex_list: list of hex code strings
    float_list: list of floats between 0 and 1, same length as hex_list. Must start with 0 and end with 1.

    Returns
    ----------
    colour map'''
    rgb_list = [rgb_to_dec(hex_to_rgb(i)) for i in hex_list]
    if float_list:
        pass
    else:
        float_list = list(np.linspace(0,1,len(rgb_list)))

    cdict = dict()
    for num, col in enumerate(['red', 'green', 'blue']):
        col_list = [[float_list[i], rgb_list[i][num], rgb_list[i][num]] for i in range(len(float_list))]
        cdict[col] = col_list

    cmp = LinearSegmentedColormap('my_cmp', segmentdata=cdict, N=256)
    return(cmp)

def create_colorbar(cmap,values,unit,barPathFile):
    """Plot a colormap with its grayscale equivalent"""
    cmap = plt.cm.get_cmap(cmap)
    colors = cmap(np.arange(cmap.N))

    fig, ax = plt.subplots(1, figsize=(8, 4), subplot_kw=dict(xticks=[], yticks=[]))
    ax.imshow([colors], extent=[0, 20, 0, 3])
    ax.set_xticks([0,5,10,15,20])
    valrange = abs(values[0] - values[3])
    tick1 = '<'+str("{:.2f}".format(values[0]))
    tick2 = str("{:.2f}".format(valrange/4))
    tick3 = str("{:.2f}".format(valrange/2))
    tick4 = str("{:.2f}".format(valrange/1.33))
    tick5 = str("{:.2f}".format(values[3]))+'>'
    ax.set_xticklabels([tick1, tick2, tick3, tick4, tick5])
    ax.set_xlabel(unit)
    plt.savefig(barPathFile, transparent=True)

@logger.catch
def main(args):
    inputFile = args.inputFile
    outputDIR = args.outputDIR
    finalDIR = args.finalDIR

    dirPath = "/".join(outputDIR.split('/')[0:-1])+'/'

    logger.remove()
    log_path = os.getenv('LOG_PATH', os.path.join(os.path.dirname(__file__), 'logs'))
    logger.add(log_path+'/adcirc2geotiff-logs.log', level='DEBUG')

    # When error exit program
    logger.add(lambda _: sys.exit(1), level="ERROR")

    makeDIRS(outputDIR.strip())

    os.environ['QT_QPA_PLATFORM']='offscreen'
    xdg_runtime_dir = '/run/user/adcirc2geotiff'
    os.makedirs(xdg_runtime_dir, exist_ok=True)
    os.environ['XDG_RUNTIME_DIR']=xdg_runtime_dir
    logger.info('Set QGIS enviroment.')

    app = initialize_qgis_application() 
    app.initQgis()
    app, processing = initialize_processing(app)
    logger.info('Initialzed QGIS.')

    parameters = getParameters(dirPath, inputFile.strip(), outputDIR.strip())
    logger.info('Got mesh regrid paramters for '+inputFile.strip())

    filename = exportRaster(parameters)
    valueList = styleRaster(filename)

    barPathFile = ".".join("".join(filename.strip().split('.raw')).split('.')[0:-1])+'.colorbar.png'
    barvar = filename.strip().split('/')[-1].split('.')[0]

    if barvar == 'maxele':
        hexList = ['#0000ff', '#00ffff', '#ffff00', '#ff0000']
        unit = 'm'
    elif barvar == 'maxwvel':
        hexList = ['#000000', '#ff0000', '#ffff00', '#ffffff']
        unit = 'm'
    elif barvar == 'swan_HS_max':
        hexList = ['#000000', '#ff0000', '#ffff00', '#ffffff']
        unit = 'm s-1'
    else:
        logger.info('Incorrect rlayer name')

    cmap = get_continuous_cmap(hexList)
    create_colorbar(cmap,valueList,unit,barPathFile)

    app.exitQgis()
    logger.info('Quit QGIS')

    moveRaw(inputFile, outputDIR, finalDIR)
    logger.info('Moved float64 tiff file')

    moveBar(barPathFile, outputDIR, finalDIR)
    logger.info('Moved colorbar png file')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("--inputFile", action="store", dest="inputFile")
    parser.add_argument("--outputDIR", action="store", dest="outputDIR")
    parser.add_argument("--finalDIR", action="store", dest="finalDIR")

    args = parser.parse_args()
    main(args)

