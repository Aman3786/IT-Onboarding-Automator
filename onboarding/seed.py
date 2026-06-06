from sqlalchemy import select

from database import get_session, init_db
from models import App, RoleAppGrant

APPS = [
    "slack",
    "google_workspace",
    "jira",
    "salesforce",
]

ROLE_APP_MAPPINGS: dict[str, list[str]] = {
    "engineer": ["slack", "google_workspace", "jira"],
    "sales": ["slack", "google_workspace", "salesforce"],
    "it_admin": ["slack", "google_workspace", "jira", "salesforce"],
}


def seed_database() -> None:
    init_db()
    session = get_session()
    try:
        apps_by_name: dict[str, App] = {}
        for name in APPS:
            app = session.scalar(select(App).where(App.name == name))
            if app is None:
                app = App(name=name)
                session.add(app)
                session.flush()
            apps_by_name[name] = app

        for role, app_names in ROLE_APP_MAPPINGS.items():
            for app_name in app_names:
                app = apps_by_name[app_name]
                existing = session.scalar(
                    select(RoleAppGrant).where(
                        RoleAppGrant.role == role,
                        RoleAppGrant.app_id == app.id,
                    )
                )
                if existing is None:
                    session.add(RoleAppGrant(role=role, app_id=app.id))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
