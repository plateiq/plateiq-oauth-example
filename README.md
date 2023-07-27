Install Poetry (https://python-poetry.org/docs/#installation)
Set environment variables `PLATEIQ_AUTH_CLIENT_ID` and `PLATEIQ_AUTH_CLIENT_SECRET`

```
poetry install
poetry run flask --app plateiq_oauth_example.main:app run
```

Then navigate to http://localhost:5000