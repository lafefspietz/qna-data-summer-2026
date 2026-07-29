debug_mode = true;

if (!debug_mode) {
  socket = new WebSocket('ws://localhost:8080');
}

instrument = {};
cold_switch_states = {};
warm_switch_states = {};
analyzer_states = {};

virtual_instrument_payload = {};

function sendData(instrumentData) {
  if (!debug_mode && socket) {
    socket.send(JSON.stringify(instrumentData));
  } else {
    console.log("Debug Mode (No Socket Connection):", instrumentData);
  }
}

fetch('load-file.php?filename=instrument.json')
  .then(response => response.text())
  .then(data => {
    instrument = JSON.parse(data.trim());
    loadMenus();
  });


function loadMenus(){
  instrument.cold_output_switch_1.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="cold_output_switch_1"]').appendChild(option);
  });
  document.querySelector('select[name="cold_output_switch_1"]').value = instrument.cold_output_switch_1.state;

  instrument.cold_output_switch_2.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="cold_output_switch_2"]').appendChild(option);
  });
  document.querySelector('select[name="cold_output_switch_2"]').value = instrument.cold_output_switch_2.state;

  instrument.cold_thru_switch_pair.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="cold_thru_switch_pair"]').appendChild(option);
  });
  document.querySelector('select[name="cold_thru_switch_pair"]').value = instrument.cold_thru_switch_pair.state;

instrument.measurement_select.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="measurement_select"]').appendChild(option);
  });
  document.querySelector('select[name="measurement_select"]').value = instrument.measurement_select.state;

  instrument.s_parameter_select.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="s_parameter_select"]').appendChild(option);
  });
  document.querySelector('select[name="s_parameter_select"]').value = instrument.s_parameter_select.state;

  instrument.twpa_pump_select.options.forEach(item => {
  let option = document.createElement("option");
  option.value = item.key;
  option.text = item.text;
  document.querySelector('select[name="twpa_pump_select"]').appendChild(option);
    });
    document.querySelector('select[name="twpa_pump_select"]').value = instrument.twpa_pump_select.state;

  instrument.jpa_pump_select.options.forEach(item => {
  let option = document.createElement("option");
  option.value = item.key;
  option.text = item.text;
  document.querySelector('select[name="jpa_pump_select"]').appendChild(option);
    });
    document.querySelector('select[name="jpa_pump_select"]').value = instrument.jpa_pump_select.state;


  document.querySelector('input[name="programmable_attenuator"]').value = Math.abs(instrument.programmable_attenuator.value);

  document.querySelector('input[name="vna_source_power"]').value = instrument.analyzer.vna_source_power;
  document.querySelector('input[name="vna_if_bandwidth"]').value = instrument.analyzer.vna_if_bandwidth;
  document.querySelector('input[name="sa_resolution_bandwidth"]').value = instrument.analyzer.sa_resolution_bandwidth / 1e6;
  document.querySelector('input[name="sa_video_bandwidth"]').value = instrument.analyzer.sa_video_bandwidth / 1e3;
  document.querySelector('input[name="start_frequency"]').value = instrument.analyzer.start_frequency / 1e9;
  document.querySelector('input[name="stop_frequency"]').value = instrument.analyzer.stop_frequency / 1e9;
  document.querySelector('input[name="number_of_points"]').value = instrument.analyzer.number_of_points;

  warm_switch_states.measurement_select = instrument.measurement_select.state;
  warm_switch_states.s_parameter_select = instrument.s_parameter_select.state;
  warm_switch_states.twpa_pump_select = instrument.twpa_pump_select.state;
  warm_switch_states.jpa_pump_select = instrument.jpa_pump_select.state;
  warm_switch_states.programmable_attenuator = Number(document.querySelector('input[name="programmable_attenuator"]').value);  
  
  cold_switch_states.cold_output_switch_1 = instrument.cold_output_switch_1.state;
  cold_switch_states.cold_output_switch_2 = instrument.cold_output_switch_2.state;
  cold_switch_states.cold_thru_switch_pair = instrument.cold_thru_switch_pair.state;
  
  analyzer_states.vna_source_power = instrument.analyzer.vna_source_power;
  analyzer_states.vna_if_bandwidth = instrument.analyzer.vna_if_bandwidth;
  analyzer_states.sa_resolution_bandwidth = instrument.analyzer.sa_resolution_bandwidth;
  analyzer_states.sa_video_bandwidth = instrument.analyzer.sa_video_bandwidth;
  analyzer_states.start_frequency = instrument.analyzer.start_frequency;
  analyzer_states.stop_frequency = instrument.analyzer.stop_frequency;
  analyzer_states.number_of_points = instrument.analyzer.number_of_points;
}

document.body.addEventListener('change', (event) => {
  let name = event.target.name;
  let value = event.target.value;
  
  if (name.startsWith('cold_')) {
    cold_switch_states[name] = value;
  } else if (
    name === "vna_source_power" || 
    name === "vna_if_bandwidth" || 
    name === "number_of_points"
  ) {
    analyzer_states[name] = Number(value);
  } else if (name === "sa_video_bandwidth") {
    analyzer_states[name] = Math.round(Number(value) * 1e3);
  } else if (name === "sa_resolution_bandwidth") {
    analyzer_states[name] = Math.round(Number(value) * 1e6);
  } else if (name === "start_frequency" || name === "stop_frequency") {
    analyzer_states[name] = Math.round(Number(value) * 1e9);
  } else {
    if (name === "programmable_attenuator") {
      warm_switch_states[name] = Number(value);
    } else {
      warm_switch_states[name] = value;
    }
  }
  
  virtual_instrument_payload.warm_switch_states = warm_switch_states;
  virtual_instrument_payload.cold_switch_states = cold_switch_states;
  virtual_instrument_payload.analyzer_states = analyzer_states;
    
  console.log(JSON.stringify(virtual_instrument_payload));  

  sendData(virtual_instrument_payload);
});
