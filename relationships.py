"""
sqlalchemy proof-of-concept.

Demonstrates using a one-to-many relationship to collect class instances for simpler
 adds/updates
 
 """

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, Session, sessionmaker, relationship

VoidBase = declarative_base()


class Dummy(VoidBase):
    from sqlalchemy import Column, Integer, String
    __tablename__ = "Dummy"

    DummyId = Column(Integer, primary_key=True)
    DummyName = Column(String)

    VoidId = Column(Integer, ForeignKey("Void.VoidId"), primary_key=True)


class Void(VoidBase):
    from sqlalchemy import Column, Integer, String
    __tablename__ = "Void"

    VoidId = Column(Integer, primary_key=True)
    VoidName = Column(String)

    Dummies = relationship("Dummy", cascade="all, delete, delete-orphan, merge, save-update")


def relationship_test():
    e_local_engine = create_engine("sqlite:///Void.db")
    VoidBase.metadata.bind = e_local_engine

    VoidBase.metadata.drop_all()
    VoidBase.metadata.create_all()

    e_SessionMaker = sessionmaker(bind=e_local_engine)
    session: Session = e_SessionMaker()

    dum0 = Dummy(DummyName="dum1", DummyId=0)
    dum1 = Dummy(DummyName="dum2", DummyId=1)
    dum2 = Dummy(DummyName="dum3", DummyId=2)
    dum3 = Dummy(DummyName="dum4", DummyId=0)
    dum4 = Dummy(DummyName="dum5", DummyId=1)
    dum5 = Dummy(DummyName="dum6", DummyId=2)

    void = Void(VoidName="void1", Dummies=[dum0, dum1, dum2])
    void2 = Void(VoidName="void2", Dummies=[dum3, dum4, dum5])

    session.add(void)
    session.add(void2)

    q = session.query(Void).all()
    print("original:")
    for v in q:
        print(v.VoidId, v.VoidName)
        for d in v.Dummies:
            print(" ", d.DummyId, d.DummyName,)

    void2.Dummies = []
    session.merge(void2)
    q = session.query(Void).all()
    print("\nafter merge:")
    for v in q:
        print(v.VoidId, v.VoidName)
        for d in v.Dummies:
            print(" ", d.DummyId, d.DummyName,)

    session.rollback()


if __name__ == "__main__":
    relationship_test()
