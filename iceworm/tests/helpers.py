"""
TODO:
 - db setup/teardown
 - all docker compose services
"""
import threading
import typing as ta

from omnibus import check
from omnibus import code as oco
from omnibus import docker
from omnibus import lang
import pytest
import sqlalchemy as sa


T = ta.TypeVar('T')


DEFAULT_TIMEOUT_S = 30


def pytest_callable_fixture(*fxargs, **fxkwargs):
    """Fuck off pytest."""

    def inner(fn):
        fixture = pytest.fixture(*fxargs, **fxkwargs)(fn)

        def override(*args, **kwargs):
            nonlocal fn
            return 1(*args, **kwargs)  # noqa

        code = override.__code__
        check.state(code.co_consts == (None, 1))
        newcodeargs = [getattr(code, f'co_{a}') for a in oco.CODE_ARGS]
        newcodeargs[oco.CODE_ARGS.index('consts')] = (None, fn)
        fixture.__code__ = type(code)(*newcodeargs)

        return fixture

    return inner


class HostPort(ta.NamedTuple):
    host: str
    port: int


@pytest_callable_fixture()
@lang.cached_nullary
def pg_host_port() -> HostPort:
    if docker.is_in_docker():
        (host, port) = 'iceworm-postgres', 5432

    else:
        with docker.client_context() as client:
            eps = docker.get_container_tcp_endpoints(
                client,
                [('docker_iceworm-postgres_1', 5432)])

        [(host, port)] = eps.values()

    return HostPort(host, port)


@pytest_callable_fixture()
@lang.cached_nullary
def raw_pg_url() -> str:
    hp = pg_host_port()
    return f'postgresql+psycopg2://iceworm:iceworm@{hp.host}:{hp.port}'


@pytest.fixture()
def pg_url() -> str:
    url = raw_pg_url()
    with lang.disposing(sa.engine.create_engine(url)) as engine:
        clean_pg(engine)
    return url


@pytest.yield_fixture()
def pg_engine(pg_url):  # noqa
    with lang.disposing(sa.engine.create_engine(pg_url)) as engine:
        yield engine


def clean_pg(engine: sa.engine.Engine) -> None:
    with engine.connect() as conn:
        conn.execute('DROP SCHEMA IF EXISTS "iceworm" CASCADE')
        conn.execute('CREATE SCHEMA IF NOT EXISTS "iceworm"')
        conn.execute('SET search_path TO "iceworm", "public"')

        if conn.scalar('SELECT COUNT(*) FROM pg_catalog.pg_user WHERE usename = \'iceworm\'') < 1:
            conn.execute('CREATE USER "iceworm" PASSWORD \'iceworm\'')
        conn.execute('ALTER ROLE "iceworm" SET search_path TO "iceworm", "public"')

        conn.execute('ALTER SCHEMA "iceworm" OWNER TO "iceworm"')


def call_many_with_timeout(
        fns: ta.Iterable[ta.Callable[[], T]],
        timeout_s: int = None,
        timeout_exception: Exception = RuntimeError('Thread timeout'),
) -> ta.List[T]:
    if timeout_s is None:
        timeout_s = DEFAULT_TIMEOUT_S

    fns = list(fns)
    missing = object()
    rets: T = [missing] * len(fns)
    thread_exception: ta.Optional[Exception] = None

    def inner(fn, idx):
        try:
            nonlocal rets
            rets[idx] = fn()
        except Exception as e:
            nonlocal thread_exception
            thread_exception = e
            raise

    threads = [threading.Thread(target=inner, args=(fn, idx)) for idx, fn in enumerate(fns)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout_s)
    for thread in threads:
        if thread.is_alive():
            raise timeout_exception

    if thread_exception is not None:
        raise thread_exception
    for ret in rets:
        if ret is missing:
            raise ValueError

    return rets


def run_with_timeout(
        *fns: ta.Callable[[], None],
        timeout_s: int = None,
        timeout_exception: Exception = RuntimeError('Thread timeout'),
) -> None:
    call_many_with_timeout(fns, timeout_s, timeout_exception)