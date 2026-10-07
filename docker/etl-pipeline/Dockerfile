# Image for the ETL pipeline that loads the CBS livestock counts into PostgreSQL.
#
# Build from the repo root:
#   docker build -f docker/etl-pipeline/Dockerfile -t etl-pipeline .
#
# Run (the database is given in DATABASE_URL; without it the run stops with exit code 2):
#   docker run --rm -e DATABASE_URL=postgresql://user:password@host:5432/dbname etl-pipeline
#   docker run --rm etl-pipeline --dry-run        fetch and validate only, no database
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The requirements first, so a change in the code does not reinstall the packages.
COPY pipeline/requirements.txt pipeline/requirements.txt
RUN pip install -r pipeline/requirements.txt

# Only what the pipeline needs: the settings and the CBS fetch of the nitrogen module, and the pipeline itself.
COPY scripts/nitrogen/config.py scripts/nitrogen/fetch_cbs_livestock.py scripts/nitrogen/
COPY pipeline/cbs_livestock.py pipeline/

RUN useradd --create-home --uid 10001 pipeline
USER pipeline

# DATABASE_URL comes from the environment of the job, never from the image.
ENTRYPOINT ["python", "pipeline/cbs_livestock.py"]
