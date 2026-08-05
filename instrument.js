debug_mode = false;

if (!debug_mode) {
  socket = new WebSocket('ws://localhost:8080');
}

instrument = {};
state = {};


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
    fetch('load-file.php?filename=state.json')
      .then(response => response.text())
      .then(data => {
        state = JSON.parse(data.trim());
        loadMenus();
      });
    
  });


function loadMenus(){

  instrument.cold_output_switch_1.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="cold_output_switch_1"]').appendChild(option);
  });
  document.querySelector('select[name="cold_output_switch_1"]').value = state.cold_output_switch_1;

  instrument.cold_output_switch_2.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="cold_output_switch_2"]').appendChild(option);
  });
  document.querySelector('select[name="cold_output_switch_2"]').value = state.cold_output_switch_2;

  instrument.cold_thru_switch_pair.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="cold_thru_switch_pair"]').appendChild(option);
  });
  document.querySelector('select[name="cold_thru_switch_pair"]').value = state.cold_thru_switch_pair;

instrument.measurement_select.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="measurement_select"]').appendChild(option);
  });
  document.querySelector('select[name="measurement_select"]').value = state.measurement_select;

  instrument.s_parameter_select.options.forEach(item => {
    let option = document.createElement("option");
    option.value = item.key;
    option.text = item.text;
    document.querySelector('select[name="s_parameter_select"]').appendChild(option);
  });
  document.querySelector('select[name="s_parameter_select"]').value = state.s_parameter_select;

  instrument.twpa_pump_select.options.forEach(item => {
  let option = document.createElement("option");
  option.value = item.key;
  option.text = item.text;
  document.querySelector('select[name="twpa_pump_select"]').appendChild(option);
    });
    document.querySelector('select[name="twpa_pump_select"]').value = state.twpa_pump_select;

  instrument.jpa_pump_select.options.forEach(item => {
  let option = document.createElement("option");
  option.value = item.key;
  option.text = item.text;
  document.querySelector('select[name="jpa_pump_select"]').appendChild(option);
    });
    document.querySelector('select[name="jpa_pump_select"]').value = state.jpa_pump_select;


  document.querySelector('input[name="programmable_attenuator"]').value = Math.abs(state.programmable_attenuator);

  document.querySelector('input[name="vna_source_power"]').value = state.vna_source_power;
  document.querySelector('input[name="vna_if_bandwidth"]').value = state.vna_if_bandwidth;
  document.querySelector('input[name="spa_resolution_bandwidth"]').value = state.spa_resolution_bandwidth / 1e6;
  document.querySelector('input[name="spa_video_bandwidth"]').value = state.spa_video_bandwidth / 1e3;
  
  document.querySelector('input[name="vna_start_frequency"]').value = state.vna_start_frequency / 1e9;
  document.querySelector('input[name="vna_stop_frequency"]').value = state.vna_stop_frequency / 1e9;
  document.querySelector('input[name="vna_number_of_points"]').value = state.vna_number_of_points;

}

document.body.addEventListener('change', (event) => {
    
  let name = event.target.name;
  let value = event.target.value;
  console.log("name = " + name);
  console.log("value = " + value);
  
  if (name.startsWith('cold_')) {
    state[name] = value;
  } else if (
    name === "vna_source_power" || 
    name === "vna_if_bandwidth" || 
    name === "vna_number_of_points" ||
    name === "spa_number_of_points"
  ) {
    state[name] = Number(value);
  } else if (name === "spa_video_bandwidth") {
    state[name] = Math.round(Number(value) * 1e3);
  } else if (name === "spa_resolution_bandwidth") {
    state[name] = Math.round(Number(value) * 1e6);
  } else if (name === "vna_start_frequency" || name === "vna_stop_frequency" || name === "spa_start_frequency" || name === "spa_stop_frequency") {
    state[name] = Math.round(Number(value) * 1e9);
  } else {
    if (name === "programmable_attenuator") {
      state[name] = Number(value);
    } else {
      state[name] = value;
    }
  }
  
    fetch('save-file.php', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' }, 
        body: `data=${encodeURIComponent(JSON.stringify(state, null, 4))}&filename=${encodeURIComponent('state.json')}` 
    });

  console.log(JSON.stringify(state));  
  sendData(state);
 
 
  
});
