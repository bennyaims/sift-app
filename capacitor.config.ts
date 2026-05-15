import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.sift.labourhire',
  appName: 'SIFT',
  webDir: 'dist',
  server: {
    url: 'https://sift-app.streamlit.app', // Your Streamlit URL
    cleartext: false
  }
};

export default config;