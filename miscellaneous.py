#!/usr/bin/env python3


def arguments(*args_t, **kwargs_t):
    args_t = [((lambda x: x) if t is None else t) for t in args_t]
    kwargs_t = {k: ((lambda x: x) if t is None else t) for k, t in kwargs_t.items()}
    def argument_filter(function):
        def wrapper(*args, **kwargs):
            nonlocal function, args_t, kwargs_t
            return function(
                *[t(v) for v, t in zip(args, args_t)],
                **{k: kwargs_t[k](v) for k, v in kwargs.items()}
            )
        return wrapper
    return argument_filter


def debug(*args, **kwargs):
    import datetime, sys
    print (datetime.datetime.strftime(datetime.datetime.now(), "[debug %Y-%m-%d %H:%M:%S.%f ?TZ]"), *args, file=sys.stderr, **kwargs)


