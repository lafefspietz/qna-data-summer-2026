const socket = new WebSocket('ws://localhost:8080');

instrument = {};
cold_switch_states = {};

function sendData(instrumentData) {
  socket.send(JSON.stringify(instrumentData));
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
  
  cold_switch_states.cold_output_switch_1 = instrument.cold_output_switch_1.state
  cold_switch_states.cold_output_switch_2 = instrument.cold_output_switch_2.state
  cold_switch_states.cold_thru_switch_pair = instrument.cold_thru_switch_pair.state
  
}

document.querySelector('fieldset').addEventListener('change', (event) => {
  let name = event.target.name;
  let value = event.target.value;
//    console.log(name);
  //  console.log(value);
    cold_switch_states[name] = value;
    
  console.log(JSON.stringify(cold_switch_states));  

  sendData(cold_switch_states);
  
});