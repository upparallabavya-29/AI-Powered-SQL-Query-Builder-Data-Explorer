import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createTheme, ThemeProvider, CssBaseline } from "@mui/material";
import App from "./App.tsx";
import "./index.css";

// 1. Create a React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

// 2. Build a customized Dark Theme with Material UI
const darkTheme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#6366f1", // Indigo
      light: "#818cf8",
      dark: "#4f46e5",
      contrastText: "#ffffff"
    },
    secondary: {
      main: "#a855f7", // Violet
      light: "#c084fc",
      dark: "#7e22ce",
      contrastText: "#ffffff"
    },
    background: {
      default: "#070a13", // Deep space dark background
      paper: "#0d1426"    // Deep space paper panel
    },
    text: {
      primary: "#f3f4f6",
      secondary: "#9ca3af"
    },
    divider: "rgba(255, 255, 255, 0.08)",
    success: {
      main: "#10b981"
    },
    error: {
      main: "#ef4444"
    },
    warning: {
      main: "#f59e0b"
    }
  },
  typography: {
    fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 500 },
    h6: { fontWeight: 500 },
    button: { textTransform: "none", fontWeight: 600 }
  },
  shape: {
    borderRadius: 12
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "8px 16px",
          transition: "all 0.2s ease-in-out"
        },
        containedPrimary: {
          background: "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)",
          color: "#ffffff",
          boxShadow: "0 4px 14px 0 rgba(99, 102, 241, 0.3)",
          "&:hover": {
            filter: "brightness(1.1)",
            boxShadow: "0 6px 20px 0 rgba(99, 102, 241, 0.4)"
          }
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: "rgba(13, 20, 38, 0.65)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.37)"
        }
      }
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: "rgba(255, 255, 255, 0.03)",
          borderColor: "rgba(255, 255, 255, 0.08)",
          transition: "all 0.2s ease-in-out",
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: "rgba(255, 255, 255, 0.2)"
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: "#6366f1",
            borderWidth: 1
          }
        }
      }
    }
  }
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
