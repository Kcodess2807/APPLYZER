#Agent01 – fetches job listings from various sources.

from __future__ import annotations
from typing import Any
import pandas as pd
from app.agents.base import AgentResult, BaseAgent
from app.agents.constants import CSV_COLUMN_MAPPINGS
from app.agents.exceptions import CSVParsingError, JobFetcherError
from app.agents.schemas import JobData, JobFetcherInput, JobSourceType
from app.agents.utils import extract_skills_from_text, find_csv_column, parse_csv_content


class JobFetcherAgent(BaseAgent[JobFetcherInput, list[JobData]]):
    #Fetches and normalises job listings from configurable sources

    def __init__(self) -> None:
        super().__init__("JobFetcherAgent", version="1.0.0")

    # Validation hook
    async def validate_and_parse_input(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, JobFetcherInput):
            return input_data.model_dump()
        return input_data

    
    #main execution logic 
    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        source = input_data.get("source")
        _fetchers = {
            JobSourceType.CSV: self._fetch_from_csv,
            JobSourceType.GOOGLE_SHEETS: self._fetch_from_google_sheets,
            JobSourceType.LINKEDIN: self._fetch_from_linkedin,
        }

        fetcher = _fetchers.get(source)
        if fetcher is None:
            raise JobFetcherError(f"Unsupported source: {source!r}", agent_name=self.name)

        jobs = await fetcher(input_data)

        return self.create_success_result(
            data={
                "jobs": [j.model_dump() if isinstance(j, JobData) else j for j in jobs],
                "count": len(jobs),
                "source": source,
            }
        )

    # ------------------------------------------------------------------
    # Source-specific fetchers
    # ------------------------------------------------------------------

    async def _fetch_from_csv(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse CSV text and yield normalised job dicts."""
        csv_content = input_data.get("csv_content")
        if not csv_content:
            raise CSVParsingError("'csv_content' is required for CSV source")

        df = parse_csv_content(csv_content)

        jobs: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            try:
                job = self._row_to_job(df, row)
                jobs.append(job)
            except (KeyError, ValueError, TypeError) as exc:
                self.logger.warning(f"Skipping malformed row: {exc}")
            except Exception as exc:
                self.logger.exception(f"Unexpected error parsing row: {exc}")

        self.logger.info(f"Parsed {len(jobs)} jobs from CSV")
        return jobs

    async def _fetch_from_google_sheets(
        self, input_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Fetch jobs from a public Google Sheets document.

        TODO: Implement via Sheets export URL or the Sheets API.
        """
        url = input_data.get("url", "")
        self.logger.warning(f"Google Sheets integration not yet implemented (url={url!r})")
        raise NotImplementedError("Google Sheets integration not yet implemented. TODO: Implement via Sheets export URL or the Sheets API.")

    async def _fetch_from_linkedin(
        self, input_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Scrape job listings from LinkedIn search results.

        TODO: Implement via Playwright or a dedicated scraping library.
        """
        url = input_data.get("url", "")
        self.logger.warning(f"LinkedIn scraping not yet implemented (url={url!r})")
        raise NotImplementedError("LinkedIn scraping not yet implemented. TODO: Implement via Playwright or a dedicated scraping library.")

    #private helpers

    def _row_to_job(self, df: pd.DataFrame, row: pd.Series) -> dict[str, Any]:
        """Map a single DataFrame row to a normalised job dict.

        Raises:
            KeyError / ValueError: Propagated to the caller, which logs and
                skips the offending row.
        """
        job: dict[str, Any] = {}

        for field, _variants in CSV_COLUMN_MAPPINGS.items():
            col_name = find_csv_column(df, field)
            if col_name is not None:
                value = row[col_name]
                if pd.notna(value):
                    job[field] = str(value).strip()

        description = job.get("description", "")
        if description:
            job["required_skills"] = extract_skills_from_text(description)

        job["source"] = "csv"
        return job