from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, MetaData, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Naming conventions for constrant names. Defining these conventions makes the database
# more portable. See: https://alembic.sqlalchemy.org/en/latest/naming.html
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))


# FIXME: Disable typechecking on the model class inheritance until stubs are created for
# Flask-SqlAlchemy
# https://github.com/dropbox/sqlalchemy-stubs/issues/76


class Analysis(db.Model):  # type: ignore
    """A model run"""

    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[datetime]
    domain: Mapped[str] = mapped_column(String(24))
    frequency: Mapped[str] = mapped_column(String(24))
    system: Mapped[str] = mapped_column(String(24))

    model_id: Mapped[int] = mapped_column(ForeignKey("weather_model.id"))
    model: Mapped["WeatherModel"] = relationship(back_populates="analysis_list")

    def __str__(self) -> str:
        return (
            f"{self.time} {self.model} {self.frequency} "
            f"over {self.domain} on {self.system}"
        )

    def __repr__(self) -> str:
        return (
            f"Analysis(id={self.id}, time={self.time}, "
            f"domain={self.domain}, model={self.model}, "
            f"system={self.system})"
        )


class WeatherModel(db.Model):  # type: ignore
    __table_args__ = (UniqueConstraint("name", "background_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(24))

    background_id = mapped_column(ForeignKey("weather_model.id"))
    background = relationship("WeatherModel", remote_side=[id])

    analysis_list: Mapped[list[Analysis]] = relationship(back_populates="model")

    def __str__(self) -> str:
        return f"{self.name} ({self.background.name})" if self.background else self.name

    def __repr__(self) -> str:
        return (
            f"WeatherModel(id={self.id}, name='{self.name}', "
            f"background_id={self.background_id})"
        )
