"use strict;"

const URL = "events";
const URL_run = "run";
const URL_selected = "selected";
const off_keys = ["theta_deg_off_1", "theta_deg_off_2", "theta_deg_off_3", "theta_deg_off_5"]
let skymapDiv = document.getElementById('skymap');
let theta2Div = document.getElementById('theta2');
let excessRateDiv = document.getElementById('excessRate');

let lastTimestamp = null;
var lastTimefrom = null;


let skymap = {
  data: [
    {
    x: [], 
    y: [], 
    type: 'histogram2d', 
    nbinsx: 50, 
    nbinsy: 50,
    colorscale: 'Blackbody',
    }
  ],
  layout: {
    title: 'Skymap:',
    titlefont: {
      family: 'Georgia, serif',
      size: 30,
      color: '#000000'
    },
    xaxis: {title: 'RA / °', constrain: 'domain'},
    yaxis: {title: 'Dec / °', scaleanchor: 'x'},
  }
}


let excessRate = {
  data: [
    {
    x: [], 
    y: [], 
    type: 'scatter',
    mode: 'markers',
    marker: {color: 'green'},
    }
  ],
  layout: {
    title: 'Excess Rate:',
    titlefont: {
      family: 'Georgia, serif',
      size: 30,
      color: '#000000'
    },
    yaxis: {title: 'Excess', range:[-20,370],}, //range:[-10, 150],
    xaxis: {title: 'Date',},

  }
}

let theta2 = {
  data: [
    {
      x: [],
      y: [],
      name: 'On region',
      type: 'histogram',
      opacity: 0.4,
      marker: {color: 'green'},
      histfunc: "sum",
      xbins: {start: 0, end: 0.3, size: 0.015}
    },
    {
      x: [],
      y: [],
      name: 'Off region',
      opacity:0.6,
      marker: {color: 'gray'},
      type: 'histogram',
      histfunc: "sum",
      xbins: {start: 0, end: 0.3, size: 0.015}
    },
  ],
  layout: {
    title: 'Source Detection:',
    titlefont: {
      family: 'Georgia, serif',
      size: 30,
      color: '#000000'
    },
    xaxis: {title: 'Theta² in deg²', }, 
    yaxis: {title: 'Count N'},
    barmode: "overlay",
    legend: {
        x: 0.80,
        y: 0.90,
        bgcolor: '#E2E2E2',
        bordercolor: 'green',
        borderwidth: 2, },
    shapes: [{
            type: 'line',
            x0: 0.025,
            x1: 0.025,
            y0: 0,
            y1: 600,
            line: {
                color: 'red',
                width: 2,
            },
    },
    ],
  }
}

function getData() {
    $.getJSON(URL_run, {timestamp: lastTimestamp, lasttimefrom: lastTimefrom}, updateExcess);  
    $.getJSON(URL, {timestamp: lastTimestamp, lasttimefrom: lastTimefrom}, updatePlots);
        
    var currentdate = new Date();  
    var months = (currentdate.getMonth()+1);
    var days = currentdate.getDate();
    var hours   = (currentdate.getHours());
    var minutes = currentdate.getMinutes();
    var seconds = currentdate.getSeconds();

    if (months < 10) {months = "0"+months;}
    if (days < 10) {days = "0"+days;}
    if (hours   < 10) {hours   = "0"+hours;}
    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    
    var time = currentdate.getFullYear() +"-"+ months + "-" + days + "&nbsp;"  + hours  + ":" + minutes + ":" + seconds;
    document.getElementById("time").innerHTML = time;
}


function updateExcess(excess) {
    let new_rate = [];
    let new_timefrom = [];

    excess.forEach((excess) => {
    new_rate.push(excess['rate']);
    new_timefrom.push(excess['timefrom']);
    })
    
    lastTimefrom = new_timefrom[new_timefrom.length - 1];
    
    Plotly.extendTraces(
      excessRateDiv, {x: [new_timefrom], y: [new_rate]}, [0]
    );
    Plotly.relayout(excessRateDiv, excessRate.layout);

    console.log("Got Excess Rates");
}

function updatePlots(data) {
  let new_ra = [];
  let new_dec = [];

  let new_theta2_on = [];
  let new_theta2_off = [];
  let new_off_weights = [];
  let new_on_weights = [];
  
  let new_timestamp = [];
  let new_source = [];

  data.forEach((data) => {
    new_ra.push(data['ra_prediction'] * 15);
    new_dec.push(data['dec_prediction']);

    new_theta2_on.push(Math.pow(data['theta_deg'], 2.0)); 
    new_on_weights.push(1.0); 
    off_keys.forEach((key) => {
      new_theta2_off.push(Math.pow(data[key], 2.0)); 
      new_off_weights.push(0.2);
    
    new_timestamp.push(data['timestamp']);  
    new_source.push(data['source']);
    })
    lastTimestamp = new_timestamp[new_timestamp.length - 1];
    lastTimefrom = new_timestamp[new_timestamp.length - 1];
    document.getElementById("lasttimestamp").innerHTML = lastTimestamp.substring(0, 19);
    lastsource = new_source[new_source.length - 1];
    document.getElementById("lastsource").innerHTML = lastsource;
  }) 

  Plotly.extendTraces(theta2Div, {
    x: [new_theta2_on, new_theta2_off], y: [new_on_weights, new_off_weights]
  }, [0, 1]);
  Plotly.relayout(theta2Div, theta2.layout);
  
  Plotly.extendTraces(
    skymapDiv, {x: [new_ra], y: [new_dec]}, [0]
  );
  Plotly.relayout(skymapDiv, skymap.layout);
  
  console.log("Got Data");
}


/*
function updateSelected(data) {
  let new_ra = data['ra_prediction'] * 15;
  let new_dec = data['dec_prediction'];

  let new_theta2_on = Math.pow(data['theta_deg'], 2.0);
  let new_theta2_off = Math.pow(data[key], 2.0);
  let new_off_weights = 1;
  let new_on_weights = 0.2;
  
  let new_timestamp = data['timestamp'];
  let new_source = data['source'];

  Plotly.restyle(theta2Div, {
    x: [new_theta2_on, new_theta2_off], y: [new_on_weights, new_off_weights]
  }, [0, 1]);
  Plotly.relayout(theta2Div, theta2.layout);
  
  Plotly.restyle(
    skymapDiv, {x: [new_ra], y: [new_dec]}, [0]
  );
  Plotly.relayout(skymapDiv, skymap.layout);
  
  console.log("Selected Data");
}
*/


var layouttheta = {
  autosize: false,
  width: 950,
  height: 500,
}

var layoutexcess = {
  autosize: false,
  width: 950,
  height: 500,
}
var layoutskymap = {
  autosize: false,
  width: 500,
  height: 500,
}

function setupPlots() {
  Plotly.newPlot(theta2Div, theta2.data, layouttheta);
  Plotly.newPlot(excessRateDiv, excessRate.data, layoutexcess);
  Plotly.newPlot(skymapDiv, skymap.data, layoutskymap);
}

setupPlots();
getData();

setInterval(getData, 5000);
