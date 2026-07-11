import os
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

# Retrieve environment configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class LlmClient:
    @staticmethod
    def _get_openai_client() -> OpenAI:
        """Instantiates the OpenAI client."""
        # Use a dummy key if none is provided to avoid SDK startup failures,
        # fallback behavior will handle actual execution if the key is missing.
        key = OPENAI_API_KEY if OPENAI_API_KEY else "mock_key_for_offline_testing"
        return OpenAI(api_key=key, base_url=OPENAI_API_BASE)

    @classmethod
    def generate_sql(cls, schema_name: str, parsed_tables: Dict[str, Any], prompt: str) -> str:
        """
        Generates a SQL query using the LLM based on the uploaded schema and user prompt.
        If no API key is available or the model API fails, falls back to a smart mock SQL generator.
        """
        # Format the schema context for the LLM
        schema_context = []
        for table_name, columns in parsed_tables.items():
            col_list = [f"{col['name']} ({col['type']})" for col in columns]
            schema_context.append(f"Table: {table_name}\nColumns: {', '.join(col_list)}")
        
        schema_context_str = "\n\n".join(schema_context)

        system_instruction = (
            "You are a Senior Data Engineer. Your task is to write a single, clean, valid SQLite SQL query "
            "to answer the user's question based ONLY on the database schema provided.\n\n"
            "Strict Constraints:\n"
            "1. ONLY use the tables and columns defined in the schema. DO NOT hallucinate tables or columns.\n"
            "2. Return ONLY the raw SQL query. Do NOT wrap the code in markdown blocks (e.g. do not write ```sql ... ```).\n"
            "3. Do NOT include any explanations, introduction, or text outside of the SQL statement.\n"
            "4. Only write SELECT statements. Multiple statements separated by semicolons are strictly forbidden.\n"
            "5. Ensure SQL joins use correct matching foreign keys.\n\n"
            f"Database Schema:\n{schema_context_str}"
        )

        user_content = f"Question: {prompt}\n\nSQLite SQL Query:"

        # If API key is missing, trigger the offline mock fallback immediately
        if not OPENAI_API_KEY:
            logger.info("OPENAI_API_KEY is not set. Using local mock SQL generator.")
            return cls._offline_mock_sql_generator(parsed_tables, prompt)

        try:
            client = cls._get_openai_client()
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                max_tokens=500
            )
            
            sql_out = response.choices[0].message.content.strip()
            # Clean up potential markdown formatting if the model ignored instructions
            if sql_out.startswith("```"):
                lines = sql_out.splitlines()
                # Remove first line if it contains triple backticks
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line if it contains triple backticks
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                sql_out = "\n".join(lines).strip()
            
            return sql_out

        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}. Falling back to mock generator.")
            return cls._offline_mock_sql_generator(parsed_tables, prompt)

    @classmethod
    def _offline_mock_sql_generator(cls, parsed_tables: Dict[str, Any], prompt: str) -> str:
        """
        Offline helper that generates a plausible SQLite query matching the tables
        and keywords in the prompt to allow testing and developer sandboxing without an API key.
        """
        p_lower = prompt.lower()
        tables = list(parsed_tables.keys())
        
        if not tables:
            return "SELECT 'No tables available in schema' AS error;"

        # Find which tables are mentioned or relevant
        matched_tables = [t for t in tables if t in p_lower]
        if not matched_tables:
            matched_tables = [tables[0]]  # Default to first table

        # Detect joins if multiple tables are matched
        if len(matched_tables) >= 2:
            t1, t2 = matched_tables[0], matched_tables[1]
            cols1 = [c["name"] for c in parsed_tables[t1]]
            cols2 = [c["name"] for c in parsed_tables[t2]]
            
            # Look for common join keys (e.g. customer_id, product_id, order_id)
            join_key = None
            for c in cols1:
                if c.endswith("_id") and c in cols2:
                    join_key = c
                    break
            
            if join_key:
                return (
                    f"SELECT *\n"
                    f"FROM {t1}\n"
                    f"JOIN {t2} ON {t1}.{join_key} = {t2}.{join_key}\n"
                    f"LIMIT 50;"
                )

        # Simple single-table query
        target_table = matched_tables[0]
        cols = [c["name"] for c in parsed_tables[target_table]]
        
        # Check for aggregations like "count", "total", "average", "sum"
        if "count" in p_lower:
            return f"SELECT COUNT(*) AS total_count FROM {target_table};"
        elif "revenue" in p_lower or "total" in p_lower:
            # Look for a price, total, or amount column
            numeric_col = next((c for c in cols if any(x in c for x in ["price", "total", "amount", "salary", "quantity"])), None)
            if numeric_col:
                return f"SELECT SUM({numeric_col}) AS total_value FROM {target_table};"
        
        # Default SELECT *
        return f"SELECT * FROM {target_table} LIMIT 50;"
