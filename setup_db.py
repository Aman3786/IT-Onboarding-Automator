from onboarding.database import init_db
from onboarding.seed import seed_database


def main():
    print("Initializing database...")

    init_db()

    result = seed_database()

    print("Database initialized successfully")


if __name__ == "__main__":
    main()