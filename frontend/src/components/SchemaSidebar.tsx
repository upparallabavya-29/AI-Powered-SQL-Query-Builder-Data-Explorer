import React, { useState } from "react";
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  RadioGroup,
  FormControlLabel,
  Radio,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  InputAdornment,
  Divider,
  CircularProgress
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import StorageIcon from "@mui/icons-material/Storage";
import TableIcon from "@mui/icons-material/TableChart";
import ColumnIcon from "@mui/icons-material/ViewColumn";
import SearchIcon from "@mui/icons-material/Search";
import UploadIcon from "@mui/icons-material/CloudUpload";
import AddIcon from "@mui/icons-material/Add";
import { useAppStore } from "../store/useAppStore";
import { apiService } from "../services/api";

export const SchemaSidebar: React.FC = () => {
  const {
    schemas,
    selectedSchemaId,
    selectSchemaId,
    fetchSchemas,
    loadingStates
  } = useAppStore();

  // Dialog State
  const [open, setOpen] = useState(false);
  const [schemaName, setSchemaName] = useState("");
  const [schemaType, setSchemaType] = useState<"sql" | "json">("sql");
  const [schemaContent, setSchemaContent] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  // Search State
  const [searchQuery, setSearchQuery] = useState("");

  const handleOpen = () => {
    setSchemaName("");
    setSchemaContent("");
    setSchemaType("sql");
    setUploadError("");
    setOpen(true);
  };

  const handleClose = () => {
    if (!uploading) setOpen(false);
  };

  const handleUpload = async () => {
    if (!schemaName.trim()) {
      setUploadError("Please provide a schema name.");
      return;
    }
    if (!schemaContent.trim()) {
      setUploadError("Please provide the schema content.");
      return;
    }

    setUploading(true);
    setUploadError("");
    try {
      await apiService.uploadSchema(schemaName, schemaType, schemaContent);
      await fetchSchemas(); // Refresh schemas
      setOpen(false);
    } catch (err: any) {
      setUploadError(err.message || "Failed to parse or initialize database sandbox.");
    } finally {
      setUploading(false);
    }
  };

  // Get active schema
  const activeSchema = schemas.find((s) => s.id === selectedSchemaId);

  // Filtered tables based on search
  const tables = activeSchema?.parsed_tables || {};
  const filteredTableNames = Object.keys(tables).filter((tName) =>
    tName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Box
      className="glass-panel"
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        p: 2,
        overflow: "hidden"
      }}
    >
      {/* App Logo/Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <StorageIcon sx={{ fontSize: 28, color: "var(--primary)" }} />
        <Typography variant="h5" sx={{ fontWeight: 800, letterSpacing: -0.5 }}>
          Athena<span style={{ color: "var(--secondary)" }}>.db</span>
        </Typography>
      </Box>

      {/* Database Schema Dropdown Selector */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
        Active Database Sandbox
      </Typography>
      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <FormControl fullWidth size="small">
          <Select
            value={selectedSchemaId || ""}
            onChange={(e) => selectSchemaId(e.target.value || null)}
            displayEmpty
            sx={{
              backgroundColor: "rgba(255, 255, 255, 0.02)",
              borderRadius: "8px"
            }}
          >
            <MenuItem value="" disabled>
              Select database schema...
            </MenuItem>
            {schemas.map((schema) => (
              <MenuItem key={schema.id} value={schema.id}>
                {schema.name} ({schema.schema_type.toUpperCase()})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button
          variant="contained"
          color="primary"
          onClick={handleOpen}
          sx={{ minWidth: "40px", p: 0, borderRadius: "8px" }}
          title="Upload New Schema"
        >
          <AddIcon />
        </Button>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Table Search Bar */}
      <TextField
        placeholder="Search tables..."
        size="small"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        fullWidth
        sx={{
          mb: 2,
          "& .MuiOutlinedInput-root": {
            borderRadius: "8px"
          }
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon size="small" sx={{ color: "text.secondary" }} />
            </InputAdornment>
          )
        }}
      />

      {/* Expandable Tables Tree */}
      <Box sx={{ flexGrow: 1, overflowY: "auto", pr: 0.5 }}>
        {loadingStates.schemas ? (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : filteredTableNames.length > 0 ? (
          filteredTableNames.map((tableName) => (
            <Accordion
              key={tableName}
              disableGutters
              elevation={0}
              sx={{
                background: "transparent",
                borderBottom: "1px solid rgba(255, 255, 255, 0.03)",
                "&:before": { display: "none" },
                "&.Mui-expanded": { margin: 0 }
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon sx={{ fontSize: 18 }} />}
                sx={{
                  px: 1,
                  py: 0.5,
                  minHeight: "unset",
                  "& .MuiAccordionSummary-content": {
                    margin: "8px 0",
                    display: "flex",
                    alignItems: "center",
                    gap: 1
                  }
                }}
              >
                <TableIcon sx={{ fontSize: 16, color: "var(--primary)" }} />
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {tableName}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ({tables[tableName].length} columns)
                </Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0, pl: 2, pb: 1 }}>
                <List dense sx={{ p: 0 }}>
                  {tables[tableName].map((col) => (
                    <ListItem key={col.name} sx={{ py: 0.25, px: 1 }}>
                      <ListItemIcon sx={{ minWidth: 20 }}>
                        <ColumnIcon sx={{ fontSize: 13, color: "text.secondary" }} />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                            <Typography variant="caption" sx={{ fontFamily: "var(--font-mono)", fontWeight: 500 }}>
                              {col.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: "10px" }}>
                              {col.type}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          ))
        ) : (
          <Box sx={{ textAlign: "center", mt: 6, px: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {selectedSchemaId ? "No matching tables found." : "Upload a schema to create your sandbox."}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Upload Schema Dialog Modal */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <UploadIcon color="primary" /> Upload Database Schema
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Provide your database schema as SQL DDL (containing standard `CREATE TABLE` instructions) or a formatted JSON structure. Athena will instantiate an isolated SQLite database and populate it with sample data.
          </Typography>

          {uploadError && (
            <Box
              sx={{
                p: 1.5,
                mb: 2,
                borderRadius: 1,
                bgcolor: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "var(--error)"
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: 500 }}>
                {uploadError}
              </Typography>
            </Box>
          )}

          <TextField
            label="Schema Name"
            placeholder="e.g. Retail Analytics, Healthcare Records"
            fullWidth
            size="small"
            value={schemaName}
            onChange={(e) => setSchemaName(e.target.value)}
            sx={{ mb: 2.5 }}
            disabled={uploading}
          />

          <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
            Schema Format Type
          </Typography>
          <RadioGroup
            row
            value={schemaType}
            onChange={(e) => setSchemaType(e.target.value as "sql" | "json")}
            sx={{ mb: 2.5 }}
          >
            <FormControlLabel value="sql" control={<Radio size="small" />} label="SQL DDL (.sql)" disabled={uploading} />
            <FormControlLabel value="json" control={<Radio size="small" />} label="JSON Schema (.json)" disabled={uploading} />
          </RadioGroup>

          <TextField
            label="Schema Code content"
            placeholder={
              schemaType === "sql"
                ? "CREATE TABLE customers (\n  id INTEGER PRIMARY KEY,\n  name VARCHAR(100)\n);\n\nCREATE TABLE orders (...);"
                : '{\n  "tables": {\n    "customers": {\n      "id": "INTEGER PRIMARY KEY",\n      "name": "VARCHAR(100)"\n    }\n  }\n}'
            }
            multiline
            rows={10}
            fullWidth
            value={schemaContent}
            onChange={(e) => setSchemaContent(e.target.value)}
            disabled={uploading}
            InputProps={{
              sx: { fontFamily: "var(--font-mono)", fontSize: "12px" }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={uploading} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={uploading}
            startIcon={uploading ? <CircularProgress size={16} color="inherit" /> : <UploadIcon />}
          >
            {uploading ? "Provisioning..." : "Initialize Database"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
export default SchemaSidebar;
