DATABASE_FILE="instance/db.sqlite3"
if [ -f "$DATABASE_FILE" ]; then
  rm $DATABASE_FILE
fi
