"""
TODO:
 - test harness
 - debug as py
 - pure ops - pandas
 - omnibus.interp
 - opinionated src layout - git vs zipfile
 - static ana - not just no getattr but take both if branches
  - know expr origins of branches, can tell if const

yes:
 - loops
 - jinja (much stricter context but loops okay)
 - maybe sqla core
 - core api
 - maybe in-repo file io

no:
 - env vars - api.config('key'), returns *placeholder* like bindparam
 - db io
 - service io
 - current date/time (use sa.func.now(), rewritten in transforms)
 - 'run' date/time - no concept of that

- 'query': string literal, file: sql/py
 - when py, a module containing a function named 'query', *injected*
 - def query(now: iwa.now) -> str: …
 - setup.py entrypoint format - default 'query' or 'foo.py:q1'

https://www.microsoft.com/en-us/research/uploads/prod/2020/04/build-systems-jfp.pdf
https://www.lihaoyi.com/post/BuildToolsasPureFunctionalPrograms.html
https://www.lihaoyi.com/mill/page/mill-internals.html
https://github.com/pantsbuild/pants/blob/4f5462551a5023aced9277b4f4c7545f76bcd64d/src/python/pants/engine/query.py
https://github.com/pantsbuild/example-python
https://github.com/pantsbuild/example-plugin
https://www.pantsbuild.org/docs/target-api-concepts

https://medium.com/hashmapinc/dont-do-analytics-engineering-in-snowflake-until-you-read-this-hint-dbt-bdd527fa1795
https://github.com/fishtown-analytics/dbt
https://docs.getdbt.com/docs/building-a-dbt-project/building-models/materializations/
"""


class Macro:
    pass


class Rule:
    pass


class Target:
    pass


class Goal:
    """all, backfill, ddl, check, ..."""