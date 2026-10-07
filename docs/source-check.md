# Source check: how it runs and how to keep it running

As of 7 October 2026. This note describes the monthly check that tells
when a source behind `nitrogen.html` has changed: what it does, where it
runs, what was shown to work and what was not, and what to do when
something happens. It contains no secrets.

## What it is

`scripts/nitrogen/check_sources.py` asks each source a small question (a
date, a count, a short list), turns the answer into a fingerprint and
compares it with the fingerprint saved in
`data/nitrogen/source_state.json`. It downloads no data for the page and
changes nothing on the page. Refreshing the page stays a decision made by
hand.

| Source | What is compared |
|---|---|
| CBS, StatLine `80781ned` | Date of last change and period of the table |
| RIVM, GDN deposition map | Size and date of the file of the year on the page; whether a file for the next year exists |
| PDOK, Natura 2000 | Number of features |
| PDOK, municipal boundaries | Number of features |
| AERIUS open data, `relevant_habitats` | Number of records and a hash of four attributes, for the country and for the map area; number of Veluwe habitat types in the map area |
| Nationaal Georegister, record of that layer | AERIUS release named in the record and the date of the record |

Two sources have no signal a script can read: the Emissieregistratie
export and the Veluwe figure in AERIUS Monitor. The state file holds the
date they were last looked at (`manual.checked_on`); after 120 days the
check reports them as due.

What it cannot see: a change in the shapes of a layer when the attributes
stay the same.

### The report

| Line starts with | Meaning | Reported |
|---|---|---|
| `same` | Fingerprint equal to the saved one | No |
| `CHANGED` | Fingerprint differs; the fields that differ are listed | Yes |
| `COULD NOT READ` | The source gave no usable answer | Yes |
| `NEW` | No saved fingerprint for this source yet | Yes |
| `by hand` | Looked at less than 120 days ago | No |
| `BY HAND, DUE` | Looked at longer ago, or never recorded | Yes |

With `--issue`, a report with at least one "Yes" line goes into a GitHub
issue titled "Stikstofmonitor: a source changed or needs a look". If such
an issue is still open, the report is added to it as a comment, so a
source that stays changed does not produce a new issue every month.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Nothing left to do: nothing to report, or the report was put in an issue |
| 1 | Something to report and no issue asked for (does not occur in the scheduled job) |
| 2 | The saved state could not be read |
| 3 | Something to report, but the issue could not be opened |

## Where it runs

An Azure Container Apps job, next to the RAG demo. The settings below
were read from the job's own summary on 7 October 2026.

| Setting | Value |
|---|---|
| Job | `source-check` |
| Resource group, environment | `rg-rag-demo`, `env-rag-demo` (region `swedencentral`) |
| Image | `ragdemohakan71.azurecr.io/source-check:v1`, built from `docker/source-check/Dockerfile` |
| Trigger | Schedule, `0 6 1 * *`: the 1st of every month at 06:00 UTC (07:00 in the Netherlands in winter, 08:00 in summer) |
| Limits | Timeout 900 seconds, no retry, 0.25 CPU and 0.5 Gi memory |
| Pulling the image | The job's own system-assigned identity, with the role `AcrPull` on the registry |
| Secret | `github-token`, passed to the container as `GITHUB_TOKEN` |
| Other variable | `GITHUB_REPOSITORY=Elcebir71/nijkerk-transition-monitor` |
| Arguments | The image's default: `--issue --state <raw GitHub URL of source_state.json on main>` |

The job reads the saved state from GitHub at every run, so a new state
needs a commit on `main`, not a new image. The image holds only
`config.py` and `check_sources.py`.

The GitHub token is a fine-grained token named
`stikstofmonitor-source-check`, limited to this repository, with read and
write access to Issues and nothing else. It was made on 7 October 2026
for 90 days.

The job was made in steps: the job with a placeholder image and a
system-assigned identity, then the `AcrPull` role for that identity, then
the registry setting and the real image, then the secret and the two
variables. The exact commands were not kept. The current configuration
can be printed with:

```powershell
az containerapp job show --name source-check --resource-group rg-rag-demo --output yaml
```

## What was shown to work, and what was not

Shown on 7 October 2026:

- The script against the real sources, from the author's computer: first
  run all `NEW`, state written, second run all `same`.
- The image, run with Docker on the author's computer: six `same`.
- Opening an issue and adding to an open one, from the author's computer
  with a real token (test issue #13, closed afterwards).
- One run in Azure, started by hand: execution `source-check-pe9t4fc`,
  started 12:09 UTC, status `Succeeded`, six `same` and two `by hand`.
  This shows that the job can pull the image, reach the six sources and
  read the state from GitHub.

Not shown:

- **A run started by the schedule.** The first one is due on 1 November
  2026.
- **The token as stored in Azure.** The run in Azure had nothing to
  report, so it never used the token. Whether the stored value is right
  will only show at the first report, unless it is tested before.
- **A real `CHANGED`.** It cannot be produced on purpose; the logic is
  covered by the tests in `scripts/nitrogen/tests/` with made-up answers.

## Limits

- **A failed run tells nobody.** If a run ends with another code than 0,
  Azure marks the execution `Failed`, and that is visible only to someone
  who looks at the list of executions. No alert has been set up. An
  expired token is the likely case: the report then exists only in the
  log of that run.
- **No report is not proof that the check ran.** A month without an issue
  means "nothing changed" only if the execution of that month is in the
  list with status `Succeeded`.
- **Things that end by themselves.** The Azure subscription is a trial
  that ends around 31 October 2026; without an upgrade the job stops
  before its first scheduled run. The token ends around 5 January 2027
  (the exact date is on the token's page in GitHub).
- **The first report that is certain to come** is the reminder for the
  two sources checked by hand: they were looked at on 5 and 6 October
  2026, so the run of 1 March 2027 is the first that finds them older
  than 120 days. That is after the token ends, so the token has to be
  renewed before then.
- **Costs** have not been worked out here. The registry is shared with
  the RAG demo.

## What to do

All commands are for PowerShell, from the repo root where a path is used.

### See whether it ran

```powershell
az containerapp job execution list --name source-check --resource-group rg-rag-demo --output table --query "[].{Status: properties.status, Name: name, StartTime: properties.startTime}"
```

The log of the latest run:

```powershell
az containerapp job logs show --name source-check --resource-group rg-rag-demo --container source-check
```

### Run it now

```powershell
az containerapp job start --name source-check --resource-group rg-rag-demo
```

### An issue was opened

1. Read the report in the issue: which source, which fields.
2. Look at the source itself. Decide whether the page needs new data.
3. If so: refresh by hand as described in
   [`methodology.md`](methodology.md) under "Updating", compare with the
   previous figures, and publish through a pull request.
4. Save the new state, on a branch, and merge it into `main`:

   ```powershell
   python scripts/nitrogen/check_sources.py --write-state
   ```

   A source that could not be read keeps its old fingerprint.
5. For a `BY HAND, DUE` line: look at the source as the line says, then
   change the date `manual.<source>.checked_on` in
   `data/nitrogen/source_state.json` by hand.
6. Close the issue. While it stays open, later reports are added to it.

### A run failed

Read the log. The last lines say which case it is:

- "Could not read the saved state" (code 2): GitHub did not return the
  state file, or the file is not valid JSON.
- "Could not open an issue" (code 3): the line gives GitHub's own
  reason. "Bad credentials" points to a token that has ended or was
  stored wrongly; a line naming a permission points to a token without
  access to Issues.
- No log at all: the container did not start. Check the image name and
  the `AcrPull` role.

### Renew the token

1. In GitHub: Settings, Developer settings, Fine-grained tokens. Make a
   new token for this repository only, with read and write access to
   Issues. Copy it.
2. Put it in the job without typing it, so it stays out of the shell
   history:

   ```powershell
   $env:GITHUB_TOKEN = Get-Clipboard
   az containerapp job secret set --name source-check --resource-group rg-rag-demo --secrets github-token=$env:GITHUB_TOKEN
   Remove-Item Env:GITHUB_TOKEN
   ```

3. Start a run by hand and look at its status.

### The script changed

The job keeps running the old image until a new one is built and set:

```powershell
az acr login --name ragdemohakan71
docker build -f docker/source-check/Dockerfile -t ragdemohakan71.azurecr.io/source-check:v2 .
docker push ragdemohakan71.azurecr.io/source-check:v2
az containerapp job update --name source-check --resource-group rg-rag-demo --image ragdemohakan71.azurecr.io/source-check:v2
```

Use a new tag each time, so it stays clear which version runs. Then start
a run by hand.

### Change the schedule

```powershell
az containerapp job update --name source-check --resource-group rg-rag-demo --cron-expression "0 6 1 * *"
```

Five fields, in UTC: minute, hour, day of the month, month, day of the
week.

### Remove it

Only this job; the RAG demo and the registry stay:

```powershell
az containerapp job delete --name source-check --resource-group rg-rag-demo
```

Deleting the resource group `rg-rag-demo` removes everything in it. The
image `source-check` in the registry and the token in GitHub are removed
separately.

## Running it somewhere else

The script needs only Python and the `requests` package, two environment
variables for the issue, and a place to read the state from. Nothing in
it is specific to Azure; any scheduler that can run a container or a
Python script once a month can take over.
