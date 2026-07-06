import React, { createContext, useState, useMemo, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { store } from './features/store';
import { getTheme } from './theme/theme';
import App from './App';

export const ColorModeContext = createContext({ toggleColorMode: () => {} });

function Main() {
  const [mode, setMode] = useState(() => {
    return localStorage.getItem('color-scheme') || 'dark';
  });

  const colorMode = useMemo(
    () => ({
      toggleColorMode: () => {
        setMode((prevMode) => {
          const nextMode = prevMode === 'light' ? 'dark' : 'light';
          localStorage.setItem('color-scheme', nextMode);
          document.documentElement.setAttribute('data-theme', nextMode);
          return nextMode;
        });
      },
    }),
    []
  );

  const theme = useMemo(() => getTheme(mode), [mode]);

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Provider store={store}>
      <Main />
    </Provider>
  </React.StrictMode>
);
