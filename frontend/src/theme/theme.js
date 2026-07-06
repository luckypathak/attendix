import { createTheme } from '@mui/material/styles';

export const getTheme = (mode) => {
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isDark ? '#9d4edd' : '#6200ee',
        light: isDark ? '#c77dff' : '#9c27b0',
        dark: isDark ? '#7b2cbf' : '#3700b3',
      },
      secondary: {
        main: isDark ? '#00f5d4' : '#03dac6',
        light: isDark ? '#80ffdb' : '#66fff6',
        dark: isDark ? '#00bbf9' : '#018786',
      },
      background: {
        default: isDark ? '#0a0915' : '#f8f9fa',
        paper: isDark ? '#121124' : '#ffffff',
        glass: isDark ? 'rgba(18, 17, 36, 0.7)' : 'rgba(255, 255, 255, 0.7)',
      },
      text: {
        primary: isDark ? '#f8f9fa' : '#212529',
        secondary: isDark ? '#adb5bd' : '#6c757d',
      },
      divider: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
    },
    typography: {
      fontFamily: '"Outfit", "Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: { fontSize: '2.5rem', fontWeight: 700 },
      h2: { fontSize: '2rem', fontWeight: 700 },
      h3: { fontSize: '1.75rem', fontWeight: 600 },
      h4: { fontSize: '1.5rem', fontWeight: 600 },
      h5: { fontSize: '1.25rem', fontWeight: 500 },
      h6: { fontSize: '1rem', fontWeight: 500 },
      body1: { fontSize: '0.95rem', lineHeight: 1.6 },
      body2: { fontSize: '0.85rem', lineHeight: 1.5 },
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            backgroundImage: 'none',
            boxShadow: isDark 
              ? '0 8px 32px 0 rgba(0, 0, 0, 0.37)' 
              : '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
            border: isDark 
              ? '1px solid rgba(255, 255, 255, 0.05)' 
              : '1px solid rgba(255, 255, 255, 0.18)',
            backdropFilter: 'blur(10px)',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: isDark 
                ? '0 12px 40px 0 rgba(0, 0, 0, 0.5)' 
                : '0 12px 40px 0 rgba(31, 38, 135, 0.15)',
            }
          }
        }
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            textTransform: 'none',
            fontWeight: 600,
            padding: '8px 16px',
          },
          containedPrimary: {
            background: isDark 
              ? 'linear-gradient(135deg, #7b2cbf 0%, #9d4edd 100%)' 
              : 'linear-gradient(135deg, #6200ee 0%, #9c27b0 100%)',
            boxShadow: 'none',
            '&:hover': {
              boxShadow: 'none',
              filter: 'brightness(1.1)',
            }
          }
        }
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 8,
            }
          }
        }
      }
    }
  });
};
