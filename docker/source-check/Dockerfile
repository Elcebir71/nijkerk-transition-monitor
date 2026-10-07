# Image for the scheduled source check of the Stikstofmonitor.
#
# Build from the repo root, so the two script files are in the build context:
#     docker build -f docker/source-check/Dockerfile -t source-check .
#
# The container asks the sources, compares with the state saved in the GitHub repo and,
# when something changed, opens a GitHub issue. It writes nothing anywhere else.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install "requests>=2.31,<3"

# The script finds the repo root two folders above itself, so the folder layout is kept.
WORKDIR /app
COPY scripts/nitrogen/config.py scripts/nitrogen/check_sources.py scripts/nitrogen/

# No reason to run as root: the script only makes web requests.
RUN useradd --create-home --uid 10001 checker
USER checker

# GITHUB_TOKEN and GITHUB_REPOSITORY come from the environment of the job, never from the image.
ENTRYPOINT ["python", "scripts/nitrogen/check_sources.py"]
CMD ["--issue", "--state", "https://raw.githubusercontent.com/Elcebir71/nijkerk-transition-monitor/main/data/nitrogen/source_state.json"]
