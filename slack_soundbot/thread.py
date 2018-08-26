import asyncio
import concurrent.futures
import threading

# from concurrent.futures.thread library
class WorkItem():
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None
        else:
            self.future.set_result(result)

@asyncio.coroutine
def async_run_in_daemon_thread(runnable, *args, **kwargs):
    fut = concurrent.futures.Future()
    work = WorkItem(fut,runnable,args,kwargs)
    threading.Thread(target=work.run,daemon=True).start()
    result = yield from asyncio.wrap_future(fut)
    return result