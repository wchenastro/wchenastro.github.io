import datetime, io, logging, re, sys

import asyncio
from astropy import units as u
from astropy.coordinates import SkyCoord

import numpy as np

from js import document, URL, File, Uint8Array, Blob, btoa, encodeURIComponent, unescape
from pyodide.ffi import create_proxy
import pyscript
from pyscript import display
import matplotlib
matplotlib.use('SVG')

from mosaic.beamforming import PsfSim, generate_nbeams_tiling
from mosaic.coordinate import convert_sexagesimal_to_degree, createTilingRegion, readPolygonRegion, convert_equatorial_coordinate_to_pixel
from mosaic.plot import plot_overlap, plot_interferometry
from mosaic import __version__

log_stream = io.StringIO()
loggerFormatString = '%(levelname)s - %(asctime)-15s - %(name)s - %(message)s'
loggerFormat = logging.Formatter(loggerFormatString)
logger = logging.getLogger('mosaic')
stream_handler = logging.StreamHandler(log_stream)
stream_handler.setFormatter(loggerFormat)
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)

def Element(element_id):
    """
    emunuate the old Element() function
    """
    return pyscript.document.getElementById(element_id)

def get_parameters():
    parameters = {}
    parameters['array_name'] = Element("array_selection").value
    parameters['frequency'] = Element("frequency").value
    parameters['ra'] = Element("ra").value
    parameters['dec'] = Element("dec").value
    parameters['date'] = Element("date").value
    parameters['time'] = Element("time").value
    parameters['array'] = Element("array").value
    parameters['size'] = float(Element("size").value)
    parameters['resolution'] = Element("resolution").value
    parameters['beam_num'] = int(Element("beam_num").value)
    parameters['overlap'] = float(Element("overlap").value)

    parameters['tiling_method'] = Element("tiling_method").value
    parameters['tiling_shape'] = Element("tiling_shape").value
    if parameters['tiling_method'] == 'variable_overlap':
        if parameters['tiling_shape'] == "circle":
            parameters['tiling_parameter'] = float(Element("radius").value)

        elif parameters['tiling_shape'] == "hexagon":
            parameters['tiling_parameter'] = [float(Element("circumradius").value),
                                            float(Element("hexagon_angle").value)]
        elif parameters['tiling_shape'] == "ellipse":
            parameters['tiling_parameter'] = [float(Element("semi_axis1").value),
                float(Element("semi_axis2").value), float(Element("ellipse_angle").value)]
        elif parameters['tiling_shape'] == "polygon":
            vertices = Element("vertices").value
            if vertices.strip() != "":
                vertices_string = vertices.split(",")
                coordinate_sexagesami = np.array(vertices_string).reshape(-1,2)
                coordinate_degree = SkyCoord(
                    coordinate_sexagesami[:,0], coordinate_sexagesami[:,1],
                    frame='fk5', unit=(u.hourangle, u.deg))
                parameters['tiling_parameter'] = np.dstack((coordinate_degree.ra.value,
                            coordinate_degree.dec.value))[0].tolist()
    else:
        parameters['tiling_parameter'] = None

    if parameters['resolution'].strip() == '':
        parameters['resolution'] = None
    else:
        parameters['resolution'] = float(parameters['resolution'])



    if parameters['array_name'] == 'meerkat':
        parameters['array'] = np.int32(parameters['array'].split(","))
    elif parameters['array_name'] == 'custom':
        coordinate_1d = np.fromstring(
                parameters['array'].replace("\n", ' '), dtype=float, sep=' ')
        coordinate_2d = coordinate_1d.reshape(-1, 3)
        parameters['array'] = coordinate_2d
        # parameters['reference'] = (
                # float(Element('lon').value),
                # float(Element('lat').value), float(Element('height').value))
    parameters['source'] = (parameters['ra'],  parameters['dec'])
    parameters['datetime'] = datetime.datetime.strptime(parameters['date'] + " "
                + parameters['time'], '%Y-%m-%d %H:%M:%S.%f')


    point_sources_lines = Element("point_sources").value
    point_sources_lines = point_sources_lines.split('\n')
    point_sources = []
    for line in point_sources_lines:
        line = line.strip()
        if line.startswith('#') or line == '':
            continue
        else:
            point_sources.append(line.split())
    if point_sources != []:
        parameters['point_sources'] = point_sources
    else:
        parameters['point_sources'] = None

    if Element("psf_fits_checkbox").checked:
        parameters['psf_fits'] = True
    else:
        parameters['psf_fits'] = False

    if Element("psf_plot_checkbox").checked:
        parameters['psf_plot'] = True
    else:
        parameters['psf_plot'] = False

    if Element("tiling_checkbox").checked:
        parameters['tiling_plot'] = True
    else:
        parameters['tiling_plot'] = False

    if Element("region_checkbox").checked:
        parameters['tiling_region'] = True
    else:
        parameters['tiling_region'] = False

    return parameters

def convert_equatorial_to_pixel_coordinates(equatorial_coords_input, bore_sight_input):
    bore_sight = convert_sexagesimal_to_degree([bore_sight_input,])[0]
    equatorial_coordinates_degree = convert_sexagesimal_to_degree(
            equatorial_coords_input)
    pixel_coordinates = convert_equatorial_coordinate_to_pixel(
            equatorial_coordinates_degree, bore_sight)

    return pixel_coordinates

def remove_content(container_id):
    container_tag = document.getElementById(container_id)
    container_tag.innerHTML=''

def append_log(log, container_id):

    log_container_tag = document.getElementById(container_id)
    new_log_tag = document.createElement('div')
    new_log_tag.className = 'log_entry'
    log_container_tag.appendChild(new_log_tag)
    log = log.replace('\n', '<br />')
    new_log_tag.innerHTML = log

    if log_container_tag.childElementCount > 11:
        log_container_tag.children[1].remove()

    log_container_tag.scrollTop = log_container_tag.scrollHeight

def create_plot(plot_buffer, container_id):
    filename = container_id + ".png"
    plot_container_tag = document.getElementById(container_id)
    plot_tag = document.getElementById(container_id + '_image')
    if plot_tag is None:
        plot_tag = document.createElement('img')
        plot_tag.id = container_id + '_image'
        plot_container_tag.appendChild(plot_tag)

    if isinstance(plot_buffer, io.BytesIO) is True:
        plot_content = Uint8Array.new(plot_buffer.getvalue())
        plot_tag.src = URL.createObjectURL(plot_file)
    else:
        plot_content = plot_buffer.getvalue()
        base64_plot = "data:image/svg+xml;base64," + btoa(
                unescape(encodeURIComponent(plot_content)))
        plot_tag.src = base64_plot

def create_download(file_buffer, container_id, title, extension, MIME):
    filename = container_id + "." + extension
    download_container_tag = document.getElementById(container_id)
    download_tag = document.getElementById(container_id  + '_link')
    if download_tag is None:
        download_tag = document.createElement('a')
        download_tag.id = container_id  + '_link'
        download_tag.innerHTML = title
        download_container_tag.appendChild(download_tag)
        download_tag.download = filename

    if isinstance(file_buffer, io.BytesIO) is True:
        file_content = Uint8Array.new(file_buffer.getvalue())
    else:
        file_content = file_buffer.getvalue()

    download_file = File.new([file_content],
            filename, {type: MIME})
    download_tag.href = URL.createObjectURL(download_file)

# Run this using "asyncio"
async def run_mosaic_button_handler(event):

    button = document.getElementById("run_button")
    info_container_tag = document.getElementById('info')
    info_container_tag.innerHTML=""
    try:
        await run_mosaic()
    except Exception as e:
        import traceback
        traceback_string = traceback.format_exc().replace('\n', '<br />')
        info_container_tag.innerHTML = traceback_string

    enable_run_button()

def disable_run_button(event):

    button = document.getElementById("run_button")
    button.innerHTML = 'Please wait'
    document.body.style.cursor = 'wait'
    button.disabled = True

def enable_run_button():

    button = document.getElementById("run_button")
    button.innerHTML = 'Run'
    document.body.style.cursor = 'auto'
    button.disabled = False

def initialization():

    run_button_click_proxy = create_proxy(run_mosaic_button_handler)
    run_button_disable_proxy = create_proxy(disable_run_button)
    run_button = document.getElementById("run_button")
    run_button.innerHTML = 'Run'
    run_button.addEventListener("click", run_button_disable_proxy)
    run_button.addEventListener("click", run_button_click_proxy)
    document.body.style.cursor = 'auto'

async def run_mosaic():

    try:
        parameters = get_parameters()
    except Exception as e:
        raise Exception("At least one of the parameter is not valid.")

    information_board = Element("info")
    if not (parameters['psf_plot'] or
            parameters['psf_fits'] or
            parameters['tiling_plot'] or
            parameters['tiling_region']):
        information_board.innerHTML = 'Please select an output above!'
        return
    else:
        information_board.innerHTML = ''

    if parameters['array_name'] == 'meerkat':
        full_antenna_geo = np.loadtxt('antenna.geo.csv')
        antenna_geo = [full_antenna_geo[ant] for ant in parameters['array']]
    elif parameters['array_name'] == 'custom':
        # reference = parameters['reference']
        antenna_geo = [ant for ant in parameters['array']]
        # psf = PsfSim(antenna_geo, float(parameters['frequency']), reference)
    psf = PsfSim(antenna_geo, float(parameters['frequency']))
    beam_shape = psf.get_beam_shape(parameters['source'], parameters['datetime'],
        parameters['size'], parameters['resolution'], None)
    overlap = parameters['overlap']
    """
    if parameters['tiling_method'] == 'variable_size':
        overlay = True
    else:
        overlay = False
    """

    if parameters['psf_fits'] is True:
        fits_file_buffer = io.BytesIO()
        beam_shape.psf.write_fits(fits_file_buffer)
        # create_download(fits_file_buffer, 'psf_fits', 'Fits')
        create_download(fits_file_buffer, 'psf_fits', 'Fits', 'fits', 'application/fits')
    else:
        remove_content('psf_fits')

    if parameters['tiling_plot'] or parameters['tiling_region' ] is True:
        tiling = generate_nbeams_tiling(beam_shape, parameters['beam_num'],
            parameters['overlap'], parameters['tiling_method'],
            parameters['tiling_shape'], parameters['tiling_parameter'],
            coordinate_type = 'equatorial')
        overlap = tiling.overlap

        if parameters['tiling_plot'] is True:
            #tiling_plot_buffer = io.BytesIO()
            if parameters['point_sources'] is not None:
                point_sources = np.array(parameters['point_sources'])
                point_sources_name = point_sources[:, 0]
                point_sources_coord_input = point_sources[:, 1:]
                point_sources_coordinates = convert_equatorial_to_pixel_coordinates(
                    point_sources_coord_input, parameters['source'])
            else:
                point_sources_coordinates = []
                point_sources_name = []

            tiling_plot_buffer = io.StringIO()
            tiling.plot_tiling(tiling_plot_buffer, HD=True, edge=True,
                extra_coordinates = point_sources_coordinates,
                extra_coordinates_text = point_sources_name,
                output_format='svg')
            create_plot(tiling_plot_buffer, 'tiling_plot')
        else:
            remove_content('tiling_plot')

        if parameters['tiling_region'] is True:
            tiling_region_buffer = io.StringIO()
            equatorial_coordinates = tiling.get_equatorial_coordinates()
            actualShape = tiling.meta["axis"]
            createTilingRegion(equatorial_coordinates, actualShape, tiling_region_buffer)
            # create_text_download(tiling_region_buffer, 'tiling_region', 'Region')
            create_download(tiling_region_buffer, 'tiling_region', 'Region', 'reg', 'text/plain')
        else:
            remove_content('tiling_region')
        overlay = True
    else:
        remove_content('tiling_plot')
        remove_content('tiling_region')
        overlay = False

    if parameters['psf_plot'] is True:

        psf_plot_buffer = io.StringIO()
        beam_shape.plot_psf(psf_plot_buffer, overlap = overlap,
            shape_overlay=overlay, interpolation=True, output_format='svg')
        create_plot(psf_plot_buffer, 'psf_plot')
    else:
        remove_content('psf_plot')



    append_log(log_stream.getvalue(), 'logs')

    # Element("logs").write(log_stream.getvalue())
    log_stream.truncate(0)
    log_stream.seek(0)

initialization()
