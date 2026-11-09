"""Running slow side effects off the request path.

Some work is a consequence of a request rather than part of its answer. Sending
the signup verification email is the clearest case: the account exists and has
been committed, the caller is waiting on nothing but the mail, and a failure to
send must not change what the caller is told.

Keeping that work inline cost us a bug. Registration sent two Mailtrap messages
after the commit, each bounded at MAILTRAP_TIMEOUT = (10, 20), so a slow
upstream could hold the response for up to 60 seconds -- exactly the mobile
client's receive timeout. The client reported "Something went wrong" for a
registration that had in fact succeeded, and could not retry, because the email
address was by then taken.

This is deliberately the smallest thing that works: a daemon thread. It has real
limits -- the work is lost if the worker process dies, there is no retry, and
nothing records that a send was attempted. A task queue is the right answer once
there is a reason to pay for one. Until then, do not put anything here that the
customer's money depends on.
"""
import threading
import traceback


def run_detached(label, function, *args, **kwargs):
    """Run `function` in a daemon thread; never raise into the caller.

    `label` appears in the log if the work fails, so a silent background
    failure can still be traced back to what it was doing.

    The callable must not touch the Flask request or app context, and must not
    use the SQLAlchemy session: both belong to the request that is about to
    end. Pass it plain values -- render templates before handing work over.
    """
    def runner():
        try:
            function(*args, **kwargs)
        except Exception as error:
            print(f'[background] {label} failed: '
                  f'{type(error).__name__}: {error}')
            traceback.print_exc()

    thread = threading.Thread(target=runner, name=f'bg-{label}', daemon=True)
    thread.start()
    return thread
