import React from "react";
import MonacoEditor from "@monaco-editor/react";
import { Box, Typography } from "@mui/material";
import { Code as CodeIcon } from "@mui/icons-material";
import { useAppStore } from "../store/useAppStore";

export const SqlEditor: React.FC = () => {
  const { generatedSql, setGeneratedSql, selectedSchemaId } = useAppStore();

  const handleEditorChange = (value: string | undefined) => {
    setGeneratedSql(value || "");
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "8px",
        overflow: "hidden",
        backgroundColor: "#1e1e1e" // Editor dark background
      }}
    >
      {/* Editor Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          px: 2,
          py: 1,
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          backgroundColor: "rgba(255, 255, 255, 0.02)"
        }}
      >
        <CodeIcon sx={{ fontSize: 16, color: "var(--primary)" }} />
        <Typography variant="caption" sx={{ fontWeight: 600, color: "text.secondary", textTransform: "uppercase", letterSpacing: 0.5 }}>
          SQL Editor (Editable)
        </Typography>
      </Box>

      {/* Monaco Editor Wrapper */}
      <Box sx={{ flexGrow: 1, height: "240px" }}>
        <MonacoEditor
          height="100%"
          language="sql"
          theme="vs-dark"
          value={generatedSql}
          onChange={handleEditorChange}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: "var(--font-mono)",
            lineNumbers: "on",
            roundedSelection: true,
            scrollBeyondLastLine: false,
            readOnly: !selectedSchemaId,
            automaticLayout: true,
            padding: { top: 10, bottom: 10 }
          }}
        />
      </Box>
    </Box>
  );
};
export default SqlEditor;
