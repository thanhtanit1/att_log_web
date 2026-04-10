# att_log

## Run

```bash
pip install -r requirements.txt
copy .env.example .env
python run.py
```

## Structure

- app/: Flask package
- app/routes/: Blueprint routes
- app/services/: Database and business logic
- app/templates/: HTML templates
- app/static/: CSS and JS
- instance/: Local runtime config
- tests/: Test files
