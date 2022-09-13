
full_antennas = '000,001,002,003,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,019,020,021,022,023,024,025,026,027,028,029,030,031,032,033,034,035,036,037,038,039,040,041,042,043,044,045,046,047,048,049,050,051,052,053,054,055,056,057,058,059,060,061,062,063'

core_antennas = '000,001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012, 013, 014, 015, 016, 017, 018, 019, 020, 021, 022, 023, 024, 025, 026, 027, 028, 029, 030, 031, 032, 034, 035, 036, 037, 038, 039, 040, 041, 042, 043, 047'

function add_antennas_button_handler(event) {
    const configuration = event.target.getAttribute("configuration");
    add_antennas(configuration);
}

function add_antennas(configuration) {
    const array_input = document.getElementById('array');
    if (configuration == 'full' ||  configuration == undefined) {
        array_input.value = full_antennas;
    } else if (configuration == 'core') {
        array_input.value = core_antennas;
    }
}

function add_point_sources_button_handler(event) {
    const this_button = event.target;
    const point_sources_input_area = document.getElementById('point_sources');
    if (point_sources_input_area.style.display == 'block') {
        point_sources_input_area.style.display = 'none';
        this_button.innerHTML = '+';
    } else {
        point_sources_input_area.style.display = 'block';
        this_button.innerHTML = '-';
    }
}


function log_toggle_handler(event) {
    /*
    const log_panel = document.getElementById('logs');
    if (log_panel.style.display == 'block') {
        log_panel.style.display = 'none';
    } else {
        log_panel.style.display = 'block';
    }
    */
    const log_panel = document.getElementById('logs');
    const is_checked = event.target.checked;
    if (is_checked) {
        log_panel.style.display = 'block';
        log_panel.scrollTop = log_panel.scrollHeight;
    } else {
        log_panel.style.display = 'none';
    }
}

function hide_tiling_parameters() {
    const elements_tp = document.getElementsByClassName('tiling_parameter');
    for (let i=0; i<elements_tp.length; i++) {
        elements_tp[i].style.display = 'none';
    }
}

function tiling_method_handler(event) {
    const method = event.target.value;
    select_tiling_mode(method);
}

function tiling_shape_handler(event) {
    const shape = event.target.value;
    hide_tiling_parameters();
    select_tiling_shape(shape);
}

function contact_handler(event) {
    const link_tag = event.target;
    const data = "Z0BAMHJAQGQ5MkBAdzVmQG1vekBAbWFpbC5jb0BAbQ==";
    const subject = "TW9zYWljIHdlYiBmZWVkYmFjaw==";
    const address = atob(data).replaceAll('@@', '')
    link_tag.href = 'mailto:' + address + '?subject=' + atob(subject || '');
    link_tag.innerHTML = address
}


function select_tiling_mode(method) {

    if (method == undefined) {
        const tiling_method_selector = document.getElementById('tiling_method');
        method = tiling_method_selector.value;
    }

    const elements_vo = document.getElementsByClassName('variable_overlap');
    const elements_vs = document.getElementsByClassName('variable_size');
	//const overlap_input = document.getElementById('overlap');
    if (method == 'variable_size') {
		//overlap_input.disabled = false;
        for (let i=0; i<elements_vo.length; i++) {
            elements_vo[i].disabled = true;
        }
        for (let i=0; i<elements_vs.length; i++) {
            elements_vs[i].style.display = 'inline';
        }

    } else if (method == 'variable_overlap') {
		//overlap_input.disabled = true;
        for (let i=0; i<elements_vo.length; i++) {
            elements_vo[i].disabled = false;
        }
        for (let i=0; i<elements_vs.length; i++) {
            elements_vs[i].style.display = 'none';
        }

    }

}

function select_tiling_shape(shape) {

    if (shape == undefined) {
        const tiling_shape_selector = document.getElementById('tiling_shape');
        shape = tiling_shape_selector.value;
    }

    const elements = document.getElementsByClassName(shape);
    for (let i=0; i<elements.length; i++) {
        elements[i].style.display = "inline-block";
    }

}
function connect_events() {

    tiling_method_selector = document.getElementById('tiling_method');
    tiling_method_selector.addEventListener('change', tiling_method_handler);
    tiling_shape_selector = document.getElementById('tiling_shape');
    tiling_shape_selector.addEventListener('change', tiling_shape_handler);
    add_core_antennas_button = document.getElementById('add_core_antennas_button');
    add_full_antennas_button = document.getElementById('add_full_antennas_button');
    add_core_antennas_button.addEventListener('click', add_antennas_button_handler);
    add_full_antennas_button.addEventListener('click', add_antennas_button_handler);
    const add_point_sources_button = document.getElementById('add_point_sources_button');
    add_point_sources_button.addEventListener('click', add_point_sources_button_handler);
    const log_toggle = document.getElementById('show_logs');
    log_toggle.addEventListener('click', log_toggle_handler);
    const contact_link = document.getElementById('contact');
    contact_link.addEventListener('click', contact_handler);
    console.log('connected');
}


function initialization() {
    document.body.style.cursor = 'wait';
    connect_events();
    add_antennas();
    select_tiling_mode(undefined);
    select_tiling_shape(undefined);
}

window.onload = initialization;
