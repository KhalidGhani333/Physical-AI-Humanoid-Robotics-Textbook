from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


class IngestionJob(BaseModel):
    """
    Tracks the progress and status of a content ingestion job
    """
    job_id: str  # Unique identifier for the ingestion job
    source_urls: List[str]  # List of URLs to be processed
    status: str  # Current status of the job (e.g., "running", "completed", "failed")
    progress: int = 0  # Number of URLs processed so far
    total: int  # Total number of URLs to process
    start_time: datetime  # When the job was started
    end_time: Optional[datetime] = None  # When the job was completed (if finished)
    processed_chunks: int = 0  # Number of content chunks created
    error_details: Optional[str] = None  # Any error information if the job failed

    @field_validator('job_id')
    def validate_job_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('job_id must not be empty')
        return v

    @field_validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'running', 'completed', 'failed']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v

    @field_validator('progress')
    def validate_progress(cls, v, values):
        # Note: Using values.data instead of values since it's a dict in Pydantic v2
        if 'total' in values.data and v > values.data['total']:
            raise ValueError('progress must not exceed total')
        return v

    @field_validator('start_time', 'end_time')
    def validate_timestamps(cls, v, values):
        if v and 'start_time' in values.data and 'end_time' in values.data:
            start_time = values.data['start_time']
            end_time = values.data['end_time']
            if start_time and end_time and start_time > end_time:
                raise ValueError('start_time must be before end_time if job is completed')
        return v