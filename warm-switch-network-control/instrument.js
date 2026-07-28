const debug_mode = false;
let socket = null;

if (!debug_mode) {
  socket = new WebSocket('ws://localhost:8080');
}

let instrument = {};
let warm_switch_states = {};

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

function loadMenus() {
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


  document.querySelector('input[name="programmable_attenuator"]').value = -Math.abs(instrument.programmable_attenuator.value);

  warm_switch_states.measurement_select = instrument.measurement_select.state;
  warm_switch_states.s_parameter_select = instrument.s_parameter_select.state;
  warm_switch_states.twpa_pump_select = instrument.twpa_pump_select.state;
  warm_switch_states.jpa_pump_select = instrument.jpa_pump_select.state;
  warm_switch_states.programmable_attenuator = Number(document.querySelector('input[name="programmable_attenuator"]').value);
  
}

document.querySelector('fieldset').addEventListener('change', (event) => {
  let name = event.target.name;
  let value = event.target.value;

  if (name === "programmable_attenuator") {
    warm_switch_states[name] = Number(value);
  } else {
    warm_switch_states[name] = value;
  }
    
  console.log(JSON.stringify(warm_switch_states));  
  sendData(warm_switch_states);
});
