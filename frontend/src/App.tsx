import React, { useEffect } from "react";
import { Layout } from "./layouts/Layout";
import { useAppStore } from "./store/useAppStore";
import { Box, Typography } from "@mui/material";

function App() {
  const { fetchSchemas, errors } = useAppStore();

  // Load schemas when application mounts
  useEffect(() => {
    fetchSchemas();
  }, [fetchSchemas]);

  return (
    <Box sx={{ height: "100vh", width: "100vw", overflow: "hidden" }}>
      {/* Global general errors header banner */}
      {errors.general && (
        <Box
          sx={{
            position: "fixed",
            top: 16,
            left: "50%",
            transform: "translateX(-50%)",
            bgcolor: "var(--error)",
            color: "white",
            px: 3,
            py: 1,
            borderRadius: 2,
            boxShadow: 4,
            zIndex: 9999,
            display: "flex",
            alignItems: "center"
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {errors.general}
          </Typography>
        </Box>
      )}

      {/* Render layout grid */}
      <Layout />
    </Box>
  );
}

export default App;
