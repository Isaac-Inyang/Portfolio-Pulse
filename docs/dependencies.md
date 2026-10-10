# Dependencies

PortfolioPulse uses Python dependencies for market-price ingestion and dbt dependencies for data transformation and testing.

- `requirements.txt` — Python packages required by the ingestion scripts.
- `dbt_project.yml` — dbt project configuration.
- `packages.yml` — additional dbt packages, if applicable.
- GitHub Actions workflow files — automation and environment setup.

## Install Python dependencies

```bash
pip install -r [requirements.txt](/docs/requirements.txt)
pip install dbt-core dbt-postgres
```

## Install and validate dbt

Install the dbt Core version and PostgreSQL adapter specified by the project setup, configure the local database profile, then run:

```bash
dbt deps
dbt debug
dbt build
```

Keep credentials in environment variables or GitHub repository secrets. Do not commit database passwords, API keys, or private configuration files.