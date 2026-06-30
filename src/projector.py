"""
projector.py — Applies a runtime config to reshape CanonicalCandidate output.

Config format (all keys optional):
{
  "fields": [
    {
      "path":      "full_name",          # key in output dict
      "from":      "full_name",          # dot-path into canonical record (default = path)
      "type":      "string",             # "string" | "string[]" | "number"  (informational)
      "required":  true,                 # raises ProjectionError if missing + on_missing="error"
      "normalize": "E164" | "canonical"  # optional post-projection normalization
    },
    ...
  ],
  "include_confidence": true,   # append overall_confidence to output
  "include_provenance": false,  # append provenance list to output
  "on_missing": "null"          # "null" | "omit" | "error"
}

Path syntax:
  "full_name"         -> scalar field
  "emails[0]"         -> first element of list
  "skills[].name"     -> pluck "name" from each element in skills list
  "location.city"     -> nested field
"""

import json
import re
from pathlib import Path
from typing import Any

from src.models import CanonicalCandidate
from src.normaliser.phones import normalize_phone
from src.normaliser.skills import normalize_skill


class ProjectionError(ValueError):
    """Raised when a required field is missing and on_missing='error'."""


class Projector:

    def project(self, candidate: CanonicalCandidate, config: dict | None = None, ) -> dict:
        if not config:
            # No config -> dump full canonical record as JSON-compatible dict
            return json.loads(candidate.model_dump_json())

        record = json.loads(candidate.model_dump_json())
        on_missing: str = config.get("on_missing", "null")
        fields_cfg: list[dict] = config.get("fields", [])

        output: dict[str, Any] = {}

        for field_def in fields_cfg:
            path: str = field_def["path"]
            from_path: str = field_def.get("from", path)
            required: bool = field_def.get("required", False)
            normalizer: str | None = field_def.get("normalize")

            value = self._resolve(record, from_path)

            # Apply post-projection normalization
            if value is not None and normalizer:
                value = self._normalize_value(value, normalizer)

            # Handle missing
            if value is None:
                if required and on_missing == "error":
                    raise ProjectionError(f"Required field '{path}' (from '{from_path}') is missing.")
                
                if on_missing == "omit":
                    continue
                # on_missing == "null" -> include with null
                output[path] = None
            
            else:
                output[path] = value

        if config.get("include_confidence", False):
            output["overall_confidence"] = candidate.overall_confidence

        if config.get("include_provenance", False):
            output["provenance"] = record.get("provenance", [])

        return output

    @staticmethod
    def _resolve(record: dict, path: str) -> Any:
        """
        Resolve a path expression against a dict record.

        Supports chained tokens, e.g.:
          "location.city"            -> nested dict access
          "emails[0]"                -> index into list
          "education[0].institution" -> index into list, then nested access
          "skills[].name"            -> pluck attr from every list item
        """
        return Projector._resolve_tokens(record, path.split("."))

    @staticmethod
    def _resolve_tokens(val: Any, tokens: list[str]) -> Any:
        if not tokens:
            return val

        token, rest = tokens[0], tokens[1:]

        # key[] pluck remaining path from every item in the list
        match = re.fullmatch(r"(\w+)\[]", token)
        if match:
            key = match.group(1)
            lst = val.get(key) if isinstance(val, dict) else None
            lst = lst or []

            results = [Projector._resolve_tokens(item, rest) for item in lst]
            return [result for result in results if result is not None] if rest else results

        # key[n] -> index into list, continue resolving the rest
        match = re.fullmatch(r"(\w+)\[(\d+)]", token)
        if match:
            key, idx = match.group(1), int(match.group(2))
            lst = val.get(key) if isinstance(val, dict) else None
            lst = lst or []

            item = lst[idx] if idx < len(lst) else None
            return Projector._resolve_tokens(item, rest) if item is not None else None

        # plain key
        nxt = val.get(token) if isinstance(val, dict) else None
        return Projector._resolve_tokens(nxt, rest)

    @staticmethod
    def _normalize_value(value: Any, normalizer: str) -> Any:
        norm = normalizer.lower()

        if norm == "e164":
            if isinstance(value, list):
                return [normalize_phone(v) for v in value if normalize_phone(v)]
            return normalize_phone(str(value))

        if norm == "canonical":
            if isinstance(value, list):
                return [normalize_skill(v) for v in value if normalize_skill(v)]
            return normalize_skill(str(value))

        return value

    @staticmethod
    def load_config(path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))
