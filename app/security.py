"""Flask-Security setup with a minimal Role model."""
import uuid

from sqlalchemy import Column, String
from flask_security import SQLAlchemyUserDatastore, RoleMixin

from app.extensions import db, security
from app.models import GUID, User


class Role(db.Model):
    __tablename__ = "role"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(80), unique=True)
    description = Column(String(255))

    def __repr__(self):
        return f"<Role {self.name}>"

    # RoleMixin compatibility
    def __eq__(self, other):
        return self.name == other or self.name == getattr(other, "name", None)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)


# Many-to-many: users <-> roles
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", GUID(), db.ForeignKey("user.id")),
    db.Column("role_id", GUID(), db.ForeignKey("role.id")),
)

# Patch User to add roles relationship (needed by Flask-Security)
if not hasattr(User, "roles"):
    User.roles = db.relationship(
        "Role",
        secondary=roles_users,
        backref=db.backref("users", lazy="dynamic"),
    )


def setup_security(app):
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)
    return user_datastore
