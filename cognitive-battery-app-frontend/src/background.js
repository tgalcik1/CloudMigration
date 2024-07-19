const { ipcMain } = require('electron');
const path = require('path');
const os = require('os');
require('dotenv').config();
const { spawn, exec } = require('child_process');
import { app, protocol, BrowserWindow, screen } from 'electron';
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib';
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer';
const isDevelopment = process.env.NODE_ENV !== 'production';
const awsIot = require('aws-iot-device-sdk');
const fs = require('fs');

let device = null;

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
  createWindow();
});

if (isDevelopment) {
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        app.quit();
      }
    });
  } else {
    process.on('SIGTERM', () => {
      app.quit();
    });
  }
}

ipcMain.on('toMain', (event, args) => {
  console.log('[IPC MAIN]', args);
  switch (args.command) {
    case 'sign-in':
      console.log('sign-in api call for subjectId:', args.subjectId);
      break;

    case 'set-ecg-device':
      console.log('make api call');
      break;

    case 'start-data-collection':
      console.log(`starting data collection processes for subjectId "${args.subjectId}" using ${args.device} ecg device, performing task "${args.task}"...`);
      startDataCollection(args.subjectId, args.device, args.task, event);
      break;

    case 'stop-data-collection':
      console.log('stopping data collection...');
      stopDataCollection(event);
      break;

    case 'update-task':
      console.log('updating task...');
      break;

    case 'setup-iot':
      console.log('setting up IoT...');
      setupIot(event);
      break;

    case 'disconnect-iot':
      console.log('disconnecting IoT...');
      disconnectIot(event);
      break;

    case 'send-iot-message':
      console.log('sending IoT message...');
      sendIotMessage(args.topic, args.message, event);
      break;

    default:
      console.log('no command given');
  }
});

ipcMain.on('survey', (event, args) => {
  console.log('[IPC MAIN] survey responses received: ', args);
});

function startDataCollection(subjectId, device, task, event) {
  let scriptPath;

  if (isDevelopment) {
    scriptPath = path.join(__dirname, '..', 'public', 'scripts');
  } else {
    scriptPath = path.join(process.resourcesPath, 'scripts');
  }

  let filename;

  switch (device) {
    case 'arduino':
      filename = 'record_sensor_for_exe.exe';
      break;
    case 'movesense':
      filename = 'record_movesense_sensor_for_exe.exe';
      break;
    default:
      console.error('[IPC MAIN] invalid device type');
      event.reply('fromMain', { sensorError: 'Invalid device type' });
      return;
  }

  const COMPUTER_NAME = os.hostname();
  const END_OF_SERIAL = '234530000211'; // taken from config.bat

  console.log('[IPC MAIN] computer name:', COMPUTER_NAME);

  const recordEyePath = path.join(scriptPath, 'record_eye_for_exe.exe');
  const eyeProcess = spawn('cmd.exe', ['/K', recordEyePath, COMPUTER_NAME, task, subjectId]);

  eyeProcess.stdout.on('data', (data) => {
    console.log(`[IPC MAIN] record_eye stdout: ${data}`);
    event.reply('fromMain', { eyeStatus: `Record_eye output: ${data.toString()}` });
  });

  eyeProcess.stderr.on('data', (data) => {
    console.error(`[IPC MAIN] record_eye stderr: ${data}`);
    event.reply('fromMain', { eyeError: `Record_eye error: ${data.toString()}` });
  });

  eyeProcess.on('close', (code) => {
    console.log(`record_eye process exited with code ${code}`);
    event.reply('fromMain', { eyeStatus: `Record_eye exited with code ${code}` });
  });

  const recordSensorPath = path.join(scriptPath, filename);
  const sensorProcess = spawn('cmd.exe', ['/K', recordSensorPath, END_OF_SERIAL, COMPUTER_NAME, task, subjectId]);

  sensorProcess.stdout.on('data', (data) => {
    console.log(`record_sensor stdout: ${data}`);
    event.reply('fromMain', { sensorStatus: `Record_sensor output: ${data.toString()}` });
  });

  sensorProcess.stderr.on('data', (data) => {
    console.error(`record_sensor stderr: ${data}`);
    event.reply('fromMain', { sensorError: `Record_sensor error: ${data.toString()}` });
  });

  sensorProcess.on('close', (code) => {
    console.log(`record_sensor process exited with code ${code}`);
    event.reply('fromMain', { sensorStatus: `Record_sensor exited with code ${code}` });
  });

  ipcMain.once('stop-data-collection', () => {
    eyeProcess.kill();
    sensorProcess.kill();
    event.reply('fromMain', { sensorStatus: 'Stopped', eyeStatus: 'Stopped' });
  });
}

function stopDataCollection(event) {
  exec('taskkill /f /im record_eye_for_exe.exe');
  exec('taskkill /f /im record_sensor_for_exe.exe');
  exec('taskkill /f /im record_movesense_sensor_for_exe.exe');
  event.reply('fromMain', { status: 'data collection stopped' });
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
    console.log('Connected to AWS IoT');
    event.reply('fromMain', { iotStatus: 'IoT connected' });
  });

  device.on('message', function(topic, payload) {
    console.log('message received:', topic, payload.toString());
  });

  device.on('error', function(error) {
    console.error('Error:', error);
  });

  device.on('close', function() {
    console.log('Connection closed');
    event.reply('fromMain', { iotStatus: 'IoT connection closed' });
  });

  device.on('reconnect', function() {
    console.log('Reconnecting');
    event.reply('fromMain', { iotStatus: 'IoT reconnecting...' });
  });

  device.on('offline', function() {
    console.log('Offline');
    event.reply('fromMain', { iotStatus: 'IoT disconnected' });
  });
}

function disconnectIot(event) {
  if (device) {
    device.end(true, () => {
      console.log('Disconnected from AWS IoT');
      event.reply('fromMain', { iotStatus: 'IoT disconnected' });
      device = null;
    });
  } else {
    console.log('Already disconnected from IoT');
  }
}

function sendIotMessage(topic, message, event) {
  if (device) {
    device.publish(topic, JSON.stringify(message), (err) => {
      if (err) {
        console.error('Publish error:', err);
        // event.reply('fromMain', { iotStatus: 'Failed to send IoT message', error: err });
      } else {
        console.log('Message sent to topic:', topic);
        // event.reply('fromMain', { iotStatus: 'IoT message sent', topic: topic, message: message });
      }
    });
  } else {
    console.error('IoT device is not connected');
    event.reply('fromMain', { iotStatus: 'IoT disconnected' });
  }
}
