const { ipcMain } = require('electron');
const path = require('path');
const os = require('os');
require('dotenv').config();
const { spawn, exec } = require('child_process');
const net = require('net');
import { app, protocol, BrowserWindow, screen } from 'electron';
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib';
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer';
const isDevelopment = process.env.NODE_ENV !== 'production';
const awsIot = require('aws-iot-device-sdk');
const fs = require('fs');
// import axios from 'axios'; // will be used for posting survey results to db

let device = null;
let subjectId = null;
let currentTask = null;
let currentEcgDevice = null;
let scriptPath;

if (isDevelopment) {
  scriptPath = path.join(__dirname, '..', 'public', 'scripts');
} else {
  scriptPath = path.join(process.resourcesPath, 'scripts');
}

const EYE_PIPE_NAME_PATH = '\\\\.\\pipe\\eye_pipe';
const SENSOR_PIPE_NAME_PATH = '\\\\.\\pipe\\sensor_pipe';

let sensorConnected = false;
let eyeConnected = false;

const EYE_EXIT_CODES = Object.freeze({
  0: "Eye tracker disconnected",
  1: "Eye tracker setup interrupted", //"Invalid eye tracker arguments",
  2: "Eye tracker not found",
  3: "Failed to open eye tracker pipe",
  4: "Connection to eye tracker pipe unexpectedly closed",
  5: "Eye tracker unexpectedly disconnected",
  99: "Unhandled eye tracker exception"
});

const ARDUINO_EXIT_CODES = Object.freeze({
  0: "ECG disconnected",
  1: "ECG setup interrupted", //"Invalid ECG arguments",
  2: "Could not open COM port",
  3: "Failed to open ECG pipe",
  4: "Connection to ECG pipe unexpectedly closed",
  5: "Failed to open ECG serial port",
  6: "Failed to find ECG device within acceptable timeout period",
  99: "Unhandled ECG exception"
}); 

const MOVESENSE_EXIT_CODES = Object.freeze({
    0: "ECG disconnected",
    1: "ECG setup interrupted", //"Invalid ECG arguments",
    2: "ECG sensor end with given serial not found",
    3: "Failed to open ECG pipe",
    4: "Connection to ECG pipe unexpectedly closed",
    5: "Failed to open ECG serial port",
    99: "Unhandled ECG exception"
});

protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true } }
]);

async function createWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  const win = new BrowserWindow({
    autoHideMenuBar: true,
    width: width,
    height: height,
    webPreferences: {
      nodeIntegration: process.env.ELECTRON_NODE_INTEGRATION,
      contextIsolation: !process.env.ELECTRON_NODE_INTEGRATION,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  if (process.env.WEBPACK_DEV_SERVER_URL) {
    await win.loadURL(process.env.WEBPACK_DEV_SERVER_URL);
    if (!process.env.IS_TEST) win.webContents.openDevTools();
  } else {
    createProtocol('app');
    win.loadURL('app://./index.html');
  }
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    disconnectIot();
    localStorage.clear();
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on('ready', async () => {
  if (isDevelopment && !process.env.IS_TEST) {
    try {
      await installExtension(VUEJS3_DEVTOOLS);
    } catch (e) {
      console.error('Vue Devtools failed to install:', e.toString());
    }
  }
  await createWindow();
  setupPipeServer(EYE_PIPE_NAME_PATH, 'eye');
  setupPipeServer(SENSOR_PIPE_NAME_PATH, 'sensor');
});

if (isDevelopment) {
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        localStorage.clear();
        app.quit();
      }
    });
  } else {
    process.on('SIGTERM', () => {
      localStorage.clear();
      app.quit();
    });
  }
}

// IPC event listeners - handle commands from the renderer process
ipcMain.on('toMain', (event, args) => {
  console.log('[IPC MAIN]', args);
  switch (args.command) {
    case 'sign-in':
      subjectId = args.subjectId;
      console.log('[IPC MAIN] sign-in api call for subjectId:', args.subjectId);
      break;

    case 'set-ecg-device':
      currentEcgDevice = args.device;
      break;

    case 'start-data-collection':
      console.log(`[IPC MAIN] starting data collection processes for subjectId "${args.subjectId}" using ${args.device} ecg device, performing task "${args.task}"...`);
      startDataCollection(args.device, event);
      break;

    case 'stop-data-collection':
      console.log('[IPC MAIN] stopping data collection...');
      stopDataCollection(event);
      break;

    case 'update-task':
      currentTask = args.task;
      break;

    case 'setup-iot':
      console.log('[IPC MAIN] setting up IoT...');
      setupIot(event);
      break;

    case 'setup-eye-tracker':
      console.log('[IPC MAIN] setting up eye tracker...');
      setupEyeTracker(event);
      break;

    case 'setup-sensor':
      console.log('[IPC MAIN] setting up ECG sensor...');
      setupSensor(currentEcgDevice, event);
      break;

    case 'disconnect-iot':
      console.log('[IPC MAIN] disconnecting IoT...');
      disconnectIot(event);
      break;

    case 'send-iot-message':
      console.log('[IPC MAIN] sending IoT message...');
      sendIotMessage(args.topic, args.message, event);
      break;

    default:
      console.log('[IPC MAIN] no command given');
  }
});

ipcMain.on('survey', (event, args) => {
  console.log('[IPC MAIN] survey responses received: ', args);
});

function setupEyeTracker(event) {
  const recordEyePath = path.join(scriptPath, 'record_eye_for_exe.exe');
  const eyeProcess = spawn('cmd.exe', ['/C', recordEyePath, EYE_PIPE_NAME_PATH]);

  console.log('Connecting eye tracker...');
  event.reply('fromMain', { eyeStatus: 'Connecting eye tracker...' });

  eyeProcess.stdout.on('data', (data) => {
    console.log(`[RECORD_EYE] stdout: ${data}`);
    // event.reply('fromMain', { eyeStatus: `Record_eye output: ${data.toString()}` });
  });

  eyeProcess.stderr.on('data', (data) => {
    console.error(`[RECORD_EYE] stderr: ${data}`);
    // event.reply('fromMain', { eyeError: `Record_eye error: ${data.toString()}` });
  });

  eyeProcess.on('close', (code) => {
    console.log(`[RECORD_EYE] ${EYE_EXIT_CODES[code]}`);
    eyeConnected = false;
    event.reply('fromMain', { eyeStatus: `${EYE_EXIT_CODES[code]}` });
  });

  return eyeProcess;
}

function setupSensor(ecgDevice, event) {
  let filename;
  let sensorArgs;
  let sensorExitCodes;

  console.log(ecgDevice);

  switch (ecgDevice) {
    case 'arduino':
      filename = 'record_arduino_sensor_for_exe.exe';
      const COM_PORT = 'COM4'; // hardcoded, need to identify arduino com port dynamically
      sensorArgs = COM_PORT;
      sensorExitCodes = ARDUINO_EXIT_CODES;
      break;
    case 'movesense':
      filename = 'record_movesense_sensor_for_exe.exe';
      const END_OF_SERIAL = '234530000211'; // hardcoded (taken from config.bat), need to identify movesense serial dynamically
      sensorArgs = END_OF_SERIAL;
      sensorExitCodes = MOVESENSE_EXIT_CODES;
      break;
    default:
      console.error('[IPC MAIN] invalid device type');
      event.reply('fromMain', { sensorError: 'Invalid device type' });
      return null;
  }

  const recordSensorPath = path.join(scriptPath, filename);
  const sensorProcess = spawn('cmd.exe', ['/C', recordSensorPath, sensorArgs, SENSOR_PIPE_NAME_PATH]);

  console.log('Connecting ECG sensor...');
  event.reply('fromMain', { sensorStatus: 'Connecting ECG sensor...' });

  sensorProcess.stdout.on('data', (data) => {
    console.log(`[RECORD_SENSOR] stdout: ${data}`);
    // event.reply('fromMain', { sensorStatus: `Record_sensor output: ${data.toString()}` });
  });

  sensorProcess.stderr.on('data', (data) => {
    console.error(`[RECORD_SENSOR] stderr: ${data}`);
    // event.reply('fromMain', { sensorError: `Record_sensor error: ${data.toString()}` });
  });

  sensorProcess.on('close', (code) => {
    console.log(`${sensorExitCodes[code]}`);
    sensorConnected = false;
    event.reply('fromMain', { sensorStatus: `${sensorExitCodes[code]}` });
  });

  return sensorProcess;
}

function startDataCollection(device, event) {
  let eyeProcess;
  if (!eyeConnected){
    eyeProcess = setupEyeTracker(event);
  }

  let sensorProcess;
  if (!sensorConnected){
    sensorProcess = setupSensor(device, event);
  }

  if ((!sensorConnected && !sensorProcess) || (!eyeConnected && !eyeProcess)) {
    return;
  }

  ipcMain.once('stop-data-collection', () => {
    if (eyeProcess) eyeProcess.kill();
    if (sensorProcess) sensorProcess.kill();
    stopDataCollection();
    event.reply('fromMain', { sensorStatus: 'ECG disconnected', eyeStatus: 'Eye tracker disconnected' });
  });
}

function stopDataCollection(event) {
  exec('taskkill /f /im record_eye_for_exe.exe');
  exec('taskkill /f /im record_arduino_sensor_for_exe.exe');
  exec('taskkill /f /im record_movesense_sensor_for_exe.exe');
  event.reply('fromMain', { sensorStatus: 'ECG disconnected', eyeStatus: 'Eye tracker disconnected' });
}

function setupPipeServer(pipeName, type) {
  const server = net.createServer((stream) => {
    stream.on('data', (data) => {
      //console.log(`[${type.toUpperCase()} PIPE] ${data}`);
      
      // update device status on first data reception
      if (type === 'sensor' && !sensorConnected)
      {
        sensorConnected = true;
        BrowserWindow.getAllWindows().forEach(win => {
          win.webContents.send('fromMain', { sensorStatus: 'ECG connected' });
        });
      }
      if (type === 'eye' && !eyeConnected)
      {
        eyeConnected = true;
        BrowserWindow.getAllWindows().forEach(win => {
          win.webContents.send('fromMain', { eyeStatus: 'Eye tracker connected' });
        });
      }

      // parse the data into valid JSON
      // note - sometimes it reads more than one entry from the pipe at a time so i handled it below by splitting it first
      const decoder = new TextDecoder('utf-8');
      let jsonString = decoder.decode(data);
      jsonString = jsonString.replace(/NaN/g, 0);
      let objects = jsonString.split(/(?<=})\s*(?={)/);
      
      objects.forEach(objString => {
        let validJsonString = objString.replace(/'/g, '"');
        let jsonData = JSON.parse(validJsonString);

        // publish data to AWS IoT
        if (type === 'eye')
        {
          let transformedData = {
            timestamp: jsonData.Timestamp || 'null timestamp',
            computer_name: '',
            user_id: subjectId || 'null subjectId',
            game_type: currentTask || 'null task',
            gaze_x: jsonData.Gaze_X || 0,
            gaze_y: jsonData.Gaze_Y || 0,
            pupil_left: jsonData.Pupil_left || 0,
            pupil_right: jsonData.Pupil_right || 0
          };
          //console.log(transformedData)
          sendIotMessage('sensor/eye', transformedData);
        }
        else if (type === 'sensor')
        {
          // movesense ecg
          if (currentEcgDevice === 'movesense')
          {
            // heart data
            if (jsonData.data_type === 'Heart_Data')
            {
              let transformedData = {
                timestamp: jsonData.Timestamp || 'null timestamp',
                computer_name: '',
                user_id: subjectId || 'null subjectId',
                game_type: currentTask || 'null task',
                ecg_data: jsonData.ecg_data || 0,
              };
              sendIotMessage('sensor/ecg', transformedData);
            }
            // IMU9 data
            else if (jsonData.data_type === 'IMU9') {
              let transformedData = {
                timestamp: jsonData.Timestamp || 'null timestamp',
                computer_name: '',
                user_id: subjectId || 'null subjectId',
                game_type: currentTask || 'null task',
                acc_x: jsonData.acc_x || 0,
                acc_y: jsonData.acc_y || 0,
                acc_z: jsonData.acc_z || 0,
                gyro_x: jsonData.gyro_x || 0,
                gyro_y: jsonData.gyro_y || 0,
                gyro_z: jsonData.gyro_z || 0,
                magn_x: jsonData.magn_x || 0,
                magn_y: jsonData.magn_y || 0,
                magn_z: jsonData.magn_z || 0
              };
              sendIotMessage('sensor/imu9', transformedData);
            }
          }
          // arduino ecg
          else
          {
            let transformedData = {
              timestamp: jsonData.Timestamp || 'null timestamp',
              computer_name: '',
              user_id: subjectId || 'null subjectId',
              game_type: currentTask || 'null task',
              ecg_data: jsonData.ecg_data || 0,
            };

            // get arduino snr from ecg_data and pass to renderer
            let snr = jsonData.snr_values;
            BrowserWindow.getAllWindows().forEach(win => {
              win.webContents.send('fromMain', { signalStrength: snr });
            });

            //console.log(transformedData)
            sendIotMessage('sensor/ecg', transformedData);
          }
        }
      })
    });

    stream.on('end', () => {
      if (type === 'sensor'){
        sensorConnected = false;
        BrowserWindow.getAllWindows().forEach(win => {
          win.webContents.send('fromMain', { sensorStatus: 'ECG disconnected' });
        });
      }
      if (type === 'eye'){
        eyeConnected = false;
        BrowserWindow.getAllWindows().forEach(win => {
          win.webContents.send('fromMain', { eyeStatus: 'Eye tracker disconnected' });
        });
      } 
      console.log(`[${type.toUpperCase()} PIPE] End of data`);
    });
  });

  server.listen(pipeName, () => {
    console.log(`[IPC MAIN] ${type} pipe server listening on ${pipeName}`);
  });

  server.on('error', (err) => {
    console.error(`[IPC MAIN] ${type} pipe server error:`, err);
    BrowserWindow.getAllWindows().forEach(win => {
      win.webContents.send('fromMain', { [`${type}PipeError`]: err.message });
    });
  });
}

function setupIot(event) {
  device = awsIot.device({
    keyPath: process.env.AWS_IOT_KEY_PATH,
    certPath: process.env.AWS_IOT_CERT_PATH,
    caPath: process.env.AWS_IOT_CA_PATH,
    clientId: process.env.AWS_IOT_CLIENT_ID,
    host: process.env.AWS_IOT_HOST,
    debug: true
  });

  device.on('connect', function() {
    console.log('[IOT] Connected to AWS IoT');
    event.reply('fromMain', { iotStatus: 'IoT connected' });
  });

  device.on('message', function(topic, payload) {
    console.log('[IOT] Message received:', topic, payload.toString());
  });

  device.on('error', function(error) {
    console.error('[IoT] Error:', error);
  });

  device.on('close', function() {
    console.log('[IOT] Connection closed');
    event.reply('fromMain', { iotStatus: 'IoT connection closed' });
  });

  device.on('reconnect', function() {
    console.log('[IOT] Reconnecting...');
    event.reply('fromMain', { iotStatus: 'IoT reconnecting...' });
  });

  device.on('offline', function() {
    console.log('[IOT] Offline');
    event.reply('fromMain', { iotStatus: 'IoT disconnected' });
  });
}

function disconnectIot(event) {
  if (device) {
    device.end(true, () => {
      console.log('[IOT] Disconnected from AWS IoT');
      event.reply('fromMain', { iotStatus: 'IoT disconnected' });
      device = null;
    });
  } else {
    console.log('[IOT] Already disconnected from IoT');
  }
}

function sendIotMessage(topic, message) {
  if (device) {
    //console.log('[IOT] Sending message: ', message);
    device.publish(topic, JSON.stringify(message), (err) => {
      if (err) {
        console.error('[IOT] Publish error:', err);
      } else {
        //console.log('[IOT] Message sent to topic:', topic);
      }
    });
  } else {
    console.error('[IOT] IoT device is not connected');
  }
}
