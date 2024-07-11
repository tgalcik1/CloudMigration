const { ipcMain } = require('electron');
const path = require('path');
const os = require('os');
const { spawn, exec } = require('child_process');
import { app, protocol, BrowserWindow } from 'electron';
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib';
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer';
const isDevelopment = process.env.NODE_ENV !== 'production';
const net = require('net');

protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true } }
]);

async function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
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
      updateTask(args.task);
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
      event.reply('fromMain', { error: 'invalid device type' });
      return;
  }

  const COMPUTER_NAME = os.hostname();
  const END_OF_SERIAL = '234530000211'; // taken from config.bat

  console.log('[IPC MAIN] computer name:', COMPUTER_NAME);

  const recordEyePath = path.join(scriptPath, 'record_eye_for_exe.exe');
  const eyeProcess = spawn('cmd.exe', ['/K', recordEyePath, COMPUTER_NAME, task, subjectId]);

  eyeProcess.stdout.on('data', (data) => {
    console.log(`[IPC MAIN] record_eye stdout: ${data}`);
    event.reply('fromMain', { status: `record_eye output: ${data.toString()}` });
  });

  eyeProcess.stderr.on('data', (data) => {
    console.error(`[IPC MAIN] record_eye stderr: ${data}`);
    event.reply('fromMain', { error: `record_eye error: ${data.toString()}` });
  });

  eyeProcess.on('close', (code) => {
    console.log(`record_eye process exited with code ${code}`);
    event.reply('fromMain', { status: `record_eye exited with code ${code}` });
  });

  const recordSensorPath = path.join(scriptPath, filename);
  const sensorProcess = spawn('cmd.exe', ['/K', recordSensorPath, END_OF_SERIAL, COMPUTER_NAME, task, subjectId]);

  sensorProcess.stdout.on('data', (data) => {
    console.log(`record_sensor stdout: ${data}`);
    event.reply('fromMain', { status: `record_sensor output: ${data.toString()}` });
  });

  sensorProcess.stderr.on('data', (data) => {
    console.error(`record_sensor stderr: ${data}`);
    event.reply('fromMain', { error: `record_sensor error: ${data.toString()}` });
  });

  sensorProcess.on('close', (code) => {
    console.log(`record_sensor process exited with code ${code}`);
    event.reply('fromMain', { status: `record_sensor exited with code ${code}` });
  });

  ipcMain.once('stop-data-collection', () => {
    eyeProcess.kill();
    sensorProcess.kill();
    event.reply('fromMain', { status: 'data collection stopped' });
  });
}

function stopDataCollection(event) {
  exec('taskkill /f /im record_eye_for_exe.exe');
  exec('taskkill /f /im record_sensor_for_exe.exe');
  exec('taskkill /f /im record_movesense_sensor_for_exe.exe');
  event.reply('fromMain', { status: 'data collection stopped' });
}

function updateTask(newTask) {
  const client = new net.Socket();
  client.connect(50501, 'localhost', () => {
    console.log('connected to control server');
    client.write(newTask);
  });

  client.on('data', (data) => {
    console.log(`received: ${data}`);
  });

  client.on('close', () => {
    console.log('connection closed');
  });
}
