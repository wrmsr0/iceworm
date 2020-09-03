"""
TODO:
 -
"""
import dataclasses as dc
import os.path

from omnibus import lang
import pytest
import sqlalchemy as sa

from .. import state as st
from ...tests.helpers import clean_pg
from ...tests.helpers import pg_url  # noqa


@dc.dataclass(frozen=True)
class WorldState:
    id: int
    a: str
    b: str


def test_state():
    store = st.HeapObjStore([
        st.ObjMapper(WorldState, ['id']),
    ])
    wos = [
        WorldState(0, 'aa', 'bb'),
        WorldState(1, 'cc', 'dd'),
    ]
    store.put(wos[0])
    store.put(wos[1])
    assert store.get(WorldState, store.key(wos[0])) == wos[0]


@pytest.mark.xfail()
def test_state_script(pg_url):  # noqa
    with open(os.path.join(os.path.dirname(__file__), 'state.sql'), 'r') as f:
        buf = f.read()

    engine: sa.engine.Engine
    with lang.disposing(sa.create_engine(pg_url)) as engine:
        clean_pg(engine)
        with engine.connect() as conn:
            conn.execute(buf)
