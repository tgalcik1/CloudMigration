import { createStore } from 'vuex';
import router from '../router/router';

export default createStore({
  state: {
    subjectId: localStorage.getItem('user') || null,
    selectedEcgDevice: localStorage.getItem('ecgDevice') || 'ecg1',
    isSidebarCollapsed: true,
    iotStatus: 'IoT disconnected'
  },
  mutations: {
    setSubjectId(state, subjectId) {
      state.subjectId = subjectId;
      if (subjectId) {
        localStorage.setItem('user', subjectId);
        window.api.send('toMain', { command: 'sign-in', subjectId: subjectId });
      } else {
        localStorage.removeItem('user');
      }
    },
    setSelectedEcgDevice(state, device) {
      state.selectedEcgDevice = device;
      if (device) {
        localStorage.setItem('ecgDevice', device);
        window.api.send('toMain', { command: 'set-ecg-device', device: device });
      } else {
        localStorage.removeItem('ecgDevice');
      }
    },
    toggleSidebar(state) {
      state.isSidebarCollapsed = !state.isSidebarCollapsed;
    },
    collapseSidebar(state) {
      state.isSidebarCollapsed = true;
    },
    setIotStatus(state, status) {
      state.iotStatus = status;
    }
  },
  actions: {
    login({ commit }, subjectId) {
      commit('setSubjectId', subjectId);
    },
    logout({ commit }) {
      commit('setSubjectId', null);
      commit('collapseSidebar');
      window.api.send('toMain', { command: 'disconnect-iot' });
      router.push('/signin');
    },
    selectEcgDevice({ commit }, device) {
      commit('setSelectedEcgDevice', device);
    },
    toggleSidebar({ commit }) {
      commit('toggleSidebar');
    },
    updateIotStatus({ commit }, status) {
      commit('setIotStatus', status);
    }
  }
});

// update iot status
if (window.api && window.api.receive) {
  window.api.receive('fromMain', (data) => {
    const store = require('./store').default;
    if (data.iotStatus) {
      store.dispatch('updateIotStatus', data.iotStatus);
    } else if (data.error) {
      store.dispatch('updateIotStatus', `Error: ${data.error}`);
    }
  });
}
