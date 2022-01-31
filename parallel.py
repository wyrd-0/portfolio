"""
sqlalchemy proof-of-concept.

Proves that sessions actions in parallel threads can work on the same file,
so long as the session is closed within the thread that created it
"""

from threading import Thread, current_thread

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session, sessionmaker

DummyBase = declarative_base()


class Dummy(DummyBase):
    from sqlalchemy import Column, Integer, String
    __tablename__ = "Dummy"

    DummyId = Column(Integer, primary_key=True)
    DummyName = Column(String)


def add_dummy():
    e_local_engine = create_engine("sqlite:///Dummy.db")
    DummyBase.metadata.bind = e_local_engine
    e_SessionMaker = sessionmaker(bind=e_local_engine)
    d_session: Session = e_SessionMaker()

    for i in range(10):
        dummy = Dummy(DummyName="DumDum " + current_thread().name[0])

        d_session.add(dummy)
        d_session.commit()
        # print(current_thread().name, i, dummy.DummyId)
    d_session.close()


def parallel_session_test():
    e_local_engine = create_engine("sqlite:///Dummy.db")
    DummyBase.metadata.bind = e_local_engine
    e_SessionMaker = sessionmaker(bind=e_local_engine)
    session: Session = e_SessionMaker()

    DummyBase.metadata.drop_all()
    DummyBase.metadata.create_all()

    thread_a = Thread(name="A:", target=add_dummy)
    thread_b = Thread(name="B:", target=add_dummy)

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    q = session.query(Dummy.DummyId, Dummy.DummyName).all()
    for d in q:
        print(d)


if __name__ == "__main__":
    parallel_session_test()
