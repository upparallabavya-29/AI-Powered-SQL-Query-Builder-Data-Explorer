import React from "react";
import { Grid, Box, Container } from "@mui/material";
import { SchemaSidebar } from "../components/SchemaSidebar";
import { PromptPanel } from "../components/PromptPanel";
import { SqlEditor } from "../components/SqlEditor";
import { ResultsGrid } from "../components/ResultsGrid";
import { QueryHistorySidebar } from "../components/QueryHistorySidebar";

export const Layout: React.FC = () => {
  return (
    <Box
      sx={{
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
        backgroundColor: "var(--bg-main)",
        background: "radial-gradient(circle at 10% 20%, rgba(13, 20, 38, 0.4) 0%, rgba(7, 10, 19, 1) 90%)",
        display: "flex",
        flexDirection: "column"
      }}
    >
      <Container
        maxWidth={false}
        sx={{
          height: "100%",
          py: 3,
          px: { xs: 2, md: 4 },
          display: "flex",
          flexDirection: "column"
        }}
      >
        <Grid
          container
          spacing={3}
          sx={{
            flexGrow: 1,
            height: "100%",
            minHeight: 0 // Crucial for nested scroll containers to function
          }}
        >
          {/* Left Panel: Schema Tree (25% width) */}
          <Grid
            size={{ xs: 12, md: 3 }}
            sx={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              minHeight: { xs: "300px", md: "100%" }
            }}
          >
            <SchemaSidebar />
          </Grid>

          {/* Center Panel: Prompt + Editor + Results (50% width) */}
          <Grid
            size={{ xs: 12, md: 6 }}
            sx={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              gap: 3,
              overflowY: "auto",
              pr: 1
            }}
          >
            {/* 1. Prompt panel */}
            <Box className="glass-panel" sx={{ p: 2.5 }}>
              <PromptPanel />
            </Box>

            {/* 2. Monaco Editor panel */}
            <Box sx={{ flexShrink: 0 }}>
              <SqlEditor />
            </Box>

            {/* 3. Results grid */}
            <Box className="glass-panel" sx={{ p: 2.5, mb: 2 }}>
              <ResultsGrid />
            </Box>
          </Grid>

          {/* Right Panel: History/Saved Queries (25% width) */}
          <Grid
            size={{ xs: 12, md: 3 }}
            sx={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              minHeight: { xs: "350px", md: "100%" }
            }}
          >
            <QueryHistorySidebar />
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
export default Layout;
