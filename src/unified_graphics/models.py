from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unified_graphics import db

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
