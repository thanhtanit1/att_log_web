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

## Render Deploy

Project nay dung `pyodbc`, vi vay tren Render ban nen deploy bang `Docker` thay vi Python native service.

Can chuan bi:

- Tao cac environment variables tren Render dua theo `.env.example`
- Dam bao SQL Server cho phep ket noi tu Internet hoac whitelist IP outbound cua Render
- Khong commit file `.env` that

Sau khi push repo len GitHub:

1. Tao `Web Service` moi tren Render
2. Chon repo GitHub cua ban
3. Render se tu nhan `Dockerfile`
4. Them cac environment variables tu `.env.example`
5. Deploy

Neu database khong cho ket noi, app van len duoc nhung trang chu se hien loi truy van database.
