# MySQL Database Setup Guide

This guide explains how to set up MySQL database for the Content Management API.

## Prerequisites

- MySQL Server installed (or XAMPP/WAMP with phpMyAdmin)
- Python 3.11+ installed
- All Python dependencies installed (`pip install -r requirements.txt`)

## Option 1: Using Local MySQL/phpMyAdmin (Recommended for Development)

### Step 1: Create Database in phpMyAdmin

1. Open phpMyAdmin (usually at `http://localhost/phpmyadmin`)
2. Click on "New" to create a new database
3. Database name: `emo_energy`
4. Collation: `utf8mb4_unicode_ci`
5. Click "Create"

### Step 2: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file and update the database connection:
   ```env
   DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/emo_energy
   ```
   
   Replace `your_mysql_password` with your MySQL root password.
   If MySQL root has no password, use:
   ```env
   DATABASE_URL=mysql+pymysql://root@localhost:3306/emo_energy
   ```

### Step 3: Update Other Environment Variables

Edit `.env` and set:
- `SECRET_KEY`: A random string (minimum 32 characters)
- `HUGGINGFACE_API_KEY`: Your HuggingFace API key
- `OPENAI_API_KEY`: (Optional) Your OpenAI API key

### Step 4: Run the Application

The database tables will be created automatically on first run:

```bash
uvicorn app.main:app --reload
```

## Option 2: Using Docker Compose

### Step 1: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and update MySQL credentials:
   ```env
   MYSQL_ROOT_PASSWORD=your_secure_password
   MYSQL_DATABASE=emo_energy
   MYSQL_USER=app_user
   MYSQL_PASSWORD=app_password
   ```

### Step 2: Start Services

```bash
docker-compose up -d
```

This will:
- Start MySQL container
- Create the database automatically
- Start the FastAPI application
- Create tables automatically

### Step 3: Access phpMyAdmin (Optional)

To access phpMyAdmin for database management, add this to `docker-compose.yml`:

```yaml
phpmyadmin:
  image: phpmyadmin/phpmyadmin
  container_name: emo_energy_phpmyadmin
  environment:
    PMA_HOST: db
    PMA_PORT: 3306
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
  ports:
    - "8080:80"
  depends_on:
    - db
```

Then access phpMyAdmin at `http://localhost:8080`

## Database Schema

The application will automatically create these tables:

- **users**: User accounts
  - id (Primary Key)
  - username (Unique)
  - email (Unique)
  - hashed_password
  - created_at

- **contents**: User content with analysis
  - id (Primary Key)
  - user_id (Foreign Key to users)
  - text
  - summary
  - sentiment
  - created_at
  - updated_at

## Troubleshooting

### Connection Error: "Access denied for user"

- Check MySQL username and password in `.env`
- Ensure MySQL user has proper permissions
- For local MySQL, try using `root` user

### Connection Error: "Can't connect to MySQL server"

- Ensure MySQL server is running
- Check if MySQL is listening on port 3306
- Verify host and port in `DATABASE_URL`

### Import Error: "No module named 'pymysql'"

Install the MySQL driver:
```bash
pip install pymysql cryptography
```

### Tables Not Created

- Check application logs for errors
- Ensure database exists
- Verify user has CREATE TABLE permissions
- Try manually creating tables using Alembic migrations

## Migration from SQLite to MySQL

If you have existing data in SQLite (`Emo_Energy.db`):

1. Export data from SQLite:
   ```bash
   sqlite3 Emo_Energy.db .dump > backup.sql
   ```

2. Create MySQL database (as shown above)

3. Import data (may require manual conversion):
   - Use a tool like `mysqldump` or manual SQL conversion
   - Or use a migration tool like `sqlalchemy-migrate`

## Production Considerations

- Use strong passwords for MySQL root and application user
- Create a dedicated database user with limited permissions
- Enable SSL/TLS for database connections
- Set up database backups
- Use connection pooling (already configured in `database.py`)
- Consider using environment-specific `.env` files

