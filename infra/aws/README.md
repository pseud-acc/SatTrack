# SatTrack hosting: AWS + GitHub setup (DRAFT, nothing applied yet)

The pipeline runs daily in GitHub Actions (public repo) and keeps all data in one private S3 bucket in
**eu-west-1 (Ireland)**, next to the Heroku EU app. An AWS EventBridge schedule is the **only** trigger: it
calls GitHub's `workflow_dispatch` API once a day at 03:17 UTC. GitHub reaches AWS only through OIDC; no AWS
keys exist in GitHub. **One public repo** holds the app, the pipeline and this infra: `pseud-acc/SatTrack`
(the existing Heroku app repo; app at the root, pipeline in `pipeline/`, infra in `infra/`; decided 2026-11-10).
The `production` environment has **no required reviewer** (decided 2026-11-08): the run is
unattended and the environment's "main only" deployment branch rule is the gate. Full design, threat model and
reasoning: `hosting_security_plan.html` (the design page).

| File | What it creates |
|---|---|
| `sattrack-core.yaml` | GitHub OIDC provider, pipeline role + least-privilege policy, private bucket (Block Public Access, ACLs off, SSE-S3, versioning, lifecycle, deny-everyone-else policy), Heroku app reader IAM user (no key), monthly budget |
| `sattrack-scheduler.yaml` | Daily EventBridge rule + API destination that calls GitHub `workflow_dispatch` (the only trigger), SNS topic and two CloudWatch alarms that email you if the dispatch fails or stops |
| `../state/sattrack_state.py` | Pull/commit of run state with a conditional-write manifest (used by the workflow; `seed` for the cutover) |
| `../../.github/workflows/pipeline.yml` | The daily job |

Apply order: core stack (step 3) -> seed and first manual run (steps 4-6) -> app key (step 7) -> scheduler stack
(step 8). The scheduler goes last so nothing triggers a run before the state is seeded.

Run every command below yourself, from the root of `pseud-acc/SatTrack`, signed in as your **admin** identity
(not the pipeline role): the IAM Identity Center profile, e.g. `aws sso login --profile admin` then
`export AWS_PROFILE=admin`. Replace the `<...>` placeholders. Nothing here prints secret values.

## 0. Before you start

1. **Rotate the Space-Track password** (it leaked into a log on 2026-10-11). Put the new value **only**
   into the Secrets Manager secret, never into the laptop's `.env.sh`.
2. Make the secret a JSON object with exactly these keys (what `credentials.py` reads):
   `{"username": "...", "password": "..."}`. Console: Secrets Manager → the secret → *Retrieve secret value* → *Edit*.
3. Note the secret's **full ARN** (ends in `-` plus 6 random characters) and its **region**.
4. AWS account hygiene: MFA on the root user and no root access keys; IAM Identity Center (eu-west-1) with
   group `Admins` and permission set `AdministratorAccess` for daily work, used through `aws configure sso`;
   confirm the account is on the **paid plan** (an account opened Dec 2025 has left the 6-month free plan;
   leftover credits still apply until they expire).
5. Region: everything new goes in **eu-west-1** (the Heroku app runs in Heroku's EU region, so S3 -> app
   traffic stays in-region). The Space-Track secret may stay in another region: the pipeline reads the region
   from the secret ARN. Use `--region eu-west-1` (or `AWS_REGION=eu-west-1`) in every command below.

## 1. Read the repo's ids (the repo already exists)

`pseud-acc/SatTrack` is the existing app repo; the pipeline was moved into it under `pipeline/` (do not create
a second repo). After the merged `main` is pushed (secret scan first, see step 5):

```bash
gh api repos/pseud-acc/SatTrack --jq '.id, .owner.id'              # repo id, owner id
gh api repos/pseud-acc/SatTrack/actions/oidc/customization/sub     # subject-claim settings
```

Repos created after 2026-07-15 send `sub = repo:OWNER@OWNER_ID/REPO@REPO_ID:environment:production`
(GitHub OIDC reference). This repo is older, so it likely still sends the legacy
`repo:OWNER/REPO:environment:production`: set `UseImmutableSubject` to match what the second command reports
(`false` for the legacy form). A history reset (orphan commit + force push) keeps the repo id; deleting and
re-creating the repo does not, so then update `GitHubRepoId`.

## 2. Account-level S3 Block Public Access

```bash
aws s3control put-public-access-block --account-id <account-id> \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws accessanalyzer create-analyzer --analyzer-name account-external-access --type ACCOUNT   # free; flags any public/cross-account grant
```

## 3. Deploy the core stack

```bash
aws cloudformation validate-template --template-body file://infra/aws/sattrack-core.yaml
pip install cfn-lint && cfn-lint infra/aws/sattrack-core.yaml          # optional but recommended
aws cloudformation deploy --region <region> --stack-name sattrack-core \
  --template-file infra/aws/sattrack-core.yaml --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    BucketName=<private-bucket-name> \
    GitHubOwner=pseud-acc GitHubOwnerId=<owner-id> GitHubRepo=SatTrack GitHubRepoId=<repo-id> \
    SpaceTrackSecretArn=<full-secret-arn> \
    AdminPrincipalArn='arn:aws:iam::<account-id>:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_AdministratorAccess_*' \
    BudgetEmail=<you@example.com>        # RollbackDays defaults to 30
aws cloudformation describe-stacks --stack-name sattrack-core --query 'Stacks[0].Outputs'
```

If the account already has a `token.actions.githubusercontent.com` provider, add
`CreateOidcProvider=false ExistingOidcProviderArn=<arn>`.

## 4. Seed the state from the laptop (one-time cutover)

Stop the laptop's scheduled runs **first** (Task Scheduler → disable the SatTrack task), let any run in
progress finish, then upload its last good DuckDB files as the starting state. This carries over the
Space-Track login-backoff counter and the freshness timestamps.

```bash
aws sso login --profile admin
export AWS_PROFILE=admin SATTRACK_BUCKET=<private-bucket-name> SATTRACK_DATA_DIR=<laptop data dir> AWS_REGION=eu-west-1
python infra/state/sattrack_state.py seed     # uses your SSO admin session; refuses if state already exists
```

## 5. GitHub repository settings (before the first push of the workflow)

Pre-publish checks:
- Run a secret scanner over the full history and the working tree of the merged repo (`gitleaks git .`,
  `gitleaks dir .`). The repo root is `Space_Junk/SatTrack/`, so the key files under `SatTrack_dev/` are outside it.
- `.gitignore` excludes `pipeline/data/*`, `*.duckdb`, `.env.sh`.
- `.slugignore` keeps `pipeline/`, `infra/` and docs out of the Heroku build.
- The app's `sync-requirements.yml` must pass the Actions settings below: actions pinned to SHAs, no
  `ad-m/github-push-action` (plain `git push` instead), `permissions: contents: write`, push to `main` only.

Settings:
- **Security**: secret scanning + push protection on (free for public repos); Dependabot alerts on.
- **Actions → General**: *Allow \<owner\>, and select non-\<owner\>, actions* with the allow-list
  `actions/checkout@*, actions/setup-python@*, aws-actions/configure-aws-credentials@*,
  actions/upload-pages-artifact@*, actions/deploy-pages@*` (the last two for `docs.yml`); tick
  *Require actions to be pinned to a full-length commit SHA*; *Workflow permissions* = read repository
  contents; untick *Allow GitHub Actions to create and approve pull requests*; *Fork pull request workflows*
  = require approval for all external contributors.
- **Environments → New `production`**: *Deployment branches and tags* = *Selected branches*, rule `main`.
  **No required reviewer** (the run is unattended; the main-only branch rule is the gate). Environment secrets:
  `AWS_PIPELINE_ROLE_ARN` (stack output), `SATTRACK_BUCKET`, `SATTRACK_SPACETRACK_SECRET_ID` (secret ARN).
  These are identifiers, not credentials; they are secrets only so they are masked in public logs.
- **Variables**: repository variable `AWS_REGION` = `eu-west-1`.
- **Rules → Rulesets** on `main`: block force pushes and deletion; require a pull request with code-owner
  review once anyone else has write access (as sole maintainer you can add yourself as a bypass actor; the
  planned history reset needs one force push, so do it as the bypass actor or before enabling the ruleset).
- `.github/CODEOWNERS` and the `if:` guards in both workflows are set to `pseud-acc/SatTrack` with
  `pipeline/` paths.

## 6. First run

Actions → *sattrack-pipeline* → *Run workflow* on `main` with `force` ticked. Expect: pull downloads two
verified files, the pipeline step prints only its exit code, push commits the manifest and writes
`app/satcat_tle.csv`, `app/last_data_update.csv`, `app/manifest.json` and, last, `app/current.json`.

## 7. Heroku app reader key (phase 1)

The app release that reads S3 must be deployed together with the pipeline's `export_app_csvs.py` change
(drop `StatusCode`/`UcsData`/`OrbitClassEstimated`, rename the freshness row to `SpaceTrack_GP`); see the design
page. The patch is `agents/hosting2/app_s3_read.patch` (not applied). It falls back to the raw GitHub URLs while
`SATTRACK_S3_BUCKET` is unset, so deploying it first is safe.

Create the key in the console (IAM → Users → sattrack-app-reader → *Create access key* →
*Application running outside AWS*), not with the CLI, so it is never echoed into a terminal or shell
history file, and paste the pair straight into Heroku → app → Settings → *Config Vars*. The equivalent variables
(set `SATTRACK_S3_BUCKET` last: it is the switch from GitHub URLs to S3):

```bash
heroku config:set -a sattrackapp AWS_ACCESS_KEY_ID=<id> AWS_SECRET_ACCESS_KEY=<secret> AWS_DEFAULT_REGION=eu-west-1
heroku config:set -a sattrackapp SATTRACK_S3_BUCKET=<bucket>       # SATTRACK_S3_PREFIX defaults to app/
```
Rotate every 90 days: create the second key, update Heroku, confirm the app loads, deactivate then delete the old key.

## 8. Scheduler (EventBridge → workflow_dispatch, the only trigger)

1. GitHub → Settings → Developer settings → **Fine-grained token**: repository access = only this repo;
   permission **Actions: Read and write** (nothing else); expiry 1 year; calendar reminder to renew it.
2. AWS console (eu-west-1) → EventBridge → API destinations → **Connections → Create**: authorization type *API key*,
   key name `Authorization`, value `Bearer <token>`. (The token is stored in an EventBridge-managed secret;
   its storage cost is included in API destination pricing.)
3. Deploy, then confirm the SNS subscription email:
```bash
aws cloudformation deploy --region eu-west-1 --stack-name sattrack-scheduler   --template-file infra/aws/sattrack-scheduler.yaml --capabilities CAPABILITY_NAMED_IAM   --parameter-overrides ConnectionArn=<connection-arn> GitHubOwner=pseud-acc GitHubRepo=SatTrack AlarmEmail=<you@example.com>
```
Expect one "no successful dispatch" alarm email right after deploying, until the first 03:17 dispatch succeeds.
Renewing the token yearly: edit the connection's API key value in the console; no redeploy.
The workflow's 12-hour freshness gate stays: the concurrency group queues a second dispatch (manual, or a retry
after a lost response) rather than dropping it, and that second run would hit Space-Track GP again within the hour.

## 9. Retire the laptop as a runner

Delete the Task Scheduler entry; remove `SPACETRACK_USER`/`SPACETRACK_PASS` from the laptop's `.env.sh`
(the rotated password never lived there). Stop the old laptop job (`run_pipeline.sh`, which commits `dat/*.csv`)
and, once the app reads S3, delete the old pipeline from the repo in one commit: `src/`, `dat/` and the root
`run_pipeline.py`. After that the history can be reset (orphan commit, force push to `origin` and `heroku`). Local development uses a downloaded copy of the state and no
Space-Track login.

## Verification checklist

- [ ] `aws s3api get-public-access-block --bucket <bucket>` → all four `true`; same at account level (`aws s3control get-public-access-block`).
- [ ] `aws s3api get-bucket-policy-status --bucket <bucket>` → `IsPublic: false`.
- [ ] `aws s3api get-bucket-ownership-controls --bucket <bucket>` → `BucketOwnerEnforced`.
- [ ] `aws s3api get-bucket-versioning --bucket <bucket>` → `Enabled`; `get-bucket-lifecycle-configuration` shows the 8 rules (rollback window 30 days).
- [ ] IAM Access Analyzer: no active findings for the bucket or the role.
- [ ] `curl -sI http://<bucket>.s3.<region>.amazonaws.com/state/manifest.json` → 403 (no anonymous or non-TLS access).
- [ ] A manifest PUT without `If-Match`/`If-None-Match` from the admin → `AccessDenied` (enforced CAS).
- [ ] With the app reader key: `aws s3api get-object --bucket <bucket> --key app/current.json /tmp/x.json` works, and so does fetching a CSV with the `--version-id` named in it;
      `--key warehouse/sattrack.duckdb` → `AccessDenied`; `aws s3 ls s3://<bucket>` → `AccessDenied`.
- [ ] Dispatch the workflow on a non-`main` branch → the job is refused by the environment's branch rule (it never reaches AWS).
- [ ] CloudTrail → Event history: `AssumeRoleWithWebIdentity` events show the expected `sub` (stack output `ExpectedOidcSubject`) and no others; `GetSecretValue` only from `sattrack-run-*` sessions.
- [ ] The public Actions log of a run contains no row counts, object names, error text from the pipeline, or data; only exit codes and `[state]` lines.
- [ ] Repo has no workflow artifacts; Actions caches list is empty.
- [ ] Budget email received as "subscription confirmed" (if set).
- [ ] Next day: one run started by the EventBridge dispatch (`trigger = eventbridge` in the manifest's `last_run`).
- [ ] CloudWatch → Metrics → Events → By rule name: `FailedInvocations` and `SuccessfulInvocationAttempts` exist for `sattrack-daily-dispatch` (the alarm names rely on them). Test the alarm path once by temporarily breaking the connection token.
