from sqlalchemy import create_engine, text

# Ganti connection string ini jika pakai PostgreSQL/MySQL
engine = create_engine("sqlite:///db/data.db")

def match_with_db(name, amount):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM receipts
            WHERE name LIKE :name AND amount LIKE :amount
            LIMIT 1
        """), {"name": f"%{name}%", "amount": f"%{amount}%"})

        row = result.fetchone()
        return dict(row) if row else None
